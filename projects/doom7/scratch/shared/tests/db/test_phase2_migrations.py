import pytest
import sqlite3
import os

DB_PATH = "/tmp/phase2_test.db"

@pytest.fixture(scope="function")
def conn():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    yield conn
    conn.close()
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)


def test_phase2_migration_runs(conn):
    cur = conn.cursor()
    # Read Up migration for phase2
    with open('shared/db/migrations/2025_02_phase2_runtime_worlds.sql', 'r') as f:
        sql = f.read()
    up_sql = sql.split("\n-- Down", 1)[0]
    cur.executescript(up_sql)

    # basic checks
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='worlds';")
    assert cur.fetchone() is not None
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='runtime_worlds';")
    assert cur.fetchone() is not None
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='runtime_world_entities';")
    assert cur.fetchone() is not None
