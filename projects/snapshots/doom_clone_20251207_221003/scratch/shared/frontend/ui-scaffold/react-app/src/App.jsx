import React from 'react';

export default function App() {
  const [grid, setGrid] = React.useState({ rows: 8, cols: 8, cells: {} });
  const toggle = (r, c) => {
    const key = `${r},${c}`;
    setGrid((g) => {
      const next = { ...g, cells: { ...g.cells, [key]: !g.cells[key] } };
      return next;
    });
  };
  return (
    <div className="app-shell">
      <h2>Grid Editor (React)</h2>
      <div className="grid" style={{ gridTemplateColumns: `repeat(${grid.cols}, 1fr)` }}>
        {Array.from({ length: grid.rows }).map((_, r) => (
          Array.from({ length: grid.cols }).map((_, c) => {
            const key = `${r},${c}`; const filled = !!grid.cells[key];
            return (
              <button key={key} className={`cell ${filled ? 'filled' : ''}`} onMouseDown={() => toggle(r,c)} aria-label={`cell ${r} ${c} ${filled ? 'filled':'empty'}`} />
            );
          })
        ))}
      </div>
    </div>
  );
}
