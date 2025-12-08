LEVELS API (PUT /levels/:id) - design and usage

Overview
- This API manages an in-memory store of Level objects used by the QA and UI layers.
- The PUT /levels/:id endpoint updates an existing level.
- Payload validation mirrors the POST rules, ensuring server-side consistency.

Data model (Level)
- id: string
- name: string
- dimensions: { width: number, height: number, depth: number }
- tiles: string[]
- monsters: string[]
- weapons: string[]
- assets: string[]
- spawn_points: [{ x: number, y: number, z: number }]
- version: string (pattern: digits.digits.digits, e.g. 1.0.0)
- createdAt?: string (read-only, server side)

PUT /levels/:id
- Path: /levels/:id
- Method: PUT
- Authentication: Bearer token (expects testtoken in QA tests). We reject requests with missing/invalid Authorization header.
- Payload requirements:
  - Must be a JSON object matching the Level schema.
  - The payload must include id, and payload.id must equal the URL id.
  - All required fields must be present:
    - id (string)
    - name (string)
    - dimensions (object with width/height/depth numbers)
    - tiles (array of strings)
    - monsters (array of strings)
    - weapons (array of strings)
    - assets (array of strings)
    - spawn_points (array of { x, y, z as numbers })
    - version (string matching x.y.z pattern)
- Behavior:
  - If the level with the given id does not exist, respond with 404 { error: 'Level not found' }.
  - If the payload is invalid, respond with 400 and a JSON body { errors: [...] } describing validation failures.
  - If valid and exists, update stored level fields (name, dimensions, tiles, monsters, weapons, assets, spawn_points, version) while preserving createdAt and id, and respond 200 with the updated level object.

Response examples
- Success (204 is not used for PUT in this implementation; 200 with updated data):
  {
    "id": "lvl-01",
    "name": "Updated Level",
    "dimensions": { "width": 10, "height": 10, "depth": 1 },
    "tiles": ["tile1"],
    "monsters": ["goblin"],
    "weapons": ["sword"],
    "assets": ["asset"],
    "spawn_points": [{ "x": 0, "y": 0, "z": 0 }],
    "version": "1.1.0",
    "createdAt": "<original_created_at>"
  }

Error responses
- 400: Payload id must match URL id or other schema validation errors
- 404: Level not found
- 401: Unauthorized (missing/invalid token)

Notes
- The in-memory store is reset between tests/instances using resetLevelsStore().
- This endpoint is designed for unit tests and QA; a production API would replace in-memory with a persistent DB.
