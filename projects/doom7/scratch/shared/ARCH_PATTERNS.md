# ARCH_PATTERNS

Concise architectural patterns guiding the in-engine editor UI integration.

1) UI Shell Pattern
- A modular, pluggable UI where each panel (Grid, Entities, Assets, Inspector) is a standalone module that communicates via a centralized EditorController.
- Supports keyboard navigation, ARIA roles, and responsive resizing.

2) Data Contracts
- UI and Engine exchange data through JSON-like contracts. The Level/Asset definitions are serialized to and from JSON for save/load.
- Validation occurs at the contract boundary to avoid runtime errors.

3) Editor Modules & Contracts
- Levels, Entities, and Assets live in dedicated modules with clear interfaces.
- Each module can be loaded/unloaded without breaking the overall UI.

4) Controller & Presenter Pattern
- A single EditorController maintains UI state (current tab, selected entity, current JSON). Views are presenters that render state.

5) Renderer Abstraction for Preview
- The in-editor preview (grid) uses a lightweight renderer interface that can be swapped to Canvas2D or WebGL. Start with Canvas2D and a toggle.

6) Accessibility & Internationalization
- ARIA labels, proper focus order, and keyboard shortcuts (e.g., arrow keys move selection, Ctrl+S saves).
- Design to accommodate i18n in the strings layer.

7) Integration Points
- Actions: save, load, export, import, reset. All actions flow through a contract layer and EditorController.

8) Testing & Quality
- UI state tests and snapshot-like tests for contract serialization are recommended.

9) ECS vs Components
- Summary: ECS (Entity-Component-System) is a data-oriented design where Entities are lightweight IDs, Components carry data, and Systems implement behavior. Classic component-based patterns combine data and behavior at the object level.
- When to use:
  - Large numbers of entities with sparse component sets.
  - Frequent runtime iteration over entities, where cache-friendly layouts improve performance.
  - Clear separation of data (components) from logic (systems).
- When NOT to use:
  - Small, highly interconnected object graphs with complex inter-object behavior.
  - Projects where team is less familiar with ECS, and a simpler OOP approach suffices.
- Hybrid guidance for this project:
  - Use an ECS-like data store for game world data (entities, components, systems).
  - Use a separate UI-facing model and contracts for the Editor to avoid leaking engine internals into the UI layer.
- Example sketch (conceptual):
  - EntityId = number
  - interface Component {}
  - interface World { entities: Map<EntityId, Map<string, Component>>; }
  - interface System { update(world: World, dt: number): void }

10) Event Bus
- Summary: In-process publish/subscribe mechanism to decouple event producers from consumers within the Editor and Engine.
- Design guidance:
  - Central EventBus with subscribe(eventType, handler) and publish(eventType, payload).
  - Use a small, strongly-typed event surface to minimize runtime errors (e.g., TypeScript discriminated unions if possible).
  - Scope: per-editor instance to avoid cross-process coupling; optionally support per-module buses for isolation.
- Common event types (examples):
  - LEVEL_LOADED, LEVEL_SAVED, LEVEL_CHANGED
  - ENTITY_SELECTED, ENTITY_UPDATED, COMPONENT_ADDED/REMOVED
  - RENDER_REQUEST, VIEWPORT_RESIZED
- Pros/Cons:
  - Pros: Loose coupling, easier testing, extensibility.
  - Cons: Potential for event avalanche if not rate-limited; debug complexity.

11) JSON Contracts
- Summary: Define stable JSON shapes for Level, Entities, and Assets to enable save/load, exchange between UI and engine, and future networked features.
- Design considerations:
  - Versioning: include contractVersion in the root; plan migrations when shapes change.
  - Validation: use JSON Schema or lightweight validators to enforce required fields and types at boundary points.
  - Serialization: deterministic ordering where possible to aid diffs and testing.
- Example contract shapes (conceptual, not exhaustive):
  - LevelContract: { "id": "level_01", "name": "Test Level", "grid": [[0,1,0],[1,0,1]], "assets": ["asset_01"] }
  - EntityContract: { "id": "e_1001", "type": "enemy", "components": { "Position": {"x": 5, "y": 10}, "Health": {"hp": 100} } }
  - AssetContract: { "id": "asset_01", "kind": "monster", "definition": { ... } }
- Validation & Migration:
  - Validate contracts at the boundary (UI <-> engine) to prevent runtime crashes.
  - Increment contract version and provide migration path for older saved data.

12) Data Flow Diagrams
- Editor UI data flow (ASCII):

  UI_Panels -> EditorController -> JSON_Contract (Level/Entity/Asset) -> Storage (Save/Load) -> Engine (World State via World Contract)
  
  [UI_Panels]  [EditorController]  [Contracts/JSON]  [Storage]
     |              |                       |               |
     v              v                       v               v
  User actions -> state changes          serialize/deserialize   Engine consumes via World contracts

- ECS-driven world data flow (ASCII):

  World_State (Entities + Components) -> Systems -> Render -> Editor View (snapshot of world) -> UI actions -> World_State

- Notes:
  - Keep editor contracts isolated from engine internals; expose read-only world snapshots for UI rendering where possible.
  - Use the EventBus to propagate significant changes (e.g., Level changed) without tight coupling.
