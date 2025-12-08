## Decisions Log
- 2025-12-08: Adopt a simple in-memory API-backed persistence surface with JSON dump support for world/editor state. Plan to evolve to a small Express server with in-memory store for MVP.
- 2025-12-08: Use JSON payload shapes defined in shared/api_contracts.ts for frontend-backend parity; implement aliases in /api endpoints to avoid breaking existing UI during migration.
