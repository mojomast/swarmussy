import sqlite3
import os

DB_PATH = os.environ.get('TEST_DB', ':memory:')

import unittest

class TestDBSchema(unittest.TestCase):
    def setUp(self):
        # connect to test DB
        self.conn = sqlite3.connect(DB_PATH)
        self.cur = self.conn.cursor()

    def tearDown(self):
        self.cur.close()
        self.conn.close()

    def test_connect(self):
        self.assertIsNotNone(self.conn)

    def test_migrate(self):
        # basic migration: create migrations table and apply 01_initial
        self.cur.execute("CREATE TABLE IF NOT EXISTS migrations (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);")
        self.conn.commit()
        # Apply initial schema from SQL file
        with open('shared/db/migrations/01_initial.sql','r') as f:
            sql = f.read()
        # split by semicolon; naive approach but fine for simple migrations
        for stmt in [s.strip() for s in sql.split(';') if s.strip()]:
            self.cur.execute(stmt)
        self.conn.commit()
        # basic assertions
        self.cur.execute("SELECT name FROM migrations WHERE name='01_initial';")
        row = self.cur.fetchone()
        self.assertIsNotNone(row)
