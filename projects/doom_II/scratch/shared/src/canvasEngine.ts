// Canvas engine utilities for the demo

export interface CanvasBundle {
  canvas: HTMLCanvasElement;
  ctx: CanvasRenderingContext2D;
  resize: () => void;
}

/** Create and configure a canvas element, attach to an optional parent, and handle high-DPI sizing. */
export function createCanvas(width: number = 800, height: number = 600, parent?: HTMLElement): CanvasBundle {
  const canvas = document.createElement('canvas');
  canvas.id = 'gameCanvas';
  canvas.style.width = '100%';
  canvas.style.height = '100%';
  canvas.style.display = 'block';
  // Ensure accessibility
  canvas.setAttribute('aria-label', 'Game Canvas');
  if (parent) {
    parent.appendChild(canvas);
  } else {
    document.body.appendChild(canvas);
  }

  const ctx = canvas.getContext('2d')!;

  // Resize handler to support high-DPI canvases
  const resize = () => {
    const dpr = Math.max(window.devicePixelRatio || 1, 1);
    const w = window.innerWidth;
    const h = window.innerHeight;
    canvas.style.width = w + 'px';
    canvas.style.height = h + 'px';
    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  };

  // Initial size
  resize();

  // Bind to resize events
  window.addEventListener('resize', resize);

  return { canvas, ctx, resize };
}

export default { createCanvas };
