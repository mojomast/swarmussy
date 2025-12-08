export let onTick: ((dt: number) => void) | null = null;
let isRunning = false;
let rafId: number | null = null;
let lastTime = 0;

export function startTickLoop(): void {
  if (isRunning) return;
  isRunning = true;
  lastTime = performance.now();
  const loop = (t: number) => {
    const dt = Math.max(0, (t - lastTime) / 1000);
    lastTime = t;
    if (onTick) onTick(dt);
    if (isRunning) rafId = requestAnimationFrame(loop);
  };
  rafId = requestAnimationFrame(loop);
}

export function stopTickLoop(): void {
  if (!isRunning) return;
  isRunning = false;
  if (rafId != null) cancelAnimationFrame(rafId);
  rafId = null;
}

export function isTickRunning(): boolean {
  return isRunning;
}
