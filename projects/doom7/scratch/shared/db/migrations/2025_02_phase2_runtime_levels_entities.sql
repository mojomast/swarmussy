-- Phase 2 Migration: runtime levels and entities scaffolding
-- Up: create runtime_levels and runtime_entities tables
-- Down: drop the two tables and related indices in reverse order

BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS runtime_levels (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  world_id INTEGER NOT NULL,
  level_template_id INTEGER NOT NULL,
  status TEXT,
  started_at TEXT,
  ended_at TEXT,
  FOREIGN KEY (world_id) REFERENCES runtime_worlds(id) ON DELETE CASCADE,
  FOREIGN KEY (level_template_id) REFERENCES levels(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS runtime_entities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  world_id INTEGER NOT NULL,
  entity_id INTEGER NOT NULL,
  level_id INTEGER,
  pos_x REAL,
  pos_y REAL,
  rotation REAL,
  FOREIGN KEY (world_id) REFERENCES runtime_worlds(id) ON DELETE CASCADE,
  FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
  FOREIGN KEY (level_id) REFERENCES runtime_levels(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_runtime_levels_world_id ON runtime_levels(world_id);
CREATE INDEX IF NOT EXISTS idx_runtime_levels_level_template_id ON runtime_levels(level_template_id);
CREATE INDEX IF NOT EXISTS idx_runtime_entities_world_id ON runtime_entities(world_id);
CREATE INDEX IF NOT EXISTS idx_runtime_entities_entity_id ON runtime_entities(entity_id);
CREATE INDEX IF NOT EXISTS idx_runtime_entities_level_id ON runtime_entities(level_id);

COMMIT;

-- Down migrations (reversible)
BEGIN TRANSACTION;
DROP INDEX IF EXISTS idx_runtime_levels_world_id;
DROP INDEX IF EXISTS idx_runtime_levels_level_template_id;
DROP INDEX IF EXISTS idx_runtime_entities_world_id;
DROP INDEX IF EXISTS idx_runtime_entities_entity_id;
DROP INDEX IF EXISTS idx_runtime_entities_level_id;
DROP TABLE IF EXISTS runtime_entities;
DROP TABLE IF EXISTS runtime_levels;
COMMIT;
