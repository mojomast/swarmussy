# Doom Clone - Local Single-Player User Management Plan

Overview
- This plan implements a minimal, local-only user profile system for a single-player Doom clone. All data is stored in the browser's localStorage; no server or cloud integration is required.

Scope
- Frontend-only feature: create, load, save, and delete a single player profile on the device.
- Persisted data includes: name, avatar (emoji/color), current level, health, score, and a simple inventory snapshot.

Assumptions
- One profile per device.
- LocalStorage is available (no offline/edge-case fallback required for initial scope).
- No authentication, no networking.

Data model (contract)
- PlayerProfile:
  - name: string
  - avatar: string (emoji or color string)
  - level: number
  - health: number
  - score: number
  - inventory: string[] (or a simple array representation)
  - lastSaved: number (timestamp)

Storage strategy
- LocalStorage key: doomClone.profile
- Methods:
  - getProfile(): PlayerProfile | null
  - saveProfile(profile: PlayerProfile): void
  - loadProfile(): PlayerProfile | null
  - deleteProfile(): void

Files and functions
- scratch/shared/frontend/src/profile.js
  - Exports: getProfile(), saveProfile(profile), loadProfile(), deleteProfile()
- scratch/shared/frontend/src/ProfilePanel.jsx
  - React component: ProfilePanel
  - UI: name input, avatar selector (emoji/color), save button, load/delete controls
  - Validates name, provides accessible messages
- scratch/shared/frontend/src/doomBootstrapping.js (optional integration point)
  - Hooks into app startup to auto-load profile and hydrate game state

### Integration steps / missing pieces

- Bring `profile.js` in line with the full `PlayerProfile` contract:
  - Extend stored data to include `level`, `health`, `score`, `inventory`, and `lastSaved`.
  - Maintain backward compatibility with existing name/avatar-only profiles where possible.
- Implement `doomBootstrapping.js`:
  - On app startup, load the profile via `loadProfile()`.
  - If a profile exists, hydrate the Doom game state (player metadata and initial level/progress) from it.
  - Provide a clear extension point (for example, a `bootstrapProfile(gameApi)` function) that the main game loop can call.
- Wire `ProfilePanel.jsx` into the Doom Clone UI:
  - Expose a menu screen or panel for editing the local profile.
  - Ensure it uses the same `profile.js` contract and updates the game state after save/load/delete.

### Engine and core game integration (missing work)

- Align engine with `shared_models`:
  - Add a dependency from the `engine` crate to `shared_models`.
  - Use `Level`, `Weapon`, and `Monster` types (or compatible equivalents) as the canonical data model for runtime.
  - Define conversion helpers between any editor/export formats (e.g., JSON or grid exports) and `shared_models::Level`.
- Define a minimal game loop and level loading path:
  - Implement a simple game loop entrypoint in `engine/src/main.rs` (or via `desktop`) that can load a single level and run a basic simulation.
  - Load a level from a fixture (JSON or similar) that follows the `Level` contract, or from an in-memory demo level.
  - Expose a thin public API from `engine` for "load_level", "start", "stop" that other components can call.
- Connect editors/UI to the engine:
  - Choose a minimal contract for grid/editor output (e.g., a Level JSON schema matching `shared_models::Level`).
  - Ensure the grid/editor tools (React `ui-engine`/`ui-editor` or the Web Components scaffold) can export a level in that format.
  - Provide a path for the engine to consume that exported level on startup (file path, CLI arg, or IPC/HTTP in a later phase).
- End-to-end "Play" flow:
  - On app startup, run profile bootstrapping first (if available) to determine player metadata and last level.
  - Load the corresponding level into the engine and start the minimal game loop.
  - Ensure there is at least one CLI or desktop entrypoint that performs this sequence so a user can "press play" and run the Doom clone end-to-end.

Milestones
- Design complete: 1 day
- Implementation: 2-3 days
- QA: 1 day
- Documentation: 0.5 day

Risks & Mitigations
- Risk: LocalStorage blocked by user
  - Mitigation: Graceful fallback to in-memory storage (no persistence)
- Risk: Data loss on browser clear
  - Mitigation: Clear user aware prompts; provide export/import (future)

Plan owner
- Product/Architecture owner: Bossy McArchitect

"Plan ready" when you confirm the Go, I will kick off the Go-phase and assign tasks to the frontend dev to implement the local profile manager as described.