// Lightweight UI module for HUD overlay (vanilla TS)

export function createHUD(container: HTMLElement) {
  const hud = document.createElement('div');
  hud.className = 'hud';
  // Ensure overlay area visually distinct but unobtrusive
  hud.style.display = 'flex';
  hud.style.gap = '16px';
  hud.style.alignItems = 'center';
  hud.style.padding = '6px 10px';
  hud.style.borderRadius = '6px';
  hud.style.background = 'rgba(0,0,0,0.45)';
  hud.style.color = '#fff';

  const posEl = document.createElement('div');
  posEl.textContent = 'Position: 0, 0';
  hud.appendChild(posEl);

  const fpsEl = document.createElement('div');
  fpsEl.textContent = 'FPS: 0';
  hud.appendChild(fpsEl);

  container.style.display = 'flex';
  container.style.alignItems = 'center';
  container.style.justifyContent = 'flex-start';
  container.style.minHeight = '32px';
  container.style.gap = '8px';
  container.appendChild(hud);

  let last = performance.now();
  let frames = 0;
  let fps = 0;
  const tick = () => {
    frames++;
    const now = performance.now();
    if (now - last >= 500) {
      fps = Math.round((frames * 1000) / (now - last));
      fpsEl.textContent = 'FPS: ' + fps;
      last = now;
      frames = 0;
    }
    requestAnimationFrame(tick);
  };
  tick();

  return {
    setPosition: (x: number, y: number) => {
      posEl.textContent = `Position: ${Math.round(x)}, ${Math.round(y)}`;
    },
  };
}

export default { createHUD };
