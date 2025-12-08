Architectural Patterns for Engine-Editor Integration

- Event Bus: In-process, typed publish/subscribe with one-to-many listeners. Events must be serializable for future network transport.
- Data Contracts: WorldDescriptor, EntityDescriptor, and ComponentDescriptor saved/loaded via JSON; validation rules ensure forward/backward compatibility.
- Contract Updated: Editor and Engine coordinate on ContractUpdated events to refresh bindings and dashboards.
- MVP integration: EditorController emits ContractUpdated when contracts change; Engine subscribes to listen and react.
- Security/Observability: Basic logging for events, metrics counters for event rate.
