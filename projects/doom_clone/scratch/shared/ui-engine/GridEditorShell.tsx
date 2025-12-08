import React from 'react';
import { GridEditorPlaceholder } from './GridEditorPlaceholder';
import type { TileType } from '../types/EngineTypes';

export type GridEditorShellProps = {
  rows: number;
  cols: number;
  value?: TileType[][];
  onCellClick?: (r: number, c: number) => void;
};

// Shell wrapper for the in-engine grid editor. Integrates placeholder grid with layout chrome.
const GridEditorShell: React.FC<GridEditorShellProps> = ({ rows, cols, value, onCellClick }) => {
  return (
    <section aria-label="grid-editor-shell" style={{ padding: 16 }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <h2 style={{ fontSize: 18, margin: 0 }}>In-Engine Grid Editor (Wireframe)</h2>
        <div style={{ fontSize: 12, color: '#666' }}>Rows: {rows} • Cols: {cols}</div>
      </header>
      <GridEditorPlaceholder rows={rows} cols={cols} value={value} onCellClick={onCellClick} />
    </section>
  );
};

export { GridEditorShell };
export default GridEditorShell;
