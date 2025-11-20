"""
Tiny sqlite wrapper functions.
- init_db creates the users table if it doesn't exist.
- get_db_connection returns sqlite3.Connection with Row factory.
"""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    age INTEGER,
    bio TEXT
);
"""

def init_db(db_path: str):
    """Create the database file and table if not present."""
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()

def get_db_connection(db_path: str):
    """Return a sqlite3 connection with row factory set to sqlite3.Row."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
    
