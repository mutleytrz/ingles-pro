from __future__ import annotations
# database.py — Camada de banco de dados (SQLite local + Turso remoto)

import sqlite3
from datetime import datetime, timezone
from config import DB_PATH
from typing import Optional, Any


# ---------------------------------------------------------------------------
# DictRow — wrapper p/ acessar resultados como row["coluna"] ou row[0]
# ---------------------------------------------------------------------------
class DictRow(dict):
    """Permite acesso por nome (row['col']) e por indice (row[0])."""
    def __init__(self, columns: list[str], values: tuple | list):
        super().__init__(zip(columns, values))
        self._values = list(values)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return super().__getitem__(key)

    def keys(self):
        return super().keys()


# ---------------------------------------------------------------------------
# TursoCursor — faz o resultado do libsql-client parecer um cursor sqlite3
# ---------------------------------------------------------------------------
class TursoCursor:
    """Emula cursor sqlite3 a partir de um ResultSet do libsql-client."""
    def __init__(self, result_set):
        self._rs = result_set
        self._rows = []
        if result_set is not None and hasattr(result_set, 'rows'):
            cols = list(result_set.columns) if hasattr(result_set, 'columns') else []
            self._rows = [DictRow(cols, r) for r in result_set.rows]
        self._index = 0
        # Expor description pra compatibilidade
        self.description = None

    def fetchone(self):
        if self._index < len(self._rows):
            row = self._rows[self._index]
            self._index += 1
            return row
        return None

    def fetchall(self):
        remaining = self._rows[self._index:]
        self._index = len(self._rows)
        return remaining

    def __iter__(self):
        return iter(self._rows)


# ---------------------------------------------------------------------------
# TursoConnection — wrapper que faz libsql-client parecer sqlite3.Connection
# ---------------------------------------------------------------------------
class TursoConnection:
    """Adapta o ClientSync do libsql-client pra interface sqlite3."""
    def __init__(self, client):
        self._client = client
        self._closed = False

    def execute(self, sql: str, params=None) -> TursoCursor:
        """Executa SQL e retorna TursoCursor."""
        if params:
            rs = self._client.execute(sql, list(params))
        else:
            rs = self._client.execute(sql)
        return TursoCursor(rs)

    def executescript(self, script: str):
        """Executa multiplos statements separados por ';'."""
        statements = [s.strip() for s in script.split(';') if s.strip()]
        for stmt in statements:
            self._client.execute(stmt)

    def commit(self):
        """No-op — libsql-client auto-commits."""
        pass

    def close(self):
        """Fecha o client."""
        if not self._closed:
            try:
                self._client.close()
            except Exception:
                pass
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# ---------------------------------------------------------------------------
# Flag global: True se estamos usando Turso
# ---------------------------------------------------------------------------
_using_turso = False


def _get_conn():
    """Retorna conexao com o banco (SQLite local ou Turso remoto via HTTP)."""
    global _using_turso
    import config

    # Se tiver credenciais do Turso, conecta via libsql-client (HTTP)
    if config.TURSO_DB_URL and config.TURSO_AUTH_TOKEN:
        try:
            from libsql_client import create_client_sync
            url = config.TURSO_DB_URL
            # Normalizar URL: libsql-client precisa de https:// ao inves de libsql://
            if url.startswith("libsql://"):
                url = url.replace("libsql://", "https://", 1)
            client = create_client_sync(url, auth_token=config.TURSO_AUTH_TOKEN)
            _using_turso = True
            return TursoConnection(client)
        except ImportError:
            print("AVISO: libsql-client nao instalado. Usando SQLite local.")
        except Exception as e:
            print(f"ERRO DE CONEXAO TURSO: {e}. Usando SQLite local.")

    # Fallback SQLite Local
    _using_turso = False
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Cria as tabelas se nao existirem."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    UNIQUE NOT NULL,
            name        TEXT    NOT NULL,
            password_hash TEXT  NOT NULL,
            is_admin    BOOLEAN DEFAULT 0,
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS progress (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    UNIQUE NOT NULL,
            pagina        TEXT    DEFAULT 'inicio',
            arquivo_atual TEXT    DEFAULT 'palavras.csv',
            indice        INTEGER DEFAULT 0,
            xp            INTEGER DEFAULT 0,
            porc_atual    INTEGER DEFAULT 0,
            tentativa     INTEGER DEFAULT 0,
            updated_at    TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (username) REFERENCES users(username)
        );

        CREATE TABLE IF NOT EXISTS module_progress (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    NOT NULL,
            module_file   TEXT    NOT NULL,
            indice        INTEGER DEFAULT 0,
            updated_at    TEXT    DEFAULT (datetime('now')),
            UNIQUE(username, module_file),
            FOREIGN KEY (username) REFERENCES users(username)
        );
    """)
    conn.commit()
    conn.close()
    _check_migrations()

def _check_migrations():
    """Verifica e aplica migracoes de schema necessarias (ex: is_admin)."""
    conn = _get_conn()
    try:
        # Check if is_admin exists
        cursor = conn.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        if "is_admin" not in columns:
            print("[MIGRATION] Adicionando coluna is_admin na tabela users...")
            conn.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
            conn.commit()

        # Email auth migrations
        if "email" not in columns:
            print("[MIGRATION] Adicionando colunas de email na tabela users...")
            conn.execute("ALTER TABLE users ADD COLUMN email TEXT")
            conn.execute("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0")
            conn.execute("ALTER TABLE users ADD COLUMN verification_code TEXT")
            conn.commit()

        # Lesson scores table (best score per lesson for badges)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS lesson_scores (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT    NOT NULL,
                module_file TEXT    NOT NULL,
                lesson_idx  INTEGER NOT NULL,
                best_score  INTEGER DEFAULT 0,
                updated_at  TEXT    DEFAULT (datetime('now')),
                UNIQUE(username, module_file, lesson_idx),
                FOREIGN KEY (username) REFERENCES users(username)
            )
        """)
        conn.commit()

        # Word errors table (adaptive learning — tracks per-word error counts)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS word_errors (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT    NOT NULL,
                word        TEXT    NOT NULL,
                error_count INTEGER DEFAULT 0,
                total_seen  INTEGER DEFAULT 0,
                last_seen   TEXT,
                UNIQUE(username, word),
                FOREIGN KEY (username) REFERENCES users(username)
            )
        """)
        conn.commit()
    except Exception as e:
        print(f"[ERR] Falha na migracao: {e}")
    finally:
        conn.close()


# -- Usuarios --

def create_user(username: str, name: str, password_hash: str) -> bool:
    """Insere novo usuario. Retorna True se criado, False se ja existe."""
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO users (username, name, password_hash) VALUES (?, ?, ?)",
            (username, name, password_hash),
        )
        conn.commit()
        return True
    except (sqlite3.IntegrityError, Exception) as e:
        # Turso pode lancar excecao diferente de sqlite3.IntegrityError
        err_msg = str(e).lower()
        if "unique" in err_msg or "constraint" in err_msg or isinstance(e, sqlite3.IntegrityError):
            return False
        raise  # Re-raise se nao for erro de unicidade
    finally:
        conn.close()


def create_user_with_email(username: str, name: str, password_hash: str, email: str, code: str) -> bool:
    """Insere novo usuario com email pendente de verificacao."""
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO users (username, name, password_hash, email, verification_code, email_verified) VALUES (?, ?, ?, ?, ?, 0)",
            (username, name, password_hash, email, code),
        )
        conn.commit()
        return True
    except (sqlite3.IntegrityError, Exception) as e:
        err_msg = str(e).lower()
        if "unique" in err_msg or "constraint" in err_msg or isinstance(e, sqlite3.IntegrityError):
            return False
        raise
    finally:
        conn.close()


def verify_email_code(username: str, code: str) -> bool:
    """Verifica se o codigo bate e ativa a conta."""
    conn = _get_conn()
    try:
        cursor = conn.execute(
            "SELECT verification_code FROM users WHERE username = ?", (username,)
        )
        row = cursor.fetchone()
        if not row:
            return False
        
        saved_code = row["verification_code"]
        if saved_code == code:
            conn.execute("UPDATE users SET email_verified = 1 WHERE username = ?", (username,))
            conn.commit()
            return True
        return False
    finally:
        conn.close()


def is_email_verified(username: str) -> bool:
    """Retorna True se o email esta verificado (ou se eh conta antiga sem email)."""
    conn = _get_conn()
    try:
        row = conn.execute("SELECT email, email_verified FROM users WHERE username = ?", (username,)).fetchone()
        if not row:
            return False
        
        # Se nao tem email (usuario antigo), considera verificado
        if not row["email"]:
            return True
            
        return bool(row["email_verified"])
    finally:
        conn.close()


def get_user(username: str) -> Optional[dict]:
    """Retorna dict do usuario ou None."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT username, name, password_hash FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def is_user_admin(username: str) -> bool:
    """Verifica se usuario eh admin."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT is_admin FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    conn.close()
    if row:
        print(f"[DEBUG] is_user_admin({username}) -> {row['is_admin']} (Type: {type(row['is_admin'])})")
        if row["is_admin"]:
            return True
    return False


def update_user_role(username: str, is_admin: bool) -> None:
    """Promove ou rebaixa usuario a admin."""
    conn = _get_conn()
    conn.execute(
        "UPDATE users SET is_admin = ? WHERE username = ?",
        (1 if is_admin else 0, username),
    )
    conn.commit()
    conn.close()


def update_user_password(username: str, new_hash: str) -> None:
    """Reseta senha do usuario (hash)."""
    conn = _get_conn()
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE username = ?",
        (new_hash, username),
    )
    conn.commit()
    conn.close()


def update_user_xp(username: str, xp: int) -> None:
    """Atualiza XP do usuario diretamente (Admin)."""
    # Atualiza na tabela progress (upsert se nao existir)
    # Mas primeiro precisamos garantir que existe row na progress
    conn = _get_conn()
    # Verifica
    has_prog = conn.execute("SELECT 1 FROM progress WHERE username=?", (username,)).fetchone()
    if has_prog:
        conn.execute("UPDATE progress SET xp = ? WHERE username = ?", (xp, username))
    else:
        # Cria zerado com XP novo
        conn.execute("""
            INSERT INTO progress (username, xp, pagina, arquivo_atual, indice, porc_atual, tentativa, updated_at)
            VALUES (?, ?, 'inicio', 'palavras.csv', 0, 0, 0, datetime('now'))
        """, (username, xp))
    conn.commit()
    conn.close()


def get_all_users_detailed() -> list[dict]:
    """Retorna lista completa de usuarios com XP e status Admin."""
    conn = _get_conn()
    # Join users and progress
    try:
        query = """
            SELECT u.id, u.username, u.name, u.email, u.is_admin, p.xp 
            FROM users u
            LEFT JOIN progress p ON u.username = p.username
            ORDER BY u.id ASC
        """
        rows = conn.execute(query).fetchall()
        # Convert sqlite3.Row to dict to be safe
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[ERR] get_all_users_detailed: {e}")
        return []
    finally:
        try:
            conn.close()
        except:
            pass


def get_all_users() -> dict:
    """
    Retorna dicionario no formato que streamlit-authenticator espera:
    { 'usernames': { 'joao': { 'name': 'Joao', 'password': '<hash>' }, ... } }
    """
    conn = _get_conn()
    rows = conn.execute("SELECT username, name, password_hash FROM users").fetchall()
    conn.close()
    credentials: dict = {"usernames": {}}
    for r in rows:
        credentials["usernames"][r["username"]] = {
            "name": r["name"],
            "password": r["password_hash"],
        }
    return credentials


# -- Progresso Global (tela atual, XP, etc) --

def save_progress(username: str, pagina: str, arquivo_atual: str,
                  indice: int, xp: int, porc_atual: int, tentativa: int) -> None:
    """Upsert do progresso global do usuario."""
    conn = _get_conn()
    conn.execute("""
        INSERT INTO progress (username, pagina, arquivo_atual, indice, xp, porc_atual, tentativa, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(username) DO UPDATE SET
            pagina=excluded.pagina,
            arquivo_atual=excluded.arquivo_atual,
            indice=excluded.indice,
            xp=excluded.xp,
            porc_atual=excluded.porc_atual,
            tentativa=excluded.tentativa,
            updated_at=excluded.updated_at
    """, (username, pagina, arquivo_atual, indice, xp, porc_atual, tentativa,
          datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()


def load_progress(username: str) -> Optional[dict]:
    """Carrega progresso global do usuario. Retorna dict ou None."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT pagina, arquivo_atual, indice, xp, porc_atual, tentativa FROM progress WHERE username = ?",
        (username,),
    ).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


# -- Progresso por Modulo (indice salvo por CSV) --

def save_module_progress(username: str, module_file: str, indice: int) -> None:
    """Salva o indice atual do usuario em um modulo especifico."""
    conn = _get_conn()
    conn.execute("""
        INSERT INTO module_progress (username, module_file, indice, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(username, module_file) DO UPDATE SET
            indice=MAX(excluded.indice, module_progress.indice),
            updated_at=excluded.updated_at
    """, (username, module_file, indice, datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()


def load_module_progress(username: str, module_file: str) -> int:
    """Carrega o indice salvo do usuario em um modulo. Retorna 0 se nao existir."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT indice FROM module_progress WHERE username = ? AND module_file = ?",
        (username, module_file),
    ).fetchone()
    conn.close()
    if row:
        return row["indice"]
    return 0


def load_all_module_progress(username: str) -> dict:
    """Carrega progresso de todos os modulos do usuario. Retorna {module_file: indice}."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT module_file, indice FROM module_progress WHERE username = ?",
        (username,),
    ).fetchall()
    conn.close()
    return {r["module_file"]: r["indice"] for r in rows}


# -- Scores por Licao (melhor nota para badges) --

def save_lesson_score(username: str, module_file: str, lesson_idx: int, score: int) -> None:
    """Salva a nota de uma licao. Mantem apenas a melhor nota (best score)."""
    conn = _get_conn()
    conn.execute("""
        INSERT INTO lesson_scores (username, module_file, lesson_idx, best_score, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(username, module_file, lesson_idx) DO UPDATE SET
            best_score = MAX(excluded.best_score, lesson_scores.best_score),
            updated_at = excluded.updated_at
    """, (username, module_file, lesson_idx, score,
          datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()


def load_lesson_score(username: str, module_file: str, lesson_idx: int) -> int:
    """Carrega a melhor nota de uma licao. Retorna 0 se nao existir."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT best_score FROM lesson_scores WHERE username = ? AND module_file = ? AND lesson_idx = ?",
        (username, module_file, lesson_idx),
    ).fetchone()
    conn.close()
    if row:
        return row["best_score"]
    return 0


# -- Erros por Palavra (Aprendizado Adaptativo) --

def record_word_errors(username: str, wrong_words: list[str], all_words: list[str]) -> None:
    """Registra erros por palavra. Incrementa error_count para erradas, total_seen para todas."""
    conn = _get_conn()
    now = datetime.now(timezone.utc).isoformat()
    try:
        wrong_set = set(wrong_words)
        for w in all_words:
            is_wrong = 1 if w in wrong_set else 0
            conn.execute("""
                INSERT INTO word_errors (username, word, error_count, total_seen, last_seen)
                VALUES (?, ?, ?, 1, ?)
                ON CONFLICT(username, word) DO UPDATE SET
                    error_count = word_errors.error_count + ?,
                    total_seen = word_errors.total_seen + 1,
                    last_seen = ?
            """, (username, w, is_wrong, now, is_wrong, now))
        conn.commit()
    except Exception as e:
        print(f"[ERR] record_word_errors: {e}")
    finally:
        conn.close()


def get_weak_words(username: str, limit: int = 30) -> list[dict]:
    """Retorna palavras com mais erros (error_count >= 2), ordenadas por frequencia de erro."""
    conn = _get_conn()
    try:
        rows = conn.execute("""
            SELECT word, error_count, total_seen
            FROM word_errors
            WHERE username = ? AND error_count >= 2
            ORDER BY error_count DESC
            LIMIT ?
        """, (username, limit)).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[ERR] get_weak_words: {e}")
        return []
    finally:
        conn.close()


def delete_user(username: str) -> bool:
    """Remove completamente um usuario e seus dados."""
    conn = _get_conn()
    try:
        # Remove de todas as tabelas referenciadas
        conn.execute("DELETE FROM progress WHERE username = ?", (username,))
        conn.execute("DELETE FROM module_progress WHERE username = ?", (username,))
        # Verifica se lesson_scores existe antes de tentar deletar
        if "lesson_scores" in _get_tables(conn):
             conn.execute("DELETE FROM lesson_scores WHERE username = ?", (username,))
        if "word_errors" in _get_tables(conn):
             conn.execute("DELETE FROM word_errors WHERE username = ?", (username,))
        conn.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        return True
    except Exception as e:
        print(f"[ERR] delete_user: {e}")
        return False
    finally:
        try:
            conn.close()
        except:
            pass


def _get_tables(conn) -> list[str]:
    """Helper para listar tabelas existentes."""
    try:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [r[0] for r in cursor.fetchall()]
    except:
        return []
