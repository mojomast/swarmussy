-- Phase 1 consolidation migration (SQLite-compatible)
-- Up: apply core Phase 1 schema and prune ephemeral tables
BEGIN;

-- Prune known temporary/legacy tables if they exist (safe no-ops if absent)
DROP TABLE IF EXISTS phase1_tmp_imports;
DROP TABLE IF EXISTS debug_logs;
DROP TABLE IF EXISTS old_events;

-- Core Phase 1 schema (idempotent CREATEs)
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  email TEXT UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS levels (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  difficulty INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS assets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  type TEXT,
  data TEXT
);

CREATE TABLE IF NOT EXISTS entities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  level_id INTEGER,
  FOREIGN KEY (level_id) REFERENCES levels(id) ON DELETE SET NULL
);

-- Metadata to indicate Phase 1 consolidation status
CREATE TABLE IF NOT EXISTS schema_phase1_meta (
  key TEXT PRIMARY KEY,
  value TEXT
);

INSERT OR IGNORE INTO schema_phase1_meta (key, value) VALUES ('phase', 'consolidated');

COMMIT;

-- Down: revert Phase 1 consolidation (drop core objects introduced above)
DROP TABLE IF EXISTS assets;
DROP TABLE IF EXISTS entities;
DROP TABLE IF EXISTS levels;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS schema_phase1_meta;

DROP TABLE IF EXISTS phase1_tmp_imports;
DROP TABLE IF EXISTS debug_logs;
DROP TABLE IF EXISTS old_events;
