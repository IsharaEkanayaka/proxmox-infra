import os
import sqlite3

from . import config


def get_db() -> sqlite3.Connection:
    os.makedirs(config.DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS environments (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS clusters (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            node_count INTEGER NOT NULL,
            control_plane_count INTEGER NOT NULL DEFAULT 1,
            worker_count INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'creating',
            ip_start INTEGER NOT NULL,
            environment_id TEXT REFERENCES environments(id) ON DELETE SET NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            cluster_id TEXT NOT NULL REFERENCES clusters(id),
            type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            error TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS ip_allocations (
            cluster_id TEXT PRIMARY KEY REFERENCES clusters(id),
            ip_start INTEGER NOT NULL,
            ip_count INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS namespaces (
            id TEXT PRIMARY KEY,
            cluster_id TEXT NOT NULL REFERENCES clusters(id),
            name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL,
            UNIQUE(cluster_id, name)
        );

        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'viewer',
            api_key TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            resource_type TEXT NOT NULL,
            resource_id TEXT NOT NULL,
            access TEXT NOT NULL DEFAULT 'read',
            UNIQUE(user_id, resource_type, resource_id)
        );
    """)
    conn.commit()
    conn.close()


def _migrate(conn: sqlite3.Connection):
    """Run any necessary schema migrations."""
    # Drop UNIQUE constraint on clusters.name so deleted cluster names can be reused
    row = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='clusters'").fetchone()
    if row and 'name TEXT UNIQUE' in row[0]:
        conn.executescript("""
            PRAGMA foreign_keys = OFF;
            ALTER TABLE clusters RENAME TO _clusters_old;
            CREATE TABLE clusters (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                node_count INTEGER NOT NULL,
                control_plane_count INTEGER NOT NULL DEFAULT 1,
                worker_count INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'creating',
                ip_start INTEGER NOT NULL,
                environment_id TEXT REFERENCES environments(id) ON DELETE SET NULL,
                created_at TEXT NOT NULL
            );
            INSERT INTO clusters SELECT * FROM _clusters_old;
            DROP TABLE _clusters_old;
            PRAGMA foreign_keys = ON;
        """)
