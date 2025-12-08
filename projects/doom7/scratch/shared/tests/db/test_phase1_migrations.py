import pytest
import sqlite3
import os

DB_PATH = "/tmp/phase1_test.db"

@pytest.fixture(scope="function")
def conn():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    yield conn
    conn.close()
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

def test_phase1_migration_runs(conn):
    cur = conn.cursor()
    with open('shared/db/migrations/2025_01_phase1_consolidation.sql', 'r') as f:
        sql = f.read()
    # Execute only the Up portion of the migration if Down statements are present
    up_sql = sql.split("\n-- Down", 1)[0]
    cur.executescript(up_sql)

    # Verify core tables created
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    assert cur.fetchone() is not None
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='levels';")
    assert cur.fetchone() is not None
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assets';")
    assert cur.fetchone() is not None
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='entities';")
    assert cur.fetchone() is not None
