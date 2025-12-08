// Concrete RaycastRenderer: a placeholder 2.5D raycasting renderer scaffold
// Implements a simple DDA-based raycaster over a grid map.

import { MapGrid, Player } from './types';
import { Renderer } from './renderer';

export class RaycastRenderer implements Renderer {
  private map: MapGrid | null = null;
  private player: Player | null = null;
  private width: number = 320;
  private height: number = 200;

  // Optional: allow configuring resolution
  public configure(resolution?: { width?: number; height?: number }) {
    if (resolution?.width) this.width = resolution.width;
    if (resolution?.height) this.height = resolution.height;
  }

  public init(map: MapGrid, player: Player): void {
    this.map = map;
    this.player = player;
  }

  public renderFrame(): number[] {
    // Basic sanity checks
    if (!this.map || !this.player) {
      // return a blank frame
      return new Array(this.width * this.height).fill(0);
    }

    const frame: number[] = new Array(this.width * this.height);

    const map = this.map;
    const px = this.player.pos.x;
    const py = this.player.pos.y;
    const dirX = this.player.dir.x;
    const dirY = this.player.dir.y;
    const planeX = this.player.plane.x;
    const planeY = this.player.plane.y;

    for (let x = 0; x < this.width; x++) {
      // cameraX ranges from -1 to 1
      const cameraX = 2 * x / this.width - 1;
      const rayDirX = dirX + planeX * cameraX;
      const rayDirY = dirY + planeY * cameraX;

      // Which map square are we in?
      let mapX = Math.floor(px);
      let mapY = Math.floor(py);

      // Length of ray from current position to next x/y side
      const deltaDistX = rayDirX === 0 ? Number.POSITIVE_INFINITY : Math.abs(1 / rayDirX);
      const deltaDistY = rayDirY === 0 ? Number.POSITIVE_INFINITY : Math.abs(1 / rayDirY);

      let stepX = 0;
      let stepY = 0;
      let sideDistX = 0;
      let sideDistY = 0;

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

      let hit = 0; // wall hit
      let side = 0; // 0 for x, 1 for y

      // DDA loop
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
        if (mapX < 0 || mapX >= map.length || mapY < 0 || mapY >= (map[0]?.length ?? 0)) {
          hit = 1; // treat outside map as hit to end the loop
          break;
        }
        if (map[mapX][mapY] > 0) {
          hit = 1;
        }
      }

      // Calculate distance to the wall
      let perpWallDist = 0;
      if (side === 0) {
        perpWallDist = (mapX - px + (1 - stepX) / 2) / rayDirX;
      } else {
        perpWallDist = (mapY - py + (1 - stepY) / 2) / rayDirY;
      }
      if (!isFinite(perpWallDist) || perpWallDist <= 0) perpWallDist = 0.0001;

      // Simple shading based on distance
      // The further the wall, the darker the shade
      let shade = Math.floor(255 - Math.min(254, perpWallDist * 128));
      if (shade < 0) shade = 0;
      if (shade > 255) shade = 255;

      // Fill the entire column with this shade as a simple placeholder for vertical wall slice
      for (let y = 0; y < this.height; y++) {
        frame[y * this.width + x] = shade;
      }
    }

    return frame;
  }
}
