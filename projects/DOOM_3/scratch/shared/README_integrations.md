Engine integration notes for Frontend Editor UI

- Wire Editor UI to EngineCore via a mock provider implementing Engine interface.
- Expose Engine.start(), Engine.tick() from the mock to drive HUD.
- Provide a /api/engine/state endpoint prototype for future real engine integration.
