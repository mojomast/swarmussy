Engine Core (Doom-like) skeleton scaffold

Overview
- Provides a minimal Engine interface implementation used by tests and examples. The canonical Engine.ts file is currently locked for exclusive editing, so this module demonstrates a concrete EngineImpl-based approach for test scaffolding and integration.

Public interfaces
- EngineState: running, tick, fps, lastTickMs
- Engine: start():Promise<EngineState>, tick():Promise<EngineState>, stop():void, status():EngineState
- World/state access via World and EngineImpl glue

Usage
- Import EngineImpl from scratch/shared/engine/engine_impl.ts and construct with an in-memory World to drive deterministic gravity-like ticks for tests.
- Add test cases under scratch/shared/tests/ to verify lifecycle and world mutation behaviors.

Extensibility
- Extend EngineImpl to wire to additional systems (physics, collisions, rendering hooks) while preserving deterministic tick semantics for tests.
