Phase 2 Testing Matrix

Overview:
- Stable, regression, and exploratory tests for Phase 2 features.

Matrix:
- Feature A: Engine core loop
  - Happy Path: correct execution of fixed-timestep loop
  - Edge: timestep drift handling
  - Error: invalid inputs
- Feature B: Runtime data collection
  - Happy: data emitted on events
  - Edge: missing fields
  - Error: corrupted payloads
