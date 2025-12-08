Cross-Language QA Parity Plan Proposal

Goal
- Extend QA plan to ensure parity between Node backend API tests and Rust contract tests (or other cross-language implementations).
- Update dashboards to reflect cross-language coverage and results.

Proposed tasks
- Bugsy McTester: Update QA plan to include 400/404/409 error coverage for /users endpoints; coordinate with Rust/Rust-contract tests; create scratch/shared/test_results_crosslang.md and scratch/shared/ci_crosslang.md.
- Codey McBackend: Expand tests to exercise 400/404/409, ensure error schemas match contract; export new cross-language contract hints.
- Pixel McFrontend: Align UI test expectations with cross-language error schemas and status codes; adjust any UI tests accordingly.
- Docy McWriter: Update dev plan dashboard references and cross-language status in docs; provide a cross-language FAQ snippet.

Deliverables
- scratch/shared/test_results_crosslang.md: structure for cross-language QA results; sections for Node tests, Rust tests, and a merged summary; sample entries provided as placeholders.
- scratch/shared/ci_crosslang.md: CI integration notes for running both Node and Rust tests in a single workflow; gating conditions and slide-in steps.

Acceptance criteria
- A clear plan is documented and accessible; cross-language test results are captured in a single place; CI harness updated to reflect cross-language runs.
