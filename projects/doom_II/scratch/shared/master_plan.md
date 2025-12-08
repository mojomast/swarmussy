Doom 2.5D FPS - Minimal ECS-based Engine with In-Engine Editors

Overview
- Build a minimal Doom-style 2.5D FPS (WASD + mouse look) with shooting, simple enemies, using a TypeScript codebase, Vite + ESBuild tooling, and Canvas/WebGL rendering without a heavyweight engine.
- Include in-engine grid-based level editor and simple editors for monsters, weapons, and asset metadata. Save/load as a single repo structure.

Project Structure (proposed)
- scratch/shared/ (planning/docs and shared artifacts)
- scratch/shared/src/engine/ (core ECS, game loop, rendering hooks)
- scratch/shared/src/game/ (game entities, components, assets, save/load)
- scratch/shared/src/editor/levels/ (level editor logic and data formats)
- scratch/shared/src/editor/entities/ (entity editor tooling for stats/behaviors)
- scratch/shared/assets/ (sprite/texture metadata and assets placeholders)
- scratch/shared/data/ (level data and save files)
- scratch/shared/ui/ (UI scaffolding for editors)
- scratch/ (private scratch files per agent during planning)

Architecture Highlights
- ECS-style architecture: Entity, Component, System, World
- Rendering via HTML5 Canvas (2.5D projection) with optional WebGL for partial acceleration
- Input handling via standard browser APIs (keyboard, mouse lock, pointer events)
- Simple audio via Web Audio API
- Editors:
  - Level editor (grid-based) with save/load
  - Entity editor for monster stats/behaviors
  - Weapon editor for parameters (damage, range, fire rate, ammo usage)
- Tooling:
  - Vite + ESBuild for TS build, dev server, and production bundling
  - npm scripts for dev/build/test

File List (high level)
- scratch/shared/master_plan.md (this document)
- scratch/shared/devplan.md (live project dashboard)
- scratch/shared/src/engine/ (ecs.ts, world.ts, system.ts)
- scratch/shared/src/game/ (components.ts, entities.ts, assets.ts, save.ts, level.ts)
- scratch/shared/src/editor/ (levels/, entities/)
- scratch/shared/data/ (levels.json, monsters.json, weapons.json, etc.)
- scratch/shared/ui/ (editor UI scaffolding)

Milestones (high level)
- Phase 1: Core ECS and rendering loop skeleton
- Phase 2: Player controls, basic weapons, and enemies
- Phase 3: Level editor and entity/asset editors
- Phase 4: Saving/loading, data formats, and UI polish
- Phase 5: QA, packaging, and cross-platform build

Risks & Mitigations
- Risk: Real-time rendering in Canvas is tricky; Mitigation: start with a 2.5D raycast-like projection on 2D canvas and progressively optimize
- Risk: Editor data formats evolving; Mitigation: design clear JSON schemas and versioned save files

Team Roles
- backend_dev (Codey McBackend): core game logic and data models
- frontend_dev (Pixel McFrontend): UI, canvas rendering, input, and UX
- qa_engineer (Bugsy McTester): testing, QA plans, and code reviews
- devops (Deployo McOps): tooling, builds, CI/CD pipelines
- project_manager (Checky McManager): progress tracking and milestones
- tech_writer (Docy McWriter): docs and user guides

Milestone Tracking & Delivery
- We will track progress in scratch/shared/devplan.md and update after each task.