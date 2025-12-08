import { createCanvas } from './canvasEngine';

// Simple WASD + mouse look demo wiring

type Vec2 = { x: number; y: number };

class InputManager {
  keys: Record<string, boolean> = {};
  mouseDelta: Vec2 = { x: 0, y: 0 };
  locked: boolean = false;

  constructor() {
    window.addEventListener('keydown', (e) => { this.keys[e.key.toLowerCase()] = true; });
    window.addEventListener('keyup', (e) => { this.keys[e.key.toLowerCase()] = false; });
    // Pointer lock
    const onMouseMove = (e: MouseEvent) => {
      if (this.locked) {
        this.mouseDelta.x += e.movementX;
        this.mouseDelta.y += e.movementY;
      }
    };
    window.addEventListener('mousemove', onMouseMove);
  }

  lockPointer(canvas: HTMLCanvasElement) {
    canvas.requestPointerLock = canvas.requestPointerLock || (canvas as any).mozRequestPointerLock;
    canvas.requestPointerLock();
    this.locked = true;
  }

  resetMouseDelta() {
    this.mouseDelta.x = 0;
    this.mouseDelta.y = 0;
  }
}

function clamp(v: number, a: number, b: number) {
  return Math.max(a, Math.min(b, v));
}

function main() {
  const { canvas, ctx, resize } = createCanvas(0, 0, (document.getElementById('game') as HTMLElement));
  // Ensure canvas fills container
  resize();
  // UI wiring
  const input = new InputManager();
  const cam = { x: 0, y: 0, rot: 0, fov: Math.PI / 4 };

  // Simple render loop: clear, draw a grid and a center cross representing player
  const world = {
    w: 2000,
    h: 2000,
  };

  const lockBtn = document.getElementById('root');
  // On click canvas lock pointer
  canvas.addEventListener('click', () => input.lockPointer(canvas));

  const loop = () => {
    // movement
    const speed = 2;
    const dir = { x: 0, y: 0 };
    if (input.keys['w']) dir.y -= 1;
    if (input.keys['s']) dir.y += 1;
    if (input.keys['a']) dir.x -= 1;
    if (input.keys['d']) dir.x += 1;
    // normalize
    const mag = Math.hypot(dir.x, dir.y) || 1;
    cam.x += (dir.x / mag) * speed;
    cam.y += (dir.y / mag) * speed;
    cam.rot += input.mouseDelta.x * 0.01;
    input.resetMouseDelta();

    // simple render: clear canvas, draw grid relative to cam
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    // world to screen projection (simple top-down with rotation)
    ctx.save();
    ctx.translate(canvas.width / 2, canvas.height / 2);
    ctx.rotate(cam.rot);
    ctx.translate(-cam.x, -cam.y);

    // grid
    ctx.strokeStyle = '#e0e0e0';
    for (let x = -1000; x <= 1000; x += 100) {
      ctx.beginPath();
      ctx.moveTo(x, -1000);
      ctx.lineTo(x, 1000);
      ctx.stroke();
    }
    for (let y = -1000; y <= 1000; y += 100) {
      ctx.beginPath();
      ctx.moveTo(-1000, y);
      ctx.lineTo(1000, y);
      ctx.stroke();
    }

    // player
    ctx.fillStyle = '#f44336';
    ctx.fillRect(cam.x - 5, cam.y - 5, 10, 10);

    ctx.restore();

    requestAnimationFrame(loop);
  };

  loop();
}

document.addEventListener('DOMContentLoaded', main);
