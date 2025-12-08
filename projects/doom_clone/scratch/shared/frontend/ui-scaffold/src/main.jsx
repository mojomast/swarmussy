import './styles/global.css';

// The same lightweight UI scaffold is re-implemented in JSX for better integration

class UiButton extends HTMLElement {
  constructor() {
    super(); this.attachShadow({ mode: 'open' }); this.btn = document.createElement('button'); this.btn.setAttribute('class','ui-btn'); this.btn.addEventListener('click', e => this.dispatchEvent(new CustomEvent('press', { detail: { originalEvent: e }, bubbles: true })) ); const style = document.createElement('style'); style.textContent = `
      .ui-btn { padding: .5rem 1rem; border: none; border-radius: 6px; background: #4f46e5; color: white; cursor: pointer; }
      .ui-btn.secondary { background: #64748b; }
      .ui-btn.ghost { background: transparent; color: #374151; border: 1px solid #d1d5db; }
      .ui-btn:focus { outline: 2px solid #93c5fd; outline-offset: 2px; }
    `; this.shadowRoot.append(style, this.btn); }
  connectedCallback(){ const label = this.getAttribute('label') || this.textContent || 'Button'; this.btn.textContent = label; const variant = this.getAttribute('variant'); if (variant) this.btn.classList.add(variant); }
}

class UiCard extends HTMLElement { constructor(){ super(); this.attachShadow({mode:'open'}); const wrapper=document.createElement('div'); wrapper.className='card'; const style=document.createElement('style'); style.textContent=`
      .card { background:#fff; border-radius:12px; box-shadow:0 6px 20px rgba(0,0,0,.08); padding:1rem; margin:1rem; }
      :host { display: block; }
    `; wrapper.appendChild(document.createElement('slot')); this.shadowRoot.append(style, wrapper); } }

class GridEditor extends HTMLElement {
  constructor(){ super(); this.attachShadow({mode:'open'}); this.rows = parseInt(this.getAttribute('rows'))||8; this.cols = parseInt(this.getAttribute('cols'))||8; this.grid=new Set(); this.isPainting=false; const root=document.createElement('div'); root.className='grid-container'; this.root = root; const style=document.createElement('style'); style.textContent=`
      .grid { display:grid; grid-gap:4px; background:#e5e7eb; padding:6px; border-radius:8px; }
      .cell { background:#fff; border:1px solid #d1d5db; border-radius:4px; aspect-ratio:1/1; width:100%; cursor:pointer; }
      .cell.filled { background:#2563eb; border-color:#1e40af; }
      .cell.selected { box-shadow: inset 0 0 0 2px #111827; }
    `; this.shadowRoot.append(style, root); }
  connectedCallback(){ this.renderGrid(); this.root.addEventListener('mousedown', e=>{ if(e.target?.classList.contains('cell')){ this.isPainting=true; this.toggleCell(e.target.dataset.r, e.target.dataset.c); } }); window.addEventListener('mouseup', ()=>{ this.isPainting=false; }); this.root.addEventListener('mouseenter', ()=>{}, true); }
  static get observedAttributes(){ return ['rows','cols']; }
  attributeChangedCallback(n,o,nv){ if(n==='rows'||n==='cols'){ this.rows=parseInt(this.getAttribute('rows'))||8; this.cols=parseInt(this.getAttribute('cols'))||8; this.renderGrid(); } }
  renderGrid(){ this.root.innerHTML=''; const gridEl=document.createElement('div'); gridEl.className='grid'; gridEl.style.gridTemplateColumns = `repeat(${this.cols}, 1fr)`; for(let r=0;r<this.rows;r++){ for(let c=0;c<this.cols;c++){ const cell=document.createElement('button'); cell.type='button'; cell.className='cell'; cell.dataset.r=r; cell.dataset.c=c; if(this.grid.has(`${r},${c}`)) cell.classList.add('filled'); cell.addEventListener('click', (ev)=>{ ev.stopPropagation(); this.toggleCell(r,c); }); gridEl.appendChild(cell); } } this.root.appendChild(gridEl); }
  toggleCell(r,c){ const key=`${r},${c}`; if(this.grid.has(key)) this.grid.delete(key); else this.grid.add(key); const gridEl=this.root.querySelector('.grid'); if(gridEl){ const cell = gridEl.querySelector(`.cell[data-r=\"${r}\"][data-c=\"${c}\"]`); if(cell){ cell.classList.toggle('filled'); gridEl.querySelectorAll('.cell').forEach(el => el.classList.remove('selected')); cell.classList.add('selected'); } } AppBus.dispatchEvent(new CustomEvent('cellSelected', { detail: { r, c, filled: this.grid.has(key) } })); }
  getGrid(){ const arr=[]; for(let r=0;r<this.rows;r++){ const row=[]; for(let c=0;c<this.cols;c++){ row.push(this.grid.has(`${r},${c}`)); } arr.push(row); } return arr; }
}

class InEngineEditor extends HTMLElement {
  constructor(){ super(); this.attachShadow({mode:'open'}); const container=document.createElement('div'); container.className='engine-panel'; const style=document.createElement('style'); style.textContent=`
      .panel{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }
      .pane{ background:#fff; border-radius:8px; padding:12px; border:1px solid #e5e7eb; }
      h3{ margin:6px 0 12px; font-size:1rem; }
      .row{ display:flex; gap:8px; align-items:center; padding:6px 0; }
      .label{ width:80px; color:#374151; }
      .value{ font-family:monospace; color:#374151; }
    `; const panel=document.createElement('div'); panel.className='panel'; const inspector=document.createElement('div'); inspector.className='pane'; inspector.innerHTML=`<h3>Inspector</h3><div id="inspector">No cell selected</div>`; const properties=document.createElement('div'); properties.className='pane'; properties.innerHTML=`<h3>Properties</h3><div class="row"><span class="label">Row</span><span class="value" id="propRow">-</span></div><div class="row"><span class="label">Col</span><span class="value" id="propCol">-</span></div><div class="row"><span class="label">Filled</span><span class="value" id="propFilled">-</span></div>`; panel.append(inspector, properties); container.appendChild(panel); this.shadowRoot.append(style, container); this.inspectorEl=inspector; this.propRow=this.shadowRoot.querySelector('#propRow'); this.propCol=this.shadowRoot.querySelector('#propCol'); this.propFilled=this.shadowRoot.querySelector('#propFilled'); }
  connectedCallback(){ AppBus.addEventListener('cellSelected', (e)=>{ const {r,c,filled} = e.detail; this.updateInspector({r,c,filled}); }); }
  updateInspector({r,c,filled}){ this.inspectorEl.textContent = filled ? `Cell ${r},${c} filled` : `Cell ${r},${c} empty`; this.propRow.textContent = String(r); this.propCol.textContent = String(c); this.propFilled.textContent = filled ? 'Yes' : 'No'; }
}

function initAppShell(){ const root=document.querySelector('#root'); const style=document.createElement('style'); style.textContent=`
    :root{--bg:#f8f9fb;--card:#fff;--accent:#4f46e5;} *{box-sizing:border-box;} body{margin:0;font-family:system-ui,Arial;} header{position:sticky;top:0;z-index:10;background:#fff;border-bottom:1px solid #e5e7eb;} nav{display:flex;gap:8px;padding:12px 16px;align-items:center;} nav a{ text-decoration:none;color:#374151;padding:8px 12px;border-radius:6px;} nav a.active{ background:#eef2ff; color:#3730a3;} #content{ padding:16px; display:grid; grid-template-columns:1fr 1fr; gap:16px;} @media(max-width:900px){ #content{ grid-template-columns:1fr; } }
  `; const header=document.createElement('header'); const nav=document.createElement('nav'); const homeLink=document.createElement('a'); homeLink.href='#/'; homeLink.textContent='Home'; const gridLink=document.createElement('a'); gridLink.href='#/grid'; gridLink.textContent='Wireframe Grid'; const engineLink=document.createElement('a'); engineLink.href='#/engine'; engineLink.textContent='In-Engine Editor'; const usersLink=document.createElement('a'); usersLink.href='#/users'; usersLink.textContent='Users'; nav.append(homeLink, gridLink, engineLink, usersLink); header.appendChild(nav); root.appendChild(header); const content=document.createElement('div'); content.id='content'; root.appendChild(content); }

function renderHome(){ const content=document.getElementById('content'); content.innerHTML=''; const wireframe=document.createElement('div'); wireframe.style.display='block'; wireframe.style.padding='0'; wireframe.innerHTML='<h3>Wireframe Grid Editor</h3>'; const grid=document.createElement('grid-editor'); grid.setAttribute('rows','8'); grid.setAttribute('cols','8'); wireframe.appendChild(grid); const eng=document.createElement('div'); eng.style.display='block'; eng.style.padding='0'; eng.innerHTML='<h3>In-Engine Editor</h3>'; const engine=document.createElement('in-engine-editor'); eng.appendChild(engine); content.appendChild(wireframe); content.appendChild(eng); }

function renderGridRoute(){ const content=document.getElementById('content'); content.innerHTML=''; const wrap=document.createElement('div'); wrap.style.display='block'; wrap.style.padding='0'; wrap.innerHTML='<h2>Wireframe Grid Editor</h2>'; const grid=document.createElement('grid-editor'); grid.setAttribute('rows','10'); grid.setAttribute('cols','12'); wrap.appendChild(grid); content.appendChild(wrap); }

function renderEngineRoute(){ const content=document.getElementById('content'); content.innerHTML=''; const wrap=document.createElement('div'); wrap.style.display='block'; wrap.style.padding='0'; wrap.innerHTML='<h2>In-Engine Editor</h2>'; const engine=document.createElement('in-engine-editor'); wrap.appendChild(engine); content.appendChild(wrap); }

function renderUsersRoute(){ const content=document.getElementById('content'); content.innerHTML=''; const usersPanel=document.createElement('users-panel'); content.appendChild(usersPanel); }

function renderRoute(){ const path = location.hash.replace('#','') || '/'; const links=document.querySelectorAll('nav a'); links.forEach(a=>a.classList.remove('active')); if(path==='/grid') links[1].classList.add('active'); else if(path==='/engine') links[2].classList.add('active'); else if(path==='/users') links[3].classList.add('active'); else links[0].classList.add('active'); if(path==='/grid'){ renderGridRoute(); } else if(path==='/engine'){ renderEngineRoute(); } else if(path==='/users'){ renderUsersRoute(); } else { renderHome(); } }

document.addEventListener('DOMContentLoaded', ()=>{ initAppShell(); if(!customElements.get('ui-card')) customElements.define('ui-card', UiCard); if(!customElements.get('ui-button')) customElements.define('ui-button', UiButton); if(!customElements.get('grid-editor')) customElements.define('grid-editor', GridEditor); if(!customElements.get('in-engine-editor')) customElements.define('in-engine-editor', InEngineEditor); if(!customElements.get('users-panel')) customElements.define('users-panel', UsersPanel); renderRoute(); window.addEventListener('hashchange', renderRoute); });

// Users Panel integration (simplified)
class UsersPanel extends HTMLElement { constructor(){ super(); this.attachShadow({mode:'open'}); this.state={loading:false, error:null, users:[]}; this.render(); }
  connectedCallback(){ this.loadUsers(); const form = this.shadowRoot.querySelector('#userForm'); if(form){ form.addEventListener('submit', (e)=>{ e.preventDefault(); const name = this.shadowRoot.querySelector('#name').value.trim(); const email = this.shadowRoot.querySelector('#email').value.trim(); if(!name){ this.setError('Name is required.'); return; } if(!email || !/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email)){ this.setError('A valid email is required.'); return; } this.setError(null); this.createUser({name, email}); this.shadowRoot.querySelector('#name').value=''; this.shadowRoot.querySelector('#email').value=''; }); } }
  setLoading(flag){ this.state.loading = flag; this.render(); }
  setError(msg){ this.state.error = msg; this.render(); }
  async loadUsers(){ this.setLoading(true); try{ const res = await fetch('/users'); if(!res.ok){ throw new Error(`Failed to load users: ${res.status}`); } const data = await res.json(); this.state.users = data.users ?? []; this.setLoading(false); this.render(); } catch(err){ this.setLoading(false); this.setError(err?.message ?? 'Unknown error'); } }
  async createUser(payload){ try{ const res = await fetch('/users', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) }); if(!res.ok){ const errObj = await res.json().catch(()=>({message:'Server error'})); throw new Error(errObj?.message || `Request failed: ${res.status}`); } const user = (await res.json()).user ?? data; if(user){ this.state.users = [...this.state.users, user]; } this.render(); } catch(err){ this.setError(err?.message ?? 'Failed to create user'); } }
  render(){ const usersList = this.state.users.map(u => `<li>${u.name} &lt;${u.email}&gt;${u.id ? ` (id: ${u.id})`:''}</li>`).join(''); const status = this.state.loading ? '<div class="status">Loading...</div>' : ''; const errorHtml = this.state.error ? `<div class="error" role="alert" aria-live="assertive">${this.state.error}</div>` : ''; this.shadowRoot.innerHTML = ` <style> :host{ display:block; font-family: Arial, sans-serif; } .panel{ background:#fff; padding:12px; border-radius:8px; border:1px solid #e5e7eb; min-width: 320px; } h3{ margin:0 0 8px; font-size:1rem;} ul{ padding-left: 20px; margin: 8px 0; } .row{ display:flex; gap:8px; align-items:center; margin:6px 0; } input{ padding:6px; border:1px solid #ddd; border-radius:4px; } button{ padding:6px 12px; border-radius:4px; border:1px solid #ccc; background:#f3f4f6; cursor:pointer; } .error{ color:#b91c1c; background:#fee2e2; padding:6px; border-radius:4px; margin-top:6px; } .status{ color:#6b7280; margin-top:6px; font-size:0.9rem; } </style> <div class="panel" aria-label="users-panel"> <div> <h3>Users</h3> ${errorHtml} ${status} <ul>${usersList}</ul> </div> <form id="userForm" aria-label="Create user" style="display:flex; flex-direction:column; gap:8px; margin-left:12px;"> <div class="row"><label>Name</label><input id="name"/></div> <div class="row"><label>Email</label><input id="email" type="email"/></div> <div class="row" style="align-items:flex-end;"><button type="submit">Create User</button></div> </form> </div> `; const form = this.shadowRoot.querySelector('#userForm'); if (form){ form.addEventListener('submit', (e)=>{ e.preventDefault(); const name = this.shadowRoot.querySelector('#name').value.trim(); const email = this.shadowRoot.querySelector('#email').value.trim(); if(!name){ this.setError('Name required.'); return; } if(!email || !/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email)){ this.setError('Valid email required.'); return; } this.setError(null); this.createUser({name, email}); this.shadowRoot.querySelector('#name').value=''; this.shadowRoot.querySelector('#email').value=''; }); } }
}

customElements.define('users-panel', UsersPanel);
