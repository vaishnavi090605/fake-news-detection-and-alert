"""
Day 5 — Database Setup
-----------------------
Creates the SQLite schema for the whole project:

    users          -> registered accounts
    fake_news_db   -> confirmed fake news, one row per DISTINCT fake story
                       (detection_count increments when the same story
                       resurfaces instead of creating duplicate rows)
    news_history   -> every news/text a user has ever submitted + result
    alerts         -> generated when a fake story is detected repeatedly
    reports        -> user-submitted "report this as fake" entries

Run once to (re)create the database:
    python database/db_setup.py
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "fake_news.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT UNIQUE NOT NULL,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'user',   -- 'user' or 'admin'
    location      TEXT DEFAULT 'Hyderabad, India',
    full_name     TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS fake_news_db (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    original_text      TEXT NOT NULL,
    clean_text         TEXT NOT NULL,
    tfidf_vector       BLOB NOT NULL,              -- pickled sparse TF-IDF vector
    category           TEXT NOT NULL DEFAULT 'Other',
    source             TEXT,
    first_detected_at  TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen_at       TEXT NOT NULL DEFAULT (datetime('now')),
    detection_count    INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS news_history (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id               INTEGER,
    original_text         TEXT NOT NULL,
    clean_text            TEXT NOT NULL,
    prediction            TEXT NOT NULL,           -- 'Fake' or 'Genuine'
    confidence            REAL NOT NULL,
    category              TEXT,
    is_repeated           INTEGER NOT NULL DEFAULT 0,
    matched_fake_news_id  INTEGER,
    similarity_score      REAL,
    checked_at            TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (matched_fake_news_id) REFERENCES fake_news_db(id)
);

CREATE TABLE IF NOT EXISTS alerts (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    fake_news_id   INTEGER NOT NULL,
    alert_type     TEXT NOT NULL,                  -- 'repeated_detection', 'high_risk_category'
    message        TEXT NOT NULL,
    severity       TEXT NOT NULL DEFAULT 'medium',  -- 'low', 'medium', 'high'
    status         TEXT NOT NULL DEFAULT 'new',     -- 'new', 'reviewed', 'sent_to_authorities'
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (fake_news_id) REFERENCES fake_news_db(id)
);

CREATE TABLE IF NOT EXISTS reports (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER,
    reported_text  TEXT NOT NULL,
    reason         TEXT,
    status         TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'reviewed', 'dismissed'
    admin_notes    TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS police_reports (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id          INTEGER NOT NULL,
    target_authority  TEXT NOT NULL DEFAULT 'bachuvaishnavi098@gmail.com',
    report_title      TEXT NOT NULL,
    report_details    TEXT NOT NULL,
    status            TEXT NOT NULL DEFAULT 'draft_prepared',
    created_at        TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (alert_id) REFERENCES alerts(id)
);

CREATE INDEX IF NOT EXISTS idx_history_user ON news_history(user_id);
CREATE INDEX IF NOT EXISTS idx_history_repeated ON news_history(is_repeated);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
"""


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    
    # Ensure new columns exist on existing database
    try:
        conn.execute("ALTER TABLE users ADD COLUMN location TEXT DEFAULT 'Hyderabad, India'")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE users ADD COLUMN full_name TEXT")
    except Exception:
        pass

    # Ensure default admin user (admin / admin123) is pre-configured
    admin_exists = conn.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
    if not admin_exists:
        from passlib.context import CryptContext
        pwd_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
        pw_hash = pwd_ctx.hash("admin123")
        conn.execute(
            "INSERT INTO users (username, email, password_hash, role, location, full_name) VALUES (?, ?, ?, ?, ?, ?)",
            ("admin", "bachuvaishnavi098@gmail.com", pw_hash, "admin", "Anurag University, Hyderabad", "System Administrator"),
        )

    conn.commit()
    conn.close()
    print(f"Database ready -> {DB_PATH}")


def get_connection():
    """Used by other modules (repeated_news_detector.py, FastAPI app) to get a connection."""
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        conn.execute("PRAGMA journal_mode = WAL")
    except Exception:
        pass
    return conn



if __name__ == "__main__":
    init_db()