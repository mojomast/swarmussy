import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { getWorldBridge, WorldState } from '../../../ecs_bridge';

export type LevelDefinition = {
  id: string;
  name: string;
  grid: number[][]; // 0 = empty, 1 = wall
};

export type LevelEditorProps = {
  level?: LevelDefinition;
  onSave?: (level: LevelDefinition) => void;
};

/**
 * LevelEditor
 * A Level Editor wired to a tiny ECS World bridge.
 * - Grid cells are 34px square.
 * - Click to toggle a cell between empty (0) and wall (1).
 * - Dragging with mouse pressed paints walls (1) or clears (0).
 * - Save emits a LevelDefinition JSON via onSave.
 */
const LevelEditor: React.FC<LevelEditorProps> = ({ level, onSave }) => {
  // Seed grid: dynamic size based on provided level or default 10x10
  const initialGrid = useMemo(() => {
    if (level?.grid) {
      return level.grid.map((row) => row.slice());
    }
    const size = 10;
    return Array.from({ length: size }, () => Array.from({ length: size }, () => 0));
  }, [level?.grid]);

  const [grid, setGrid] = useState<number[][]>(initialGrid);
  const [dragging, setDragging] = useState<boolean>(false);
  const [paintMode, setPaintMode] = useState<number>(1); // 1 = paint wall, 0 = erase
  const [history, setHistory] = useState<number[][][]>([]);
  const [future, setFuture] = useState<number[][][]>([]);

  const bridge = getWorldBridge();

  // Initialize and subscribe to bridge state
  useEffect(() => {
    // If a seed level is provided, seed the bridge grid
    if (level?.grid) {
      level.grid.forEach((row, r) => {
        row.forEach((val, c) => bridge.setTile(c, r, val));
      });
      // Also align local grid to provided level grid size
      setGrid(level.grid.map((row) => row.slice()));
    } else {
      // Without seed level, sync from bridge state
      const init = bridge.getState();
      setGrid(init.grid);
    }
    // Sync from bridge updates
    const unsubscribe = bridge.onUpdate((state: WorldState) => {
      setGrid(state.grid);
    });
    return () => unsubscribe();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const rows = grid.length;
  const cols = grid[0]?.length ?? 0;

  // Update bridge when editing grid
  const toggleCell = useCallback((r: number, c: number, mode?: number) => {
    setGrid((g) => {
      const next = g.map((row) => row.slice());
      const value = mode != null ? mode : (next[r][c] === 0 ? 1 : 0);
      // Push current grid to history for undo
      setHistory((hist) => [...hist, g.map((row) => row.slice())]);
      // Clear redo history on new edit
      setFuture([]);
      next[r][c] = value;
      bridge.setTile(c, r, value);
      return next;
    });
  }, [bridge]);

  const handleMouseDown = (r: number, c: number) => {
    setDragging(true);
    const current = grid[r][c];
    const mode = current === 0 ? 1 : 0;
    setPaintMode(mode);
    toggleCell(r, c, mode);
  };

  const handleMouseEnter = (r: number, c: number) => {
    if (!dragging) return;
    toggleCell(r, c, paintMode);
  };

  const handleMouseUp = () => setDragging(false);

  const onSaveClick = () => {
    const levelOut: LevelDefinition = {
      id: level?.id ?? 'level-1',
      name: level?.name ?? 'Untitled Level',
      grid: grid,
    };
    onSave?.(levelOut);
  };

  const undo = () => {
    if (history.length === 0) return;
    const prev = history[history.length - 1];
    // Save current state to future for redo
    setFuture((f) => [...f, grid.map((row) => row.slice())]);
    // Revert to previous
    setGrid(prev);
    setHistory((h) => h.slice(0, -1));
  };

  const redo = () => {
    if (future.length === 0) return;
    const next = future[future.length - 1];
    // Save current state to history
    setHistory((h) => [...h, grid.map((row) => row.slice())]);
    setGrid(next);
    setFuture((f) => f.slice(0, -1));
  };

  const handleKeyDown = (r: number, c: number) => (e: React.KeyboardEvent<HTMLButtonElement>) => {
    if (e.key === 'ArrowRight') {
      if (c + 1 < cols) {
        const el = document.querySelector(`[data-cell=\"${r}-${c + 1}\"]`) as HTMLElement | null;
        el?.focus();
      }
      e.preventDefault();
    } else if (e.key === 'ArrowLeft') {
      if (c - 1 >= 0) {
        const el = document.querySelector(`[data-cell=\"${r}-${c - 1}\"]`) as HTMLElement | null;
        el?.focus();
      }
      e.preventDefault();
    } else if (e.key === 'ArrowDown') {
      if (r + 1 < rows) {
        const el = document.querySelector(`[data-cell=\"${r + 1}-${c}\"]`) as HTMLElement | null;
        el?.focus();
      }
      e.preventDefault();
    } else if (e.key === 'ArrowUp') {
      if (r - 1 >= 0) {
        const el = document.querySelector(`[data-cell=\"${r - 1}-${c}\"]`) as HTMLElement | null;
        el?.focus();
      }
      e.preventDefault();
    }
  };

  const renderCell = (r: number, c: number) => {
    const isWall = grid[r][c] === 1;
    const bg = isWall ? '#2b2f4f' : '#e8eefc';
    return (
      <button
        key={`${r}-${c}`}
        data-testid={`cell-${r}-${c}`}
        data-cell={`${r}-${c}`}
        onMouseDown={() => handleMouseDown(r, c)}
        onMouseEnter={() => handleMouseEnter(r, c)}
        onMouseUp={handleMouseUp}
        onKeyDown={handleKeyDown(r, c)}
        aria-label={`cell ${r}-${c} ${isWall ? 'wall' : 'empty'}`}
        role="gridcell"
        style={{
          width: 34,
          height: 34,
          background: bg,
          border: '1px solid #cbd5e1',
          padding: 0,
          cursor: 'pointer',
        }}
      />
    );
  };

  return (
    <div
      className="level-editor"
      aria-label="Level editor grid"
      role="grid"
      style={{ display: 'grid', gap: 4, gridTemplateColumns: `repeat(${cols}, 34px)` }}
    >
      {grid.map((row, r) =>
        row.map((_, c) => renderCell(r, c))
      )}

      <div style={{ gridColumn: `span ${cols}`, display: 'flex', gap: 8 }}>
        <button onClick={undo} aria-label="Undo" style={{ padding: '6px 10px' }}>
          Undo
        </button>
        <button onClick={redo} aria-label="Redo" style={{ padding: '6px 10px' }}>
          Redo
        </button>
        <button onClick={onSaveClick} aria-label="Save level" style={{ marginLeft: 'auto', padding: '6px 10px' }}>
          Save Level
        </button>
      </div>
    </div>
  );
};

export type { LevelDefinition, LevelEditorProps };
export default LevelEditor;
