# Doom-Style 2.5D FPS with In-Engine Editor - Master Plan

Project Overview
- Build a minimal, playable Doom-style 2.5D FPS using TypeScript, Vite, ESBuild, and HTML5 Canvas/WebGL, with an in-engine grid-based level editor and JSON save/load for monsters, weapons, and assets. All code lives in a single repo with modular components and a lightweight UI for the editor.

Scope
- Core 2.5D raycasting renderer on a grid map
- Player controls: WASD movement, mouse look, shooting
- Simple enemy AI with basic attack behavior
- In-engine level editor (grid-based) plus editors for monsters, weapons, and assets
- JSON save/load for levels and assets; export/import hooks
- Lightweight UI for editor panels; no heavy game engine dependencies
- TS-only stack; Vite dev server; ESBuild bundling; HTML5 Canvas/WebGL rendering path

Architecture
- Core Engine (src/engine)
  - Input handling
  - Game loop and timing
  - Rendering (raycasting-based 2.5D) and optional WebGL path
  - Collision and camera management
- Game Logic (src/game)
  - Player entity, weapon handling, enemy entities
  - World/map data, simple physics
- Editor (src/editor)
  - levels/ (grid maps)
  - entities/ (monsters, items, NPCs)
  - assets/ (monster/weapon/asset definitions)
- UI (src/ui)
  - Editor panels, property sheets, JSON save/load controls
- Data (src/data)
  - Default assets, sample maps, example JSON presets
- Common (src/common)
  - Math utilities, constants, types
- Build/Tooling
  - Vite config, TypeScript config, lint/test setup

Tech Stack
- Language: TypeScript
- Build: Vite (dev server), ESBuild (bundling)
- Rendering: HTML5 Canvas with optional WebGL path
- Storage: JSON save/load
- Pattern: Lightweight ECS or component-based architecture for extensibility

Planned File Structure (high-level)
- scratch/shared/src/engine/
- scratch/shared/src/game/
- scratch/shared/src/editor/{levels,entities,assets}
- scratch/shared/src/ui/
- scratch/shared/src/common/
- scratch/shared/data/
- scratch/shared/master_plan.md
- scratch/shared/devplan.md

Milestones
- M1 Scaffolding: TypeScript project skeleton, Vite config, repo structure
- M2 Engine Skeleton: core loop, input handling, camera, placeholder renderer
- M3 Player & Shooting: WASD movement, mouselook, basic firing
- M4 Enemies: basic AI and movement
- M5 Level Editor: grid-based level editor with JSON save/load
- M6 Asset Editors: monsters, weapons, assets editors with JSON
- M7 Polish: UI refinements, basic tests, packaging

Granular Task List (sample for Phase 1 and initial Phase 2 planning)
- T1: Create TS project scaffold (vite.config.ts, tsconfig.json, folder structure under scratch/shared)
- T2: Implement Engine core scaffolding (types, GameLoop interface, timestep strategy)
- T3: Establish Renderer interface and placeholder 2.5D raycasting path
- T4: Create Player controller skeleton (position, orientation, WASD handling)
- T5: Create basic Shooting mechanism skeleton (aim, trigger, impact)
- T6: Define Enemy component structure and basic AI placeholders
- T7: Set up Editor skeleton (levels/entities/assets folders and JSON schema)
- T8: Implement basic UI shell for Editor panels (no payload yet)
- T9: JSON serialization/deserialization plumbing for levels and assets
- T10: Documentation skeleton (README.md and developer guide)

Dependencies & Reading
- Align with shared/docs and data presets in scratch/shared/data
- Read initial JSON schemas and sample maps as reference when implementing editor migrations

Definition of Done
- Core loop runs at target FPS, canvas rendering is visible, and player can move
- Shooting is functional (hitscan or simple projectile)
- Simple enemies exist and demonstrate basic AI
- Level editor saves/loads to JSON with basic map preview
- Asset/monster/weapon editors save definitions to JSON
- All features have basic validation and no hard crashes

Risks & Mitigations
- Risk: Rendering path complexity may blow up. Mitigation: Start with simple Canvas2D raycasting and defer WebGL optimizations behind a toggle.
- Risk: Editor integration may become coupling-heavy. Mitigation: Keep Editor surface separated via JSON contracts and clear API surfaces.
