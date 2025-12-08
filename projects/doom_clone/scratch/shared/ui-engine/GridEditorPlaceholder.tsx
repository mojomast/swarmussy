import React from 'react';
import type { TileType } from '../types/EngineTypes';

export type GridEditorPlaceholderProps = {
  rows: number;
  cols: number;
  value?: TileType[][];
  onCellClick?: (r: number, c: number) => void;
};

// A lightweight, interactive placeholder grid editor used for in-engine planning.
// Visuals are intentionally minimal and stylized to convey layout without business logic.
const GridEditorPlaceholder: React.FC<GridEditorPlaceholderProps> = ({ rows, cols, value, onCellClick }) => {
  // Build a flat grid to render as a CSS grid
  const cells = Array.from({ length: rows * cols }, (_, idx) => {
    const r = Math.floor(idx / cols);
    const c = idx % cols;
    const val = value?.[r]?.[c] ?? 'empty';
    return { r, c, val };
  });

  const cellStyle: React.CSSProperties = {
    width: 28,
    height: 28,
    border: '1px solid #7a7a7a',
    borderRadius: 4,
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#f4f4f4',
    cursor: 'pointer',
    fontSize: 12,
    lineHeight: 1,
    padding: 0,
  };

  return (
    <div
      className="grid-editor-placeholder"
      aria-label="in-engine grid editor placeholder"
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${cols}, 28px)`,
        gap: 6,
        padding: 8,
        background: '#fff',
        border: '1px solid #e5e5e5',
        borderRadius: 8,
      }}
    >
      {cells.map(({ r, c, val }) => (
        <button
          key={`${r}-${c}`}
          aria-label={`grid cell ${r},${c}`}
          onClick={() => onCellClick?.(r, c)}
          style={cellStyle}
        >
          {val === 'empty' ? '' : String(val).charAt(0).toUpperCase()}
        </button>
      ))}
    </div>
  );
};

export { GridEditorPlaceholder };
export default GridEditorPlaceholder;
