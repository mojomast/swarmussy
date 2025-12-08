# API Contract, Editor API Integration & Schema Evolution

Table of Contents
- 1. API Contracts
- 2. API Surface Summary
- 3. Schema Evolution Guidelines
- 4. Persistence & Disk Load/Save
- 5. Auth Placeholders & Access Control
- 6. Error Handling & CORS
- 7. Testing Guidance & Test Matrix
- 8. Running & Dev Tips
- 9. Environment Variables
- 10. Cross-References


1) API Contracts

This repository defines the surface and internal schemas used by the editor, persistence, and engine components. The primary TypeScript contracts live in scratch/shared/api_contracts.ts and are consumed by the REST API in scratch/shared/server.ts.

- EditorState: the current editor snapshot including world state, entities, assets, and map metadata
- PlanState: the in-editor plan representation used by persistence
- AssetMeta, LevelMeta, EntityMeta, WorldState: metadata and state shapes for assets, levels, entities, and the world
- Payload types: EditorStatePayload, PlanStatePayload, AssetMetaPayload, LevelMetaPayload, EntityMetaPayload
- ApiResponse<T>: generic wrapper returned by all endpoints: { ok: boolean, data?: T, error?: string }

2) API Surface Summary

REST API surface (Express-based runtime in scratch/shared/server.ts):

- GET /api/editor/state -> returns current world/state JSON (editor, plan, assets, levels, map, timestamps)
- POST /api/editor/plan -> persists a plan JSON (payload: PlanStatePayload)
- GET /api/editor/assets, /api/editor/levels, /api/editor/entities -> list/fetch metadata
- POST /api/editor/assets -> create/update assets (AssetMetaPayload)
- POST /api/editor/entities -> create/update entities (EntityMetaPayload)
- POST /api/editor/levels -> create/update levels (LevelMetaPayload)
- GET /api/editor/health -> liveness
- GET /api/editor/version -> version

3) Schema Evolution Guidelines

Goal: evolve JSON schemas and API contracts without breaking existing clients. Follow these rules:

- Prefer additive changes over breaking changes. Add new optional fields rather than renaming/removing existing fields.
- When deprecating fields, mark them as deprecated in the payload and keep them for at least two minor releases, with clear migration notes.
- Use versioned top-level endpoints or versioned payload types if a breaking change is needed. Example: /api/editor/v2/state
- Introduce migration hooks on server startup to translate older payload shapes to the current in-memory model if needed.
- Maintain a stable wire format for ApiResponse<T> so existing clients that only inspect ok/data work without changes.
- Update api_contracts.ts to reflect changes and document in BUILD.md the rationale and deprecation plan.
- For persistence, ensure persisted files carry a small schema version stamp. On load, handle legacy versions with a compatibility shim if the on-disk format is older.
- Document schema changes in a CHANGELOG-like section within BUILD.md and in the dedicated API_PERSISTENCE_TESTS README.

4) Persistence & Disk Load/Save

- The runtime supports optional JSON persistence to disk via a configured path named PERSIST_PATH. When present, loadFromDisk/saveToDisk read/write state to disk.
- Persistence format: JSON representation of EditorState/PlanState and metadata blobs under a per-project directory. Atomic writes are used where supported.
- On startup, if a persisted state exists, the server loads it and exposes endpoints with the loaded state. If persistence is disabled, the server runs with in-memory defaults.
- When writing new state via POST requests, the in-memory representation is updated and then persisted to disk if PERSIST_PATH is configured.
- To migrate legacy files, a small adapter translates old field names to the new schema on load.

5) Auth Placeholders & Access Control

- All endpoints currently use permissive access in development; production should replace with proper authentication and authorization. Skip authentication in tests unless explicitly enabled.
- The codebase includes a placeholder middleware hook in server.ts for an auth strategy. Activate by wiring in your auth provider and toggling an ENABLE_AUTH flag.
- Cross-origin requests are allowed (see CORS below) to keep the UI functional in local/dev environments.

6) Error Handling & CORS

- All endpoints respond with a uniform envelope: { ok: boolean, data?: T, error?: string }.
- For frontend compatibility, CORS header Access-Control-Allow-Origin: * is included on every response.
- Validation errors return ok: false and a descriptive error string.

7) Testing Guidance & Test Matrix

Testing guidance focuses on API contracts, persistence semantics, and end-to-end behavior.

- TS contract tests: scratch/shared/tests/test_api_contracts.ts validates the shapes of EditorState, PlanState, AssetMeta, LevelMeta, WorldState, and the payload wrappers. It also validates JSON marshal/unmarshal semantics and ApiResponse wrapping.
- Python tests: existing tests validate JSON marshal/unmarshal for engine core and editor scaffolding within scratch/shared/tests.
- Persistence tests: ensure loadFromDisk/saveToDisk are exercised against a temporary directory, including concurrent writes and crash-safe behavior.
- End-to-end tests: exercise by hitting the Express endpoints against in-memory state and against a temporary disk-backed PERSIST_PATH, verifying ok/data semantics, error messages, and CORS headers.

Test Matrix (sample):
- Surface: state, plan, assets, levels, entities
- Persistence: in-memory, disk-persisted
- Auth: disabled (default), enabled (production-like)
- Payload validity: valid, invalid, missing fields, extra fields
- Concurrency: rapid alternation of updates

8) Running & Dev Tips

- npm install
- npm run dev (or equivalent) to start TS server per repository setup
- Access API at http://localhost:<port>/api/editor/state
- For persistence tests, set an environment variable PERSIST_PATH to a writable directory before starting the server.

9) Environment Variables

- PERSIST_PATH: filesystem path to persist state; if unset, persistence is disabled
- ENABLE_AUTH: if set to true, enable auth middleware (requires implementing a provider)
- SERVER_PORT: port on which the API server listens
- CORS_ORIGIN: optional origin for restricted CORS (overrides * if set)

10) Cross-References

- See scratch/shared/api_contracts.ts for TS interfaces
- See scratch/shared/server.ts for REST API implementation details
- See scratch/shared/README_API_PERSISTENCE_TESTS.md for testing guidance with persistence
- See scratch/shared/qa_api_persistence_plan.md for QA test planning

Notes
- This BUILD.md acts as a living document and should be updated with every breaking and non-breaking schema change. When schemas evolve, add entries to a CHANGELOG-like section and link to API persistence tests.
