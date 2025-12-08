Master Plan for a Minimal Doom-Style 2.5D FPS with In-Engine Editors

Overview:
- Tech: TypeScript, Vite, ESBuild, HTML5 Canvas/WebGL, no heavyweight engine
- Architecture: ECS-like, modular folders for engine/game/editor assets
- Deliverables: game core, level editor, entity/editor tooling, save/load, docs, build scripts

High-level Architecture:
- src/engine: ECS core, rendering, input, audio
- src/game: game loop, player, enemies, weapons, items, levels
- src/editor/levels: level editor UI/data structures
- src/editor/entities: editors for monster/weapon/asset metadata
- tools/build: npm scripts for dev/build
- shared/docs: BUILD.md, PLAY.md, DevPlan

Non-functional:
- TypeScript-first, strict types, modular imports, unit-test hooks
- Canvas/WebGL rendering with a minimal render pipeline
- Persist assets and levels to JSON in save/load

Milestones:
- M1: Core ECS + render loop blueprint
- M2: Player controls (WASD, mouse look)
- M3: Basic enemies + shooting
- M4: Level editor UI + save/load
- M5: Entity/weapon editors + metadata
- M6: Docs, build scripts, cross-platform instructions

Risks:
- Rendering performance in Canvas/WebGL, input latency, editor complexity

Plan ready for execution.