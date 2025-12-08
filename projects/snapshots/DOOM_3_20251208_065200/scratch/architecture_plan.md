Architect: Engine/UI wiring plan

Tasks:
- Expose Engine status via Editor: add EngineStatus widget and wire mock provider.
- Update /api/engine/state endpoint prototype (GET /api/engine/state) returning EngineState shape.
- Ensure Editor LevelEditor uses Engine to tick and display status HUD.
