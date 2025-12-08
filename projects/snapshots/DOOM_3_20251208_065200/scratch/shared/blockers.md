## Active Blockers
- ⚠️ API contract drift: LevelData payload schema lock pending Bossy approval. Until locked, risk typing drift between frontend and backend.
- ⚠️ Auth strategy: Need decision on toggleable auth middleware for tests and production parity.
- ⚠️ Router interface: Finalize Express-like Router shape and middleware semantics; dependency on Bossy's direction.
- ⚠️ Engine integration risk: Integrating the engine with the in-memory world may require coordination across teams (Codey McBackend vs. Pixel McFrontend).

## Requested Support
- Bossy: Lock payload contracts for LevelData (load/save) to prevent drift.
- Architect: Decide on the router interface and auth middleware plan (toggle).
- Engine team: Confirm server/world integration assumptions and timeline for engine tick hooks.

