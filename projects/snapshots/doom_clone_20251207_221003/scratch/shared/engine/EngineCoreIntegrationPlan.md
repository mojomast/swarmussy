# EngineCore Integration Plan

- Bridge EngineCore with app shell and backend contract for profile CRUD flows.
- Provide test scaffolding for engine-core integration: unit tests and integration harness that simulate doom-bootstrap-profile events and doom-core-profile-updated emissions.
- Define event contracts between app shell and EngineCore:
  - Incoming: doom-bootstrap-profile (profile payload)
  - Outgoing: doom-core-profile-updated (profile payload)
