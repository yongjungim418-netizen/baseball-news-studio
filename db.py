import sqlite3
from config import DB_PATH


def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init():
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS articles(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          url TEXT UNIQUE, title TEXT, source TEXT, league TEXT,
          published TEXT, snippet TEXT, collected_at TEXT,
          status TEXT DEFAULT 'new', batch_date TEXT, slot INTEGER, summary TEXT);
        CREATE TABLE IF NOT EXISTS batches(
          date TEXT PRIMARY KEY, status TEXT DEFAULT 'draft', updated_at TEXT);
        """)
