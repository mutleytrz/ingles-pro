import sqlite3
import requests
import json
from datetime import datetime, timezone
from config import DB_PATH
from typing import Optional, Any
import streamlit as st


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
# Custom Turso Client (Bypass libsql-client compatibility issues)
# ---------------------------------------------------------------------------
class CustomResultSet:
    def __init__(self, result_dict):
        self.columns = [c["name"] for c in result_dict.get("cols", [])]
        raw_rows = result_dict.get("rows", [])
        self.rows = []
        for r in raw_rows:
            parsed_row = []
            for cell in r:
                if isinstance(cell, dict) and "type" in cell:
                    t = cell["type"]
                    v = cell.get("value")
                    if t == "integer":
                        parsed_row.append(int(v) if v is not None else None)
                    elif t == "float":
                        parsed_row.append(float(v) if v is not None else None)
                    elif t == "null":
                        parsed_row.append(None)
                    else:
                        parsed_row.append(v)
                else:
                    parsed_row.append(cell)
            self.rows.append(tuple(parsed_row))

class TursoClientCustom:
    def __init__(self, url: str, auth_token: str):
        self.url = url.replace("libsql://", "https://")
        if "/v1/execute" not in self.url:
            self.url = self.url.rstrip("/") + "/v1/execute"
        self.auth_token = auth_token
        self.headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        # Use a Session for connection pooling (HTTP Keep-Alive)
        self.session = requests.Session()

    def execute(self, sql: str, params: list | tuple | None = None) -> CustomResultSet:
        stmt = {"sql": sql}
        if params:
            stmt["args"] = [self._encode_value(v) for v in params]
        
        payload = {"stmt": stmt}
        # Connection management via Session.post
        resp = self.session.post(self.url, json=payload, headers=self.headers, timeout=15)
        
        if resp.status_code != 200:
            msg = f"Turso HTTP {resp.status_code}: {resp.text}"
            print(f"[TURSO ERR] {msg}")
            try:
                err_data = resp.json()
                if "error" in err_data:
                    raise Exception(f"Turso Error: {err_data['error']}")
            except Exception as e:
                if not isinstance(e, requests.exceptions.JSONDecodeError): raise
            resp.raise_for_status()
        data = resp.json()
        
        if "result" not in data:
            if "error" in data:
                raise Exception(f"Turso Error: {data['error']}")
            if "message" in data:
                raise Exception(f"Turso Error: {data['message']} (Code: {data.get('code', 'UNKNOWN')})")
            if "results" in data and isinstance(data["results"], list) and len(data["results"]) > 0:
                res = data["results"][0]
                if "result" in res: return CustomResultSet(res["result"])
                return CustomResultSet(res)
            raise KeyError(f"Unexpected Turso response format: {data}")
            
        return CustomResultSet(data["result"])

    def _encode_value(self, v):
        if isinstance(v, bool):
            return {"type": "integer", "value": "1" if v else "0"}
        if isinstance(v, int):
            return {"type": "integer", "value": str(v)}
        if isinstance(v, float):
            return {"type": "float", "value": v}
        if v is None:
            return {"type": "null"}
        return {"type": "text", "value": str(v)}

    def close(self):
        pass

# ---------------------------------------------------------------------------
# TursoCursor — faz o resultado do client parecer um cursor sqlite3
# ---------------------------------------------------------------------------
class TursoCursor:
    """Emula cursor sqlite3 a partir de um ResultSet."""
    def __init__(self, result_set):
        self._rs = result_set
        self._rows = []
        if result_set is not None and hasattr(result_set, 'rows'):
            cols = list(result_set.columns) if hasattr(result_set, 'columns') else []
            self._rows = [DictRow(cols, r) for r in result_set.rows]
        self._index = 0
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
# TursoConnection — wrapper que faz o client parecer sqlite3.Connection
# ---------------------------------------------------------------------------
class TursoConnection:
    """Adapta o client custom pra interface sqlite3."""
    def __init__(self, client):
        self._client = client
        self._closed = False

    def execute(self, sql: str, params=None) -> TursoCursor:
        """Executa SQL e retorna TursoCursor."""
        rs = self._client.execute(sql, params)
        return TursoCursor(rs)

    def executescript(self, script: str):
        """Executa multiplos statements separados por ';'."""
        statements = [s.strip() for s in script.split(';') if s.strip()]
        for stmt in statements:
            self._client.execute(stmt)

    def commit(self):
        pass

    def close(self):
        pass

    def close_for_real(self):
        if not self._closed:
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


# ---------------------------------------------------------------------------
# Flag global: True se estamos usando Turso
# ---------------------------------------------------------------------------
_using_turso = False
_turso_singleton: TursoConnection | None = None 


def _get_conn():
    """Retorna conexao reutilizavel (singleton para Turso, nova para SQLite)."""
    global _using_turso, _turso_singleton
    import config

    # Se tiver credenciais do Turso, tenta primeiro a lib nativa (mais rápida: WebSockets/gRPC)
    if config.TURSO_DB_URL and config.TURSO_AUTH_TOKEN:
        if _turso_singleton is not None and not _turso_singleton._closed:
            return _turso_singleton
        try:
            from libsql_client import create_client_sync
            url = config.TURSO_DB_URL
            client = create_client_sync(url, auth_token=config.TURSO_AUTH_TOKEN)
            _using_turso = True
            _turso_singleton = TursoConnection(client)
            return _turso_singleton
        except Exception as e:
            # Fallback para o cliente customizado se a lib nativa falhar (ex: erro de compatibilidade)
            print(f"[DB] Fallback Turso: {e}. Usando TursoClientCustom.")
            try:
                client = TursoClientCustom(config.TURSO_DB_URL, config.TURSO_AUTH_TOKEN)
                _using_turso = True
                _turso_singleton = TursoConnection(client)
                return _turso_singleton
            except Exception as e2:
                print(f"[DB] Erro crítico no fallback: {e2}")

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
            email       TEXT    UNIQUE,
            is_admin    BOOLEAN DEFAULT 0,
            is_premium  BOOLEAN DEFAULT 0,
            plan_type   TEXT    DEFAULT 'free',
            premium_until TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS settings (
            key         TEXT PRIMARY KEY,
            value       TEXT
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

        CREATE TABLE IF NOT EXISTS payments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT,
            payment_id  TEXT,
            status      TEXT,
            amount      REAL,
            currency    TEXT,
            external_reference TEXT,
            created_at  TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (username) REFERENCES users(username)
        );
    """)
    conn.commit()
    _check_migrations()

def _check_migrations():
    """Verifica e aplica migracoes de schema necessarias (ex: is_admin).
    OTIMIZADO: usa uma unica conexao e um unico commit."""
    conn = _get_conn()
    try:
        # Check if is_admin exists
        cursor = conn.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        if "is_admin" not in columns:
            print("[MIGRATION] Adicionando coluna is_admin na tabela users...")
            conn.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")

        # Email auth migrations
        if "email" not in columns:
            print("[MIGRATION] Adicionando colunas de email na tabela users...")
            conn.execute("ALTER TABLE users ADD COLUMN email TEXT")
            conn.execute("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0")
            conn.execute("ALTER TABLE users ADD COLUMN verification_code TEXT")

        if "is_premium" not in columns:
            print("[MIGRATION] Adicionando coluna is_premium na tabela users...")
            conn.execute("ALTER TABLE users ADD COLUMN is_premium BOOLEAN DEFAULT 0")

        if "plan_type" not in columns:
            print("[MIGRATION] Adicionando colunas de plano na tabela users...")
            conn.execute("ALTER TABLE users ADD COLUMN plan_type TEXT DEFAULT 'free'")
            conn.execute("ALTER TABLE users ADD COLUMN premium_until TEXT")

        # Settings table migration
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        # Initialize default settings if not present
        _init_default_settings(conn)

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

        # Payments table migration
        conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT,
                payment_id  TEXT,
                status      TEXT,
                amount      REAL,
                currency    TEXT,
                external_reference TEXT,
                created_at  TEXT    DEFAULT (datetime('now')),
                FOREIGN KEY (username) REFERENCES users(username)
            )
        """)
        # Um unico commit para todas as migracoes
        conn.commit()
    except Exception as e:
        print(f"[ERR] Falha na migracao: {e}")

def _init_default_settings(conn):
    """Inicializa precos e visibilidade padrao."""
    defaults = {
        "price_mensal": "14.99",
        "price_anual": "159.00",
        "price_vitalicio": "499.00",
        "show_vitalicio": "0",  # Oculto por padrao conforme pedido
        "download_pc_url": "",
        "download_mobile_url": ""
    }
    for k, v in defaults.items():
        conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

def get_setting(key: str, default: str = "") -> str:
    conn = _get_conn()
    try:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default
    except Exception:
        return default
    finally:
        conn.close()

def update_setting(key: str, value: str):
    conn = _get_conn()
    try:
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit()
    except Exception as e:
        print(f"[ERR] update_setting: {e}")
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
        # Invalida caches para o autenticador ver o novo usuário
        get_all_users.clear()
        get_user.clear()
        return True
    except (sqlite3.IntegrityError, Exception) as e:
        # Turso pode lancar excecao diferente de sqlite3.IntegrityError
        err_msg = str(e).lower()
        if "unique" in err_msg or "constraint" in err_msg or isinstance(e, sqlite3.IntegrityError):
            return False
        raise  # Re-raise se nao for erro de unicidade


def create_user_with_email(username: str, name: str, password_hash: str, email: str, code: str) -> bool:
    """Insere novo usuario com email pendente de verificacao."""
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO users (username, name, password_hash, email, verification_code, email_verified) VALUES (?, ?, ?, ?, ?, 0)",
            (username, name, password_hash, email, code),
        )
        conn.commit()
        # Invalida caches para o autenticador ver o novo usuário
        get_all_users.clear()
        get_user.clear()
        return True
    except (sqlite3.IntegrityError, Exception) as e:
        err_msg = str(e).lower()
        if "unique" in err_msg or "constraint" in err_msg or isinstance(e, sqlite3.IntegrityError):
            return False
        raise


def verify_email_code(username: str, code: str) -> bool:
    """Verifica se o codigo bate e ativa a conta."""
    conn = _get_conn()
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
        # Invalida caches para o autenticador ver que o email foi verificado
        get_all_users.clear()
        get_user.clear()
        return True
    return False


def is_email_verified(username: str) -> bool:
    """Retorna True se o email esta verificado (ou se eh conta antiga sem email)."""
    conn = _get_conn()
    row = conn.execute("SELECT email, email_verified FROM users WHERE username = ?", (username,)).fetchone()
    if not row:
        return False
    
    # Se nao tem email (usuario antigo), considera verificado
    if not row["email"]:
        return True
        
    return bool(row["email_verified"])


@st.cache_data(ttl=60, show_spinner=False)
def get_user(username: str) -> Optional[dict]:
    """Retorna dict do usuario ou None. Cacheado por 60s."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT username, name, password_hash, is_premium, plan_type, premium_until FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if row:
        return dict(row)
    return None


@st.cache_data(ttl=120, show_spinner=False)
def is_user_admin(username: str) -> bool:
    """Verifica se usuario eh admin. Cacheado por 2 min."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT is_admin FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if row:
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
    # Limpa cache do is_user_admin
    is_user_admin.clear()


def update_user_password(username: str, new_hash: str) -> None:
    """Reseta senha do usuario (hash)."""
    conn = _get_conn()
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE username = ?",
        (new_hash, username),
    )
    conn.commit()


def update_user_premium(username: str, is_premium: bool, plan_type: str = "free") -> None:
    """Atualiza status Premium do usuario com tipo de plano e data de expiração."""
    from datetime import timedelta
    conn = _get_conn()
    
    until = None
    if is_premium:
        now = datetime.now(timezone.utc)
        if plan_type == "mensal":
            until = (now + timedelta(days=31)).isoformat()
        elif plan_type == "anual":
            until = (now + timedelta(days=366)).isoformat()
        elif plan_type == "vitalicio":
            until = None # Sem expiração
    
    conn.execute(
        "UPDATE users SET is_premium = ?, plan_type = ?, premium_until = ? WHERE username = ?",
        (1 if is_premium else 0, plan_type, until, username),
    )
    conn.commit()
    # Limpa cache para refletir a mudanca imediatamente
    get_all_users_detailed.clear()
    get_user.clear()

def log_payment(username: str, payment_id: str, status: str, amount: float, currency: str = "BRL", external_ref: str = ""):
    """Registra um log de pagamento na tabela payments."""
    conn = _get_conn()
    try:
        conn.execute("""
            INSERT INTO payments (username, payment_id, status, amount, currency, external_reference)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, payment_id, status, amount, currency, external_ref))
        conn.commit()
    except Exception as e:
        print(f"[ERR] log_payment: {e}")
    finally:
        conn.close()

def get_all_payments() -> list[dict[str, Any]]:
    """Retorna todos os registros de pagamentos para o painel ADM."""
    conn = _get_conn()
    try:
        cursor = conn.execute("""
            SELECT p.*, u.name as user_fullname 
            FROM payments p
            LEFT JOIN users u ON p.username = u.username
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[ERR] get_all_payments: {e}")
        return []
    finally:
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


@st.cache_data(ttl=10, show_spinner=False)
def get_all_users_detailed() -> list[dict]:
    """Retorna lista completa de usuarios com XP, status Admin e Premium."""
    conn = _get_conn()
    # Join users and progress
    try:
        query = """
            SELECT u.id, u.username, u.name, u.email, u.is_admin, u.is_premium, u.plan_type, u.premium_until, p.xp 
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


@st.cache_data(ttl=300, show_spinner=False)
def get_all_users() -> dict:
    """
    Retorna dicionario no formato que streamlit-authenticator espera:
    { 'usernames': { 'joao': { 'name': 'Joao', 'password': '<hash>' }, ... } }
    """
    conn = _get_conn()
    rows = conn.execute("SELECT username, name, password_hash FROM users").fetchall()
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


def load_progress(username: str) -> Optional[dict]:
    """Carrega progresso global do usuario. Retorna dict ou None."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT pagina, arquivo_atual, indice, xp, porc_atual, tentativa FROM progress WHERE username = ?",
        (username,),
    ).fetchone()
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


def load_module_progress(username: str, module_file: str) -> int:
    """Carrega o indice salvo do usuario em um modulo. Retorna 0 se nao existir."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT indice FROM module_progress WHERE username = ? AND module_file = ?",
        (username, module_file),
    ).fetchone()
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


def load_lesson_score(username: str, module_file: str, lesson_idx: int) -> int:
    """Carrega a melhor nota de uma licao. Retorna 0 se nao existir."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT best_score FROM lesson_scores WHERE username = ? AND module_file = ? AND lesson_idx = ?",
        (username, module_file, lesson_idx),
    ).fetchone()
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


def get_student_analytics(username: str) -> dict:
    """Retorna analytics completo de um aluno para o painel admin.
    Inclui: progresso por modulo, scores por licao, e palavras fracas."""
    conn = _get_conn()
    result = {
        'module_progress': {},
        'lesson_scores': {},
        'weak_words': [],
        'xp': 0,
    }
    try:
        # XP
        xp_row = conn.execute(
            "SELECT xp FROM progress WHERE username = ?", (username,)
        ).fetchone()
        if xp_row:
            result['xp'] = xp_row['xp'] or 0

        # Progresso por modulo {module_file: indice}
        mod_rows = conn.execute(
            "SELECT module_file, indice FROM module_progress WHERE username = ?",
            (username,),
        ).fetchall()
        result['module_progress'] = {r['module_file']: r['indice'] for r in mod_rows}

        # Scores por licao {(module_file, lesson_idx): best_score}
        score_rows = conn.execute(
            "SELECT module_file, lesson_idx, best_score FROM lesson_scores WHERE username = ?",
            (username,),
        ).fetchall()
        scores_dict = {}
        for r in score_rows:
            mod = r['module_file']
            if mod not in scores_dict:
                scores_dict[mod] = {}
            scores_dict[mod][r['lesson_idx']] = r['best_score']
        result['lesson_scores'] = scores_dict

        # Palavras fracas (todas, sem filtro de minimo)
        word_rows = conn.execute("""
            SELECT word, error_count, total_seen
            FROM word_errors
            WHERE username = ? AND error_count >= 1
            ORDER BY error_count DESC
            LIMIT 50
        """, (username,)).fetchall()
        result['weak_words'] = [dict(r) for r in word_rows]
    except Exception as e:
        print(f"[ERR] get_student_analytics: {e}")
    return result


def delete_user(username: str) -> bool:
    """Remove completamente um usuario e seus dados."""
    conn = _get_conn()
    try:
        # Lista tabelas uma vez so (reusa a mesma conexao)
        tables = _get_tables(conn)
        # Remove de todas as tabelas referenciadas
        conn.execute("DELETE FROM progress WHERE username = ?", (username,))
        conn.execute("DELETE FROM module_progress WHERE username = ?", (username,))
        if "lesson_scores" in tables:
             conn.execute("DELETE FROM lesson_scores WHERE username = ?", (username,))
        if "word_errors" in tables:
             conn.execute("DELETE FROM word_errors WHERE username = ?", (username,))
        conn.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        # Limpa caches apos deletar
        is_user_admin.clear()
        get_all_users.clear()
        get_all_users_detailed.clear()
        return True
    except Exception as e:
        print(f"[ERR] delete_user: {e}")
        return False


def _get_tables(conn) -> list[str]:
    """Helper para listar tabelas existentes."""
    try:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [r[0] for r in cursor.fetchall()]
    except:
        return []
