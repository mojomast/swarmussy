-- Phase 2 Migration: runtime world scaffolding (extended)
-- Up: create worlds, runtime_worlds, and runtime_world_entities tables
-- Down: drop the three tables and related indices in reverse order

BEGIN TRANSACTION;

-- Worlds table: consolidated Phase 2 runtime world definitions
CREATE TABLE IF NOT EXISTS worlds (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  map_reference TEXT,
  created_at TEXT NOT NULL
);

-- Runtime worlds: live instances of worlds being executed
CREATE TABLE IF NOT EXISTS runtime_worlds (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  world_id INTEGER NOT NULL,
  status TEXT,
  started_at TEXT,
  ended_at TEXT,
  FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
);

-- Runtime world entities: dynamic composition of entities within a runtime world
CREATE TABLE IF NOT EXISTS runtime_world_entities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  world_id INTEGER NOT NULL,
  entity_id INTEGER NOT NULL,
  pos_x REAL,
  pos_y REAL,
  rotation REAL,
  FOREIGN KEY (world_id) REFERENCES runtime_worlds(id) ON DELETE CASCADE,
  FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
);

-- Indexes to improve join/filter performance on FK columns
CREATE INDEX IF NOT EXISTS idx_runtime_worlds_world_id ON runtime_worlds(world_id);
CREATE INDEX IF NOT EXISTS idx_runtime_world_entities_world_id ON runtime_world_entities(world_id);
CREATE INDEX IF NOT EXISTS idx_runtime_world_entities_entity_id ON runtime_world_entities(entity_id);

COMMIT;

-- Down migrations (reversible)
BEGIN TRANSACTION;
DROP INDEX IF EXISTS idx_runtime_worlds_world_id;
DROP INDEX IF EXISTS idx_runtime_world_entities_world_id;
DROP INDEX IF EXISTS idx_runtime_world_entities_entity_id;
DROP TABLE IF EXISTS runtime_world_entities;
DROP TABLE IF EXISTS runtime_worlds;
DROP TABLE IF EXISTS worlds;
COMMIT;
