Doom-style 2.5D FPS with in-engine editors - Master Plan

Overview
- Build a minimal, playable FPS inspired by classic Doom, using TypeScript, Vite + ESBuild for tooling, and HTML5 Canvas/WebGL for rendering.
- Include an in-engine, grid-based level editor and simple editors for monsters, weapons, and asset metadata. All editors are code-driven UIs with file-based JSON saves/loads.
- Architecture is ECS-like (Entities, Components, Systems) with a small runtime and a few editor modules to manipulate data and export/import JSON.
- All code lives in a single repo with a clean structure and minimal dependencies, suitable for Windows/macOS/Linux via npm scripts.

Tech Stack
- Language: TypeScript
- Tooling: Vite, ESBuild, npm scripts
- Rendering: HTML5 Canvas and optional WebGL for 2.5D visuals
- Input/Audio: Standard browser APIs (keyboard, mouse, pointer lock, AudioContext)
- Architecture: Lightweight ECS (entity, component, system), resource manager, event bus
- Editor UI: Code-oriented editors wired to JSON data models; file-based saves/loads

Phased Plan
Phase 1 - Planning & Scaffolding
- Produce master_plan.md and devplan.md (this document and the next)
- Define initial repo structure and coding conventions
- Outline ECS schema, data models for World, Map, Entities, Components
- Create skeleton directory layout and placeholder modules for engine, game, and editors
- Prepare initial build/dev documentation (BUILD.md, PLAY.md placeholders for Phase 2)

Phase 2 - Core Runtime & MVP Gameplay
- Implement ECS core (Entity, Component, System) scaffolding
- Implement basic rendering loop and a simple 2.5D camera (ray-like or faux-3D) and wall rendering on a grid map
- Player movement with WASD and mouselook, basic shooting
- Basic enemy with simple AI and collision handling
- Create grid-based level editor (level grid, tile editing, save/load for levels)
- Data schemas for monsters, weapons, assets (initial minimal set)
- Editor plumbing to edit JSON-driven definitions and export to files

Phase 3 - Editor Enhancements & Data-Driven Assets
- Implement code-driven editors for Monsters, Weapons, and Assets with UI panels
- Ensure in-editor validation and batch import/export of JSON definitions
- File-based save/load for all editor data (monsters, weapons, assets, levels)
- Improve rendering, AI, and combat balance

Phase 4 - Polish, UX, & Tooling
- Add lightweight UI polish, menus, and help screens
- Add basic audio cues (shooting, footsteps, enemy hit sounds)
- Optimize for performance; ensure cross-platform dev experience
- Add BUILD.md and PLAY.md with cross-platform instructions

Phase 5 - Packaging & Documentation
- Finalize dev dashboard (devplan.md + dashboard.md)
- Create a minimal release package and runnable examples for Windows/macOS/Linux
- Documentation for contributors and usage

Repository Structure (proposed)
- scratch/shared/            (planning artifacts, shared docs)
- scratch/shared/master_plan.md
- scratch/shared/devplan.md
- scratch/shared/src/
  - engine/                 (core ECS, renderer, input, resources)
  - game/                   (game loop, player, enemies, levels)
  - editor/levels/          (grid-based level editor, level data models)
  - editor/entities/        (monster/weapon/asset editors and data-driven UI)
  - assets/                   (textures, sprites, audio metadata)
- scratch/BUILD.md (to be populated in Phase 2)
- scratch/PLAY.md  (to be populated in Phase 2)

Notes
- All files under scratch/shared/ are visible to all agents in the swarm.
- Deliverables will be incrementally added as separate tasks per the ASAP workflow.
