// Minimal Level Editor UI that polls Engine-like provider and hooks to a mock world

class MockEngineProvider {
  constructor() {
    this.engine = null;
  }
  async ensureEngine() {
    if (!this.engine) {
      // lazy-load a lightweight engine from the shared shim
      const mod = await import('./engineShim.js');
      this.engine = new mod.EngineShim();
    }
    return this.engine;
  }
  async start() {
    const e = await this.ensureEngine();
    await e.start();
  }
  async stop() {
    const e = await this.ensureEngine();
    await e.stop();
  }
  async tick() {
    const e = await this.ensureEngine();
    return await e.tick();
  }
  getState() {
    // return a synthetic state if engine not yet created
    if (!this.engine) return { started: false, tick: 0 };
    return this.engine.getState();
  }
}

// Engine Status widget: renders state and periodically polls since it's a mock provider
class EngineStatusWidget {
  constructor(container, provider) {
    this.container = container;
    this.provider = provider;
    this.root = document.createElement('div');
    this.root.className = 'engine-status-widget';
    this.root.style = 'padding:8px; border-radius:8px; background: rgba(0,0,0,.25);';
    this.title = document.createElement('div');
    this.title.style.fontWeight = '700';
    this.title.style.marginBottom = '6px';
    this.title.textContent = 'Engine Status';
    this.statusLine = document.createElement('div');
    this.statusLine.style.display = 'flex';
    this.statusLine.style.justifyContent = 'space-between';
    this.statusLine.style.padding = '4px 0';
    this.statusValue = document.createElement('span');
    this.statusValue.textContent = 'idle';
    const sLabel = document.createElement('span');
    sLabel.textContent = 'Status:';
    sLabel.style.color = '#a0b7d8';
    this.statusLine.appendChild(sLabel);
    const statusVal = document.createElement('span');
    statusVal.style.fontWeight = '600';
    statusVal.style.color = '#e6f2ff';
    statusVal.id = 'engineStatusValue';
    statusVal.textContent = 'idle';
    this.statusLine.appendChild(statusVal);

    // tick info
    this.tickLine = document.createElement('div');
    this.tickLine.style.display = 'flex';
    this.tickLine.style.justifyContent = 'space-between';
    this.tickLine.style.padding = '4px 0';
    const tLabel = document.createElement('span');
    tLabel.textContent = 'Tick:';
    tLabel.style.color = '#a0b7d8';
    this.tickVal = document.createElement('span');
    this.tickVal.style.fontWeight = '600';
    this.tickVal.style.color = '#e6f2ff';
    this.tickVal.id = 'engineTickValue';
    this.tickVal.textContent = '0';
    this.tickLine.appendChild(tLabel);
    this.tickLine.appendChild(this.tickVal);

    // delta line
    this.dtLine = document.createElement('div');
    this.dtLine.style.display = 'flex';
    this.dtLine.style.justifyContent = 'space-between';
    this.dtLine.style.padding = '4px 0';
    const dLabel = document.createElement('span');
    dLabel.textContent = 'Delta (ms):';
    dLabel.style.color = '#a0b7d8';
    this.dtVal = document.createElement('span');
    this.dtVal.style.fontWeight = '600';
    this.dtVal.style.color = '#e6f2ff';
    this.dtVal.id = 'engineDtValue';
    this.dtVal.textContent = '0';
    this.dtLine.appendChild(dLabel);
    this.dtLine.appendChild(this.dtVal);

    // container
    this.root.appendChild(this.title);
    this.root.appendChild(this.statusLine);
    this.root.appendChild(this.tickLine);
    this.root.appendChild(this.dtLine);

    this.container.appendChild(this.root);

    // update loop
    this._polling = true;
    this._interval = setInterval(() => this.refresh(), 400);
  }

  async refresh() {
    const state = this.provider.getState();
    const statusEl = document.getElementById('engineStatusValue');
    const tickEl = document.getElementById('engineTickValue');
    const dtEl = document.getElementById('engineDtValue');
    if (statusEl) statusEl.textContent = state.started ? 'running' : 'idle';
    if (tickEl) tickEl.textContent = String(state.tick ?? 0);
    if (dtEl) dtEl.textContent = String(((state.tick ?? 0) * 16) & 0xFFFF);
    // world hook: if world exists, advance a tick position
    if (this.onWorldTick) this.onWorldTick(state.tick ?? 0);
  }

  destroy() {
    clearInterval(this._interval);
    this.container.removeChild(this.root);
  }
}

class WorldView {
  constructor(container) {
    this.container = container;
    this.gridSize = 16; // 16x16 grid
    this.cells = [];
    this.activeIndex = -1;
    this._initGrid();
  }
  _initGrid() {
    // ensure 16x16 cells exist as simple divs
    this.container.innerHTML = '';
    const frag = document.createDocumentFragment();
    for (let i = 0; i < this.gridSize * this.gridSize; i++) {
      const cell = document.createElement('div');
      cell.className = 'world-cell';
      cell.style.width = '100%';
      cell.style.height = '60px';
      cell.style.background = 'rgba(255,255,255,.04)';
      cell.style.borderRadius = '4px';
      frag.appendChild(cell);
      this.cells.push(cell);
    }
    this.container.style.display = 'grid';
    this.container.style.gridTemplateColumns = `repeat(${this.gridSize}, 1fr)`;
    this.container.style.gridAutoRows = '60px';
    this.container.style.gap = '4px';
    this.container.appendChild(frag);
  }
  _setActive(index) {
    if (this.activeIndex >= 0 && this.cells[this.activeIndex]) {
      this.cells[this.activeIndex].style.background = 'rgba(255,255,255,.04)';
    }
    this.activeIndex = index;
    if (this.activeIndex >= 0 && this.cells[this.activeIndex]) {
      this.cells[this.activeIndex].style.background = 'rgba(123, 211, 137, 0.9)';
    }
  }
  setActiveByCoords(x, y) {
    const idx = y * this.gridSize + x;
    this._setActive(idx);
  }
  tick(index) {
    // optional, highlight a new cell on tick
    const idx = index % (this.gridSize * this.gridSize);
    this._setActive(idx);
  }
}

// Exports for debugging in the module environment (not essential for browser)
export { MockEngineProvider, EngineStatusWidget, WorldView };

// Bootstrap when the document is ready
document.addEventListener('DOMContentLoaded', async () => {
  // world grid visuals
  const worldGrid = document.getElementById('worldGrid');
  const worldView = new WorldView(worldGrid);

  // create provider and UI widgets
  const provider = new MockEngineProvider();
  const container = document.getElementById('engineStatus');
  const statusWidget = new EngineStatusWidget(container, provider);

  // connect world tick to engine tick for a simple visual hook
  let tickCounter = 0;
  statusWidget.onWorldTick = (tick) => {
    // progress world grid with tick
    tickCounter = tick;
    worldView.tick(tickCounter);
  };

  // Bind HUD buttons to provider with status refresh
  const startBtn = document.getElementById('startBtn');
  const stopBtn = document.getElementById('stopBtn');
  const tickBtn = document.getElementById('tickBtn');

  startBtn?.addEventListener('click', async () => {
    await provider.start();
    await statusWidget.refresh();
  });
  stopBtn?.addEventListener('click', async () => {
    await provider.stop();
    await statusWidget.refresh();
  });
  tickBtn?.addEventListener('click', async () => {
    const t = await provider.tick();
    await statusWidget.refresh();
    // also move world on explicit tick
    worldView.tick(t.tick);
  });

  // initial render
  await statusWidget.refresh();
});
