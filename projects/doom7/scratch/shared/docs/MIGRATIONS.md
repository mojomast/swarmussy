# Migration Plan for JSON Contracts: Level, Entity, Asset

Objective
- Provide versioning, guidance, and safe, reversible migrations for Level, Entity, and Asset JSON contracts used by Editor and Engine persistence.

Versioning Conventions
- Use semantic versioning: MAJOR.MINOR.PATCH for each contract family.
- Each contract document carries:
  - schema_version: semantic version of the contract schema
  - data_version: semantic version of the payload data
- Future migrations may introduce wildcard patterns (e.g., 1.1.*) to describe patch-level changes across multiple entities.

Migration Lifecycle
- When a structural change is required, increment the schema_version for the affected contract and, if needed, bump data_version.
- Implement reversible migrations where possible. Maintain a UP/DOWN migration description in this document for traceability.
- Provide scripts or utilities to apply migrations to existing persisted JSON payloads and to rollback if necessary.

Migration Examples (illustrative; adapt to project tooling)

1) Level: add per-entity tags and provide 3D rotation support (non-breaking by using optional fields)
- UP: Introduce entities[].tags (array of strings) and ensure existing data defaults to [].
- DOWN: Remove entities[].tags if not present before; no schema changes needed to revert data_version if backward compatible.
- Schema versions: Level schema -> 1.1.0; data_version updated accordingly.

2) Entity: add optional components array to support custom behaviors
- UP: Add components (array) to Entity; default to [].
- DOWN: Remove components field from older data or keep but empty; treat as backward-compatible if schema allows missing field.
- Schema versions: Entity schema -> 1.1.0; data_version updated.

3) Asset: default dependencies to empty array when missing
- UP: Ensure dependencies exists; default [] when absent.
- DOWN: No action required if dependencies previously absent.
- Schema versions: Asset schema -> 1.1.0; data_version updated.

Wildcard migrations
- Use 1.1.* or 2.*.* in planning to indicate patch-level migrations that touch several contract families.
- When applying a wildcard migration, ensure all affected contracts are updated coherently and tests cover cross-consistency.

Testing and Validation
- Validate all migrated documents against the new schema using JSON Schema validators.
- Run editor/engine persistence integration tests to ensure load/save paths remain stable after migrations.

Rollback and Safety
- Maintain a changelog with migration steps and reversible paths.
- Provide a lightweight migration runner in the backend to apply UP migrations and log DOWN steps for rollback.
