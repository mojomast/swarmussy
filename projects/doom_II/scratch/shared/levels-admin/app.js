// Minimal app wiring for Levels Admin

document.addEventListener('DOMContentLoaded', () => {
  const btnCreate = document.getElementById('btn-create');
  btnCreate?.addEventListener('click', () => {
    openLevelModal('create');
  });

  renderList();
});

async function renderList(){
  const tableBody = document.querySelector('#levels-table tbody');
  const loading = document.getElementById('levels-loading');
  const errorEl = document.getElementById('levels-error');
  loading.hidden = false; errorEl.hidden = true;
  tableBody.innerHTML = '';
  try {
    const levels = await window.__levels_api__.fetchLevels();
    if (!levels || levels.length === 0) {
      document.getElementById('levels-empty').hidden = false;
      return;
    } else { document.getElementById('levels-empty').hidden = true; }
    levels.forEach(l => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${l.name}</td><td>${l.difficulty}</td><td>${l.duration}</td><td><button class="btn btn-secondary" data-id="${l.id}">Open</button></td>`;
      tableBody.appendChild(tr);
    });
  } catch (e) {
    errorEl.textContent = 'Failed to load levels.'; errorEl.hidden = false;
  } finally { loading.hidden = true; }

  // Attach click for Open buttons
  document.querySelectorAll('#levels-table tbody button[data-id]').forEach(btn => {
    btn.addEventListener('click', async (ev) => {
      const id = ev.currentTarget.getAttribute('data-id');
      // fetch and show detail
      openLevelDetail(id);
    });
  });
}

async function openLevelDetail(id){
  // simple fetch by id
  try {
    const levels = await window.__levels_api__.fetchLevels();
    const level = levels.find(l => l.id == id);
    if (!level) return;
    const detailEl = document.getElementById('detail-content');
    detailEl.innerHTML = `<strong>${level.name}</strong><br/>Difficulty: ${level.difficulty}<br/>Duration: ${level.duration} min`;
    document.getElementById('detail-actions').hidden = false;
    document.getElementById('btn-detail-edit').onclick = () => openLevelModal('edit', level);
  } catch (e){ /* ignore for now */ }
}

function openLevelModal(mode, level){
  // Modal HTML scaffold
  const modalRoot = document.getElementById('modal-container');
  modalRoot.innerHTML = `
    <div class="modal-backdrop" style="position: fixed; inset: 0; background: rgba(0,0,0,.5); display:flex; align-items:center; justify-content:center;" aria-label="Level modal">
      <div class="modal-card" style="background:#141a2a; padding:20px; border-radius:12px; width: 420px; max-width: 90%; color: white;">
        <h3>${mode === 'create' ? 'Create Level' : 'Edit Level'}</h3>
        <form id="level-form">
          <label>Name</label><input id="level-name" class="input" style="width:100%;" /><br/>
          <label>Difficulty</label><select id="level-difficulty" style="width:100%;"><option>Easy</option><option>Medium</option><option>Hard</option></select><br/>
          <label>Duration (min)</label><input id="level-duration" type="number" min="1" style="width:100%;" /><br/>
          <div id="form-errors" class="error" role="alert" hidden></div>
          <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:12px;">
            <button type="button" id="level-cancel" class="btn btn-secondary">Cancel</button>
            <button type="submit" class="btn btn-primary">${mode === 'create' ? 'Create' : 'Save'}</button>
          </div>
        </form>
      </div>
    </div>`;
  // prefill if edit
  if (level){
    document.getElementById('level-name').value = level.name;
    document.getElementById('level-difficulty').value = level.difficulty;
    document.getElementById('level-duration').value = level.duration;
  }

  modalRoot.style.display = 'block';

  // form handling
  const form = document.getElementById('level-form');
  form.onsubmit = async (e) => {
    e.preventDefault();
    const payload = {
      name: document.getElementById('level-name').value,
      difficulty: document.getElementById('level-difficulty').value,
      duration: Number(document.getElementById('level-duration').value)
    };
    // client-side basic validation aligned with server rules
    const errors = [];
    if (!payload.name) errors.push('Name is required.');
    if (!payload.duration || payload.duration <= 0) errors.push('Duration must be a positive number.');
    if (errors.length){
      const errEl = document.getElementById('form-errors'); errEl.textContent = errors.join(' '); errEl.hidden = false; return;
    }

    try {
      if (mode === 'create'){
        await window.__levels_api__.createLevel(payload);
      } else if (level?.id){
        await window.__levels_api__.updateLevel(level.id, payload);
      }
      modalRoot.innerHTML = ''; modalRoot.style.display = 'none';
      await renderList();
      // refresh detail to reflect changes
      if (level?.id){ openLevelDetail(level.id); }
    } catch (err){
      const errEl = document.getElementById('form-errors'); errEl.textContent = err?.message || 'Failed to save.'; errEl.hidden = false;
    }
  };

  document.getElementById('level-cancel').onclick = () => {
    modalRoot.innerHTML = ''; modalRoot.style.display = 'none';
  };
}
