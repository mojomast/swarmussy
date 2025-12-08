Code Quality and Security Review Checklist for ECS Core, Level Editor, and Asset Editors

- Architecture:
  - Is ECS core decoupled from rendering and UI?
  - Are interfaces clearly defined for entities, components, and systems?
- Validation and Error Handling:
  - Are all public methods validating inputs and raising ECSValidationError on invalid data?
  - Is there a centralized error taxonomy and consistent error messages?
- Security:
  - Any chance of object injection via component data? Validate input types and limit allowable data shapes.
  - Are there any potential file I/O vulnerabilities (save/load) like path traversal? Tests cover safe paths.
- Data Persistence:
  - Is save_state/load_state deterministic and compatible across versions?
- Performance:
  - Is render_scene stable for large numbers of entities?
- Tests:
  - Do tests cover edge cases and negative scenarios?
  - Are tests self-contained and not relying on external resources?
- UI Editors:
  - Input sanitization for level names and asset references.
  - Ensure undo/redo pipelines are safe from data corruption.

Notes:
- Attach any findings and suggested mitigations in a separate PR description.
