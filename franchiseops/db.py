"""SQLite persistence with transactional imports and portable database paths."""
import os, sqlite3
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parent.parent

def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def connect(path=None):
    path = Path(path or os.environ.get('FRANCHISEOPS_DB', ROOT / 'data' / 'franchiseops.db'))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA journal_mode=WAL')
    return db

def initialize(db):
    db.executescript((ROOT / 'franchiseops' / 'schema.sql').read_text())

def rows(db, query, args=()):
    return [dict(r) for r in db.execute(query, args).fetchall()]

def log(db, action, detail):
    db.execute('INSERT INTO activity(at,action,detail) VALUES(?,?,?)', (now(), action, detail))
