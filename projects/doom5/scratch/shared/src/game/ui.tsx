import React from 'react';

export type WorldEntity = {
  id?: string;
  x: number;
  y: number;
  w?: number;
  h?: number;
  color?: string;
};

export type WorldLike = {
  grid?: number[][];
  entities?: WorldEntity[];
};

export type GamePreviewProps = {
  width?: number;
  height?: number;
  world?: WorldLike;
};

/**
 * GamePreview
 * Lightweight ECS-friendly render surface. Renders a backdrop, optional grid, and simple entities.
 */
const GamePreview: React.FC<GamePreviewProps> = ({ width = 320, height = 200, world }) => {
  const cellsX = world?.grid?.[0]?.length ?? 10;
  const cellsY = world?.grid?.length ?? 6;
  const cellSize = Math.floor(Math.min(width / cellsX, height / cellsY));

  return (
    <section aria-label="Game preview" style={{ border: '1px solid #e2e8f0', borderRadius: 6, padding: 8 }}>
      <canvas
        width={width}
        height={height}
        aria-label="World preview canvas"
        role="img"
        style={{ width: '100%', height: 'auto', display: 'block' }}
      />
      {/* Simple overlay rendering via inline DOM for accessibility; actual rendering would be via canvas in a real app. */}
      <div
        aria-hidden
        style={{ position: 'relative', top: -height, width: '100%', height: 0 }}
      >
        {/* Placeholder to indicate entities in a production app you would draw on the canvas */}
        {world?.entities?.length ? (
          <ul aria-label="entities list" style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {world.entities.map((e) => (
              <li key={e.id ?? Math.random()}>
                {e.id ?? 'entity'} at ({e.x},{e.y})
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </section>
  );
};

export default GamePreview;
export type { WorldLike, WorldEntity, GamePreviewProps };
