Wireframe plan: in-engine grid editor and editors

1. Grid Editor Shell (GridEditorShell.tsx)
- Layout: header bar with title and status, main content area containing GridEditorPlaceholder.
- GridEditorPlaceholder renders a scalable grid via CSS grid with n x m cells.
- Cell interaction: onCellClick hook to be wired to patch editing state.
- Visuals: light borders, rounded cells, compact sizing for planning screen.

2. Grid Grid Placeholder (GridEditorPlaceholder.tsx)
- Props: rows, cols, value grid (TileType[][]), onCellClick.
- Render: grid with cells sized 28x28, gaps 6px, simple color scheme.
- States: 'empty' cells render empty, others render first letter of type.

3. Editor Panels (WeaponEditorPlaceholder.tsx, MonsterEditorPlaceholder.tsx)
- Simple panels showing current item data and stats.
- Layout: small bordered cards suitable for stacking in a side panel.
- Data contracts defined in EngineTypes.ts: Weapon { id,name,damage,range }, Monster { id,name,hp,attack }.

4. Data Contracts (EngineTypes.ts)
- TileType union with 'empty' | 'wall' | 'floor' | 'water' | string for extensibility.
- GridCell, Weapon, Monster definitions.

5. Wire-up plan (future work)
- Connect GridEditorPlaceholder to a Grid editing API via GridEditorShell or a controller hook.
- Expose WeaponEditorPlaceholder and MonsterEditorPlaceholder in a left rail panel with selection and detail views.
- Add keyboard accessibility and ARIA labels for navigation.
