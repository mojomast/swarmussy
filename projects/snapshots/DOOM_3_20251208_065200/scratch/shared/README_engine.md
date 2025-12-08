Engine Core (Doom-like) scaffold

Overview
- Provides a minimal ECS-like Engine core that integrates with the in-memory store (scratch/shared/store.ts).
- Deteministic gravity-like tick that updates player positions on the Y axis per tick.
- Exposes a simple API compatible with the Engine interface: start(), tick(), stop(), status().

Public interfaces
- EngineState: running, tick, fps, lastTickMs
- Engine: start():Promise<EngineState>, tick():Promise<EngineState>, stop():void, status():EngineState
- LevelState/PlayerState: defined in scratch/shared/models.ts

Integration with the in-memory store
- The EngineCore reads from store or an override store provided at construction: new EngineCore({ levels: {...} })
- On each tick, the engine applies a deterministic gravity to all players in all loaded levels (p.y += 1 per tick) and clamps to the level floor.
- The gravity step demonstrates a deterministic, test-friendly tick that can be extended with more systems (movement, collisions, rendering hooks).

How to run tests
- Tests under scratch/shared/tests/engine_tests.ts exercise initialization, tick progression, and integration behavior.
- Ensure you have the project’s test runner configured (e.g., Vitest) and run the tests in the shared workspace.

Extensibility
- To add new systems (e.g., collision, input, AI), extend EngineCore and add per-tick system execution loops, maintaining deterministic behavior for tests.
- The EngineCore currently operates on LevelState.players; you can extend to other world primitives as needed.
