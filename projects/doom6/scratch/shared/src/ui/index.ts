// Vanilla UI shell bootstrapper for the editor canvas (no React)
export type UIHandlers = {
  onPlay?: () => void;
  onStop?: () => void;
  onSave?: () => void;
  onLoad?: () => void;
  onEdit?: () => void;
};

let _engineStatusListeners: Array<(running: boolean) => void> = [];

export const setEngineStatusForUI = (running: boolean) => {
  for (const cb of _engineStatusListeners) { try { cb(running); } catch { } }
  const el = document.getElementById('engine-status');
  if (el) el.textContent = `Engine: ${running ? 'Running' : 'Stopped'}`;
};

export const onEngineStatusChange = (cb: (running: boolean) => void) => {
  _engineStatusListeners.push(cb);
};

export const setEngineStatusBadge = (running: boolean) => {
  const el = document.getElementById('engine-status');
  if (el) el.textContent = `Engine: ${running ? 'Running' : 'Stopped'}`;
};

export const initUI = (mount: HTMLElement, handlers: Partial<UIHandlers> = {}) => {
  mount.innerHTML = '';
  mount.style.display = 'grid';
  mount.style.gridTemplateColumns = '260px 1fr';
  mount.style.height = '100%';
  mount.style.width = '100%';

  const sidebar = document.createElement('aside');
  sidebar.style.padding = '12px';
  sidebar.style.background = '#0f142a';

  const title = document.createElement('div');
  title.textContent = 'Menu';
  title.style.fontWeight = '700';
  title.style.fontSize = '14px';
  title.style.textTransform = 'uppercase';
  title.style.letterSpacing = '.5px';
  title.style.color = '#a2a9d4';
  title.style.marginBottom = '8px';
  sidebar.appendChild(title);

  const statusBadge = document.createElement('div');
  statusBadge.id = 'engine-status';
  statusBadge.style.fontSize = '12px';
  statusBadge.style.color = '#a2a9d4';
  statusBadge.textContent = 'Engine: Stopped';
  statusBadge.style.marginTop = '6px';
  statusBadge.style.marginBottom = '8px';
  sidebar.appendChild(statusBadge);

  const makePanel = (children) => {
    const p = document.createElement('div');
    p.style.background = '#1a2142';
    p.style.borderRadius = '8px';
    p.style.padding = '8px';
    p.style.marginBottom = '8px';
    children.forEach((c) => p.appendChild(c));
    return p;
  };

  const btnPlay = document.createElement('button'); btnPlay.className = 'btn'; btnPlay.textContent = 'Play'; btnPlay.addEventListener('click', () => handlers.onPlay?.());
  const btnStop = document.createElement('button'); btnStop.className = 'btn'; btnStop.textContent = 'Stop'; btnStop.style.marginLeft = '6px'; btnStop.addEventListener('click', () => handlers.onStop?.());
  const panel1 = makePanel([btnPlay, btnStop]);

  const btnSave = document.createElement('button'); btnSave.className = 'btn'; btnSave.textContent = 'Save'; btnSave.addEventListener('click', () => handlers.onSave?.());
  const btnLoad = document.createElement('button'); btnLoad.className = 'btn'; btnLoad.textContent = 'Load'; btnLoad.style.marginLeft = '6px'; btnLoad.addEventListener('click', () => handlers.onLoad?.());
  const panel2 = makePanel([btnSave, btnLoad]);

  const btnEdit = document.createElement('button'); btnEdit.className = 'btn'; btnEdit.textContent = 'Edit Mode'; btnEdit.addEventListener('click', () => handlers.onEdit?.());
  const panel3 = makePanel([btnEdit]);

  sidebar.appendChild(panel1);
  sidebar.appendChild(panel2);
  sidebar.appendChild(panel3);

  const main = document.createElement('main'); main.style.height = '100%';
  const canvasHost = document.createElement('div'); canvasHost.style.height = '100%';
  const render = document.createElement('canvas'); render.id = 'renderSurface'; render.width = 800; render.height = 600; render.setAttribute('aria-label', 'render-canvas'); render.style.width = '100%'; render.style.height = '100%';
  canvasHost.appendChild(render); main.appendChild(canvasHost);

  mount.appendChild(sidebar); mount.appendChild(main);

  const ctx = render.getContext('2d'); if (ctx) { let t=0; const loop = ()=>{ t+=0.016; ctx.clearRect(0,0,render.width,render.height); const cell=32; ctx.strokeStyle='#22324e'; for(let x=0;x<render.width;x+=cell){ ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,render.height); ctx.stroke(); } for(let y=0;y<render.height;y+=cell){ ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(render.width,y); ctx.stroke(); } const cx=(Math.sin(t)*0.5+0.5)*render.width; const cy=(Math.cos(t)*0.5+0.5)*render.height; ctx.fillStyle='#6be675'; ctx.beginPath(); ctx.arc(cx,cy,6,0,Math.PI*2); ctx.fill(); requestAnimationFrame(loop); }; loop(); }

  return { canvas: render };
};

export default { initUI };
