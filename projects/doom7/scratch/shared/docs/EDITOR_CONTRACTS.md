# Editor Contracts and Data Flow

This document defines the JSON contracts used by the in-engine editor shell to communicate with the engine core. It covers load, edit, save, and asset/entity operations.

Table of contents
- Overview
- Data contracts (examples)
- Editor-to-engine messages
- Engine-to-editor responses
- Validation and error handling
- Versioning and compatibility
- Troubleshooting

## Overview
The Editor contracts are designed to be lightweight JSON payloads that can be sent over a messaging channel (IM or REST) between the Editor UI and the engine core. They describe the data shapes for levels, entities, assets, and edits.

## Data contracts (examples)

- Load level
```
{
  "action": "load_level",
  "level_id": "level-01"
}
```

- Save level
```
{
  "action": "save_level",
  "level_id": "level-01",
  "data": {
    "name": "Test Level",
    "entities": [ {"id": "e1", "type": "player", "pos": {"x": 1, "y": 2} } ]
  }
}
```

- Update entity
```
{
  "action": "update_entity",
  "entity_id": "e1",
  "updates": {"pos": {"x": 2, "y": 3}}
}
```

## Editor-to-engine messages
- load_level, save_level, update_entity, delete_entity, asset_upload

## Engine-to-editor responses
- level_loaded, level_saved, entity_updated, error

## Validation and error handling
- Unknown action returns error payload with code and message.

## Versioning and compatibility
- Contracts include a version field to allow iterator upgrades.

## Troubleshooting
- If messages are not received, verify IPC channel or REST endpoint is wired correctly.
