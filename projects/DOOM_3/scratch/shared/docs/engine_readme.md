Engine Core Integration Plan

Overview:
- A minimal ECS-like engine core designed for a Doom-like loop using a deterministic world snapshot (WorldSnapshot).
- Exposes Engine API: start/stop/tick, onUpdate, registerStep to support tests and future integration.
- Gravity-like per-tick update to validate the integration path with the in-memory store of levels/players.

API surface:
- Engine(provider: WorldProvider)
- engine.start()
- engine.stop()
- engine.tick(deltaMs: number)
- engine.onUpdate(cb: WorldUpdateCallback)
- engine.registerStep(step: PluginStep)

World snapshot model:
- WorldSnapshot contains levels, each with players that have x, y, hp, etc.

Testing plan:
- Create a StaticWorldProvider returning a deep-copied world; use engine.tick to mutate world and verify changes; use onUpdate to observe changes.

Notes:
- This is a deterministic, test-friendly engine core scaffold, not a full runtime loop.