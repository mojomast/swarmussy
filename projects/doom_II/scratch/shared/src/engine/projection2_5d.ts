// Minimal 2.5D projection (raycasting) using Canvas 2D
import type { World } from './world';
import type { Entity } from '../engine/ecs';

export interface Level2D {
  width: number;
  height: number;
  tiles: number[]; // 0 = empty, 1 = wall
}

// Simple raycasting render into the provided canvas context
export function renderRaycast2D(ctx: CanvasRenderingContext2D, level: Level2D, px: number, py: number, dir: number, fov: number, screenW: number, screenH: number, wallColor?: string): void {
  const cw = screenW;
  const ch = screenH;
  const color = wallColor ?? '#888';

  // background
  ctx.fillStyle = '#000';
  ctx.fillRect(0, 0, cw, ch);
  // floor/ceiling split
  const ceiling = ch * 0.4;
  ctx.fillStyle = '#222';
  ctx.fillRect(0, 0, cw, ceiling);
  ctx.fillStyle = '#555';
  ctx.fillRect(0, ceiling, cw, ch - ceiling);

  // Precompute ray step
  for (let x = 0; x < cw; x++) {
    // ray angle for this column
    const rayScreenX = (2 * x) / cw - 1; // -1 to 1
    const rayAngle = dir + Math.atan(rayScreenX * Math.tan(fov / 2));

    // ray direction as unit vector
    const rayDirX = Math.cos(rayAngle);
    const rayDirY = Math.sin(rayAngle);

    // current map square
    let mapX = Math.floor(px);
    let mapY = Math.floor(py);

    // length of ray from one side to next in map
    const deltaDistX = Math.abs(1 / (rayDirX || 1e-6));
    const deltaDistY = Math.abs(1 / (rayDirY || 1e-6));

    let sideDistX = 0;
    let sideDistY = 0;
    let stepX = 0;
    let stepY = 0;

    // calculate step and initial sideDist
    if (rayDirX < 0) {
      stepX = -1;
      sideDistX = (px - mapX) * deltaDistX;
    } else {
      stepX = 1;
      sideDistX = (mapX + 1.0 - px) * deltaDistX;
    }
    if (rayDirY < 0) {
      stepY = -1;
      sideDistY = (py - mapY) * deltaDistY;
    } else {
      stepY = 1;
      sideDistY = (mapY + 1.0 - py) * deltaDistY;
    }

    // perform DDA
    let hit = 0; // 0 = none, 1 = wall
    let side = 0;
    while (hit === 0) {
      if (sideDistX < sideDistY) {
        sideDistX += deltaDistX;
        mapX += stepX;
        side = 0;
      } else {
        sideDistY += deltaDistY;
        mapY += stepY;
        side = 1;
      }
      // bounds check
      if (mapX < 0 || mapX >= level.width || mapY < 0 || mapY >= level.height) {
        hit = 1;
        break;
      }
      const tile = level.tiles[mapY * level.width + mapX] || 0;
      if (tile > 0) hit = 1;
    }

    // distance to wall
    let perpWallDist: number;
    if (side === 0) {
      perpWallDist = (mapX - px + (1 - stepX) / 2) / (rayDirX || 1e-6);
    } else {
      perpWallDist = (mapY - py + (1 - stepY) / 2) / (rayDirY || 1e-6);
    }

    // prevent division by zero
    if (perpWallDist <= 0) perpWallDist = 0.0001;
    const lineHeight = Math.max(1, Math.floor(ch / perpWallDist));

    // draw vertical stripe
    const drawStart = Math.max(0, Math.floor((ch - lineHeight) / 2));
    const drawEnd = Math.min(ch - 1, Math.floor((ch + lineHeight) / 2));

    ctx.fillStyle = color;
    ctx.fillRect(x, drawStart, 1, Math.max(1, drawEnd - drawStart));
  }
}

// Convenience wrapper to render a test scene onto a canvas
export function renderTestScene(ctx: CanvasRenderingContext2D, level: Level2D, playerX: number, playerY: number, playerDir: number, fov: number, width: number, height: number) {
  renderRaycast2D(ctx, level, playerX, playerY, playerDir, fov, width, height);
}
