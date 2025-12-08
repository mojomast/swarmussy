// Levels Admin UI - lives under /levels API. List, detail, and create/edit modal with validation.

(function(){
  const API_BASE = '/levels';

  // DOM refs
  const btnNew = document.getElementById('btnNew');
  const levelsTableBody = document.querySelector('#levelsTable tbody');
  const emptyState = document.getElementById('emptyState');
  const detailPanel = document.getElementById('detailPanel');
  const detailContent = document.getElementById('detailContent');
  const btnEditDetail = document.getElementById('btnEdit');
  const btnDeleteDetail = document.getElementById('btnDelete');

  // Modal
  const modalBackdrop = document.getElementById('modalBackdrop');
  const modal = modalBackdrop; // wrapper
  const modalTitle = document.getElementById('modalTitle');
  const levelName = document.getElementById('levelName');
  const levelDesc = document.getElementById('levelDesc');
  const levelDiff = document.getElementById('levelDiff');
  const levelForm = document.getElementById('levelForm');
  const modalClose = document.getElementById('modalClose');
  const modalCancel = document.getElementById('modalCancel');
  const modalSave = document.getElementById('modalSave');
  const formError = document.getElementById('errForm') || document.getElementById('formError') || document.getElementById('formError');
  
  // State
  let levels = [];
  let editingId = null; // null means creating new
  let selectedId = null; // current detail

  function escapeHtml(s){ return String(s ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function renderTable(){
    levelsTableBody.innerHTML = '';
    if (!levels || levels.length === 0){
      emptyState.hidden = false;
      detailContent.textContent = 'Select a level to view details.';
      btnEditDetail.disabled = true;
      btnDeleteDetail.disabled = true;
      return;
    }
    emptyState.hidden = true;
    for (const lv of levels){
      const tr = document.createElement('tr');
      tr.dataset.id = String(lv.id);
      tr.innerHTML = `
        <td>${escapeHtml(lv.id)}</td>
        <td>${escapeHtml(lv.name)}</td>
        <td>${escapeHtml(lv.difficulty)}</td>
        <td>${escapeHtml(lv.description ?? '')}</td>
        <td><button class="btn editRow" data-id="${lv.id}">Edit</button></td>`;
      levelsTableBody.appendChild(tr);
    }
    // wire row interactions
    levelsTableBody.querySelectorAll('tr').forEach(tr => {
      tr.addEventListener('click', ()=>{
        const id = tr.dataset.id;
        const lv = levels.find(x => String(x.id) === String(id));
        if (lv) setDetail(lv);
      });
      const editBtn = tr.querySelector('.editRow');
      if (editBtn){ editBtn.addEventListener('click', (e)=>{ e.stopPropagation(); openModalForEdit(editBtn.dataset.id); }); }
    });
  }

  function setDetail(lv){
    if (!lv){ selectedId = null; detailContent.textContent = 'Select a level to view details.'; btnEditDetail.disabled = true; btnDeleteDetail.disabled = true; return; }
    selectedId = lv.id;
    detailContent.innerHTML = `ID: ${escapeHtml(lv.id)}<br/>Name: ${escapeHtml(lv.name)}<br/>Description: ${escapeHtml(lv.description ?? '')}<br/>Difficulty: ${escapeHtml(lv.difficulty)}`;
    btnEditDetail.disabled = false;
    btnDeleteDetail.disabled = false;
  }

  function openModalForNew(){
    editingId = null;
    modalTitle.textContent = 'New Level';
    levelName.value = '';
    levelDesc.value = '';
    levelDiff.value = '';
    formError && (formError.textContent = '');
    modalBackdrop.style.display = 'flex';
  }

  function openModalForEdit(id){
    const lv = levels.find(x => String(x.id) === String(id));
    if (!lv) return;
    editingId = lv.id;
    modalTitle.textContent = 'Edit Level';
    levelName.value = lv.name ?? '';
    levelDesc.value = lv.description ?? '';
    levelDiff.value = lv.difficulty ?? '';
    formError && (formError.textContent = '');
    modalBackdrop.style.display = 'flex';
  }

  function closeModal(){ modalBackdrop.style.display = 'none'; }

  function validateForm(){
    if (!levelName.value.trim()){
      if (formError) formError.textContent = 'Name is required';
      return false;
    }
    if (!levelDiff.value){ if (formError) formError.textContent = 'Difficulty is required'; return false; }
    if (levelName.value.length > 80){ if (formError) formError.textContent = 'Name too long'; return false; }
    if (formError) formError.textContent = '';
    return true;
  }

  function toPayload(){ return {
      name: levelName.value.trim(),
      description: levelDesc.value.trim(),
      difficulty: levelDiff.value
    };
  }

  async function saveModal(e){
    if (e) e.preventDefault();
    if (!validateForm()) return;
    const payload = toPayload();
    try {
      if (editingId == null){
        const resp = await fetch(API_BASE, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        if (!resp.ok){ const data = await resp.json(); formError && (formError.textContent = (data.errors || ['Error creating level']).join(' ')); return; }
      } else {
        const resp = await fetch(`${API_BASE}/${editingId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        if (!resp.ok){ const data = await resp.json(); formError && (formError.textContent = (data.errors || ['Error updating level']).join(' ')); return; }
      }
      await loadLevels();
      closeModal();
    } catch(err){ if (formError) formError.textContent = 'Request failed'; }
  }

  async function deleteLevel(id){ if(!confirm('Delete this level?')) return; const resp = await fetch(`${API_BASE}/${id}`, { method: 'DELETE' }); if (resp.ok){ await loadLevels(); if (selectedId === id){ setDetail(null); } } }

  // Bind modal events
  modalCancel.addEventListener('click', ()=> closeModal());
  modalClose.addEventListener('click', ()=> closeModal());
  modalBackdrop.addEventListener('click', (ev)=>{ if (ev.target === modalBackdrop) closeModal(); });
  modalSave.addEventListener('click', saveModal);
  levelForm.addEventListener('submit', saveModal);

  btnNew.addEventListener('click', openModalForNew);
  btnEditDetail.addEventListener('click', ()=>{ if (selectedId) openModalForEdit(selectedId); });
  btnDeleteDetail.addEventListener('click', ()=>{ if (selectedId) deleteLevel(selectedId); });

  async function loadLevels(){
    const resp = await fetch(API_BASE, { method: 'GET', headers: { 'Accept': 'application/json' } });
    if (!resp.ok) { detailContent.textContent = 'Error loading levels.'; return; }
    levels = await resp.json();
    renderTable();
    setDetail(null);
  }

  // initial load
  loadLevels();
})();
