# Event Contracts for Engine-Editor Interactions

This document defines the event contracts and data shapes used between the Editor UI and the Engine Core, along with versioning guidance and sample payloads.

## 1) Event contracts
- RenderFrameEvent: { deltaMs: number, frame?: number }
- ContractUpdatedEvent: { contractName: string, version?: string }

- EditorToEngine events: SaveWorldDescriptor, LoadWorldDescriptor, RequestPlay, Stop, Step
- EngineToEditor events: FrameRendered, ValidationError, Log, Status

## 2) World Descriptor contracts
- WorldDescriptor: top-level payload representing a full scene.
- EntityDescriptor: represents a world entity with components.
- ComponentDescriptor: generic payload with type discriminator and data payload.

- WorldDescriptor.schemaVersion: increment on structural changes
- Server-side validation to ensure component types exist and payloads are well-formed

## 3) Save/Load contracts
- Save contracts to JSON with keys: { contracts: [ ... events ... ] }
- Load validates required fields, warns on invalid contracts

## 4) Validation Rules
- Types must be serializable (no functions)
- All payloads should be plain JSON objects
- Unknown fields ignored gracefully

## 5) Sample payloads

- Example RenderFrameEvent payload (Editor to Engine)
```json
{ "event": "RenderFrameEvent", "deltaMs": 16, "frame": 42 }
```

- Example ContractUpdatedEvent payload
```json
{ "event": "ContractUpdatedEvent", "contractName": "WorldDescriptor", "version": "1.0" }
```

- Example WorldDescriptor (simplified)
```json
{
  "world_version": "1.0",
  "levelName": "Demo Level",
  "entities": [
    { "id": "e1", "name": "Player", "components": [ { "type": "Position", "data": { "x": 0, "y": 0, "z": 0 } } ] }
  ]
}
```

- Example Engine to Editor status payload
```json
{ "event": "Status", "message": "FrameRendered", "frame": 42 }
```

## 6) Versioning guidance
- Use semantic-like versioning for WorldDescriptor (e.g., 1.0, 1.1) and a separate schemaVersion for fields in objects
- Include a ContractUpdatedEvent when contracts change to trigger reloading or migration in clients

## 7) Next steps
- Expand payloads for more events like LoadWorldDescriptor, SaveWorldDescriptor, etc.
- Align with ARCH_PATTERNS.md event bus implementation
- Add tests and CI validation for payload schemas
