Code Review Checklist for Browser Game Code

1) Architecture and coherence
- Does the code follow project conventions and naming standards?
- Are modules small, focused, and well-scoped?
- Is there a clear separation of concerns between ECS, rendering, and editors?
- Are public APIs documented (JSDoc/TS types where applicable)?

2) Correctness and edge cases
- Are there unit tests for core logic and edge cases (missing components, empty inputs)?
- Do integration tests cover typical user flows and potential failure states?
- Are deterministic behaviors guaranteed where necessary (frame steps, system ordering)?

3) Test coverage and quality
- Is test coverage sufficient for ECS lifecycle, rendering loop stability, and editor workflows?
- Are tests fast, deterministic, and flaky-free?
- Do tests validate both positive and negative paths?
- Are tests self-contained with no reliance on external services unless mocked safely?

4) Security considerations (OWASP-aligned)
- Input validation and sanitization for user-provided data.
- Avoid eval/dynamic code execution; prefer safe alternatives.
- Prevent XSS in UI; sanitize outputs that render user content.
- Secure storage and data handling on the client (avoid leaking sensitive data).
- Dependency management: lockfile integrity, up-to-date libraries.
- Error handling: avoid exposing internal error traces to users.
- Telemetry/logging: avoid collecting sensitive data without consent.

5) Performance and scalability
- Identify hot paths; ensure no obvious N+1 or unnecessary allocations in hot loops.
- Tests should not regress performance; consider lightweight benchmarks if applicable.

6) Security review notes
- Document any known vulnerabilities or risk areas and mitigations.
- Review feature flags and access control for editor features.

7) Documentation and deliverables
- Ensure TEST_PLAN.md exists and is up-to-date.
- Ensure README and contributor docs reflect current testing strategy.

8) Compliance and policy
- Confirm no sensitive data is committed to repo.
- Verify licensing of dependencies.
