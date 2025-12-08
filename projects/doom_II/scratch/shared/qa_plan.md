QA Plan for Editor Data Schemas and Engine API

Scope
- Validate JSON Schemas for Level, Monster, Weapon, Asset (server-side validation included)
- Validate editor data persistence (save/load) for levels using in-memory store (Node-friendly)
- Validate basic engine API shapes (exported editor and engine stubs)

Test Strategy
- Unit tests for validateJson against Level schema (valid/invalid)
- Integration tests for saveLevel/loadLevel flow using in-memory store
- Edge-case tests for input handling (unknown properties, missing required, wrong types)
- Security considerations: input sanitization stubs to prevent prototype pollution and path traversal in paths and IDs

Test Artifacts
- shared/schemas/*.schema.json (Level, Monster, Weapon, Asset)
- shared/src/validate.js (lightweight validator)
- shared/src/editor.js (in-memory persistence, API surface)
- shared/tests/validation.test.js (unit tests for validateJson)
- shared/tests/persistence.test.js (integration tests for save/load)
- shared/tests/run_all_tests.js (test harness)

Exit Criteria
- All tests pass locally in Node environment
- No critical security vulnerabilities detected in input handling
- Validation coverage: level schema + nested properties, arrays, and required fields
