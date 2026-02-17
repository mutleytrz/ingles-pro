-- init_db.sql — Script de criacao manual das tabelas
-- Execute com: sqlite3 ingles_pro.db < init_db.sql

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    UNIQUE NOT NULL,
    name          TEXT    NOT NULL,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    DEFAULT (datetime('now'))
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
