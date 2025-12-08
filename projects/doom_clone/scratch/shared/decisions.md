## Key Decisions & Rationale

- 2025-12-07: Node.js was chosen as the canonical implementation path? Note: This is provisional pending Bossy's decision. If Node becomes canonical, we will enforce Bearer-based auth in the Node API and align tests accordingly. If not, we'll adjust contracts to reflect Rust or unified contract.
- 2025-12-07: Auth parity approach: placeholder Bearer for Node path; plan to move to a production-grade auth (JWT/OIDC) in aligned path.
- 2025-12-07: Cross-language contract alignment strategy: maintain a shared API contract document and a test harness that can validate both implementations against the same contract.
