// Frontend app wiring for backend-backed persistence

(function(){
  // Use the lightweight fetch wrapper from script/api-client.js
  const api = window.apiClient;

  const planEditor = document.getElementById('planEditor');
  const savePlanBtn = document.getElementById('savePlanBtn');
  const countsPanel = document.getElementById('countsPanel');
  const liveStatus = document.getElementById('liveStatus');
  const errorPanel = document.getElementById('errorPanel');
  const authBtn = document.getElementById('authBtn');
  const authStatus = document.getElementById('authStatus');

  // Authentication placeholder
  function ensureAuth(){
    try {
      const token = localStorage.getItem('authToken');
      if(token){ if(authStatus) authStatus.textContent = 'Authenticated'; if(authBtn) authBtn.textContent = 'Logout'; return true; }
    } catch(e) {}
    if(authStatus) authStatus.textContent = 'Guest';
    if(authBtn) authBtn.textContent = 'Login';
    return false;
  }
  if(authBtn){
    authBtn.addEventListener('click', async ()=>{
      const isAuth = ensureAuth();
      if(!isAuth){ // mock login
        localStorage.setItem('authToken', 'demo-token');
        if(authStatus) authStatus.textContent = 'Authenticated';
        if(authBtn) authBtn.textContent = 'Logout';
      } else {
        localStorage.removeItem('authToken');
        if(authStatus) authStatus.textContent = 'Guest';
        if(authBtn) authBtn.textContent = 'Login';
      }
    });
  }

  // Load initial plan and editor state from backend
  async function initFromBackend(){
    try {
      const [state, plan] = await Promise.all([
        api.getEditorState ? api.getEditorState() : Promise.resolve(null),
        api.getPlan ? api.getPlan() : Promise.resolve(null)
      ]);
      // Update UI with raw state info if available
      if(state && typeof state === 'object'){
        const mode = state.mode || 'unknown';
        const activePlanId = state.activePlanId || 'none';
        countsPanel && (countsPanel.textContent = 'Mode: ' + mode + ', Active Plan: ' + activePlanId);
      }
      if(plan && typeof plan === 'object'){
        planEditor.value = JSON.stringify(plan, null, 2);
        // show a small status in counts panel as well
        const updatedAt = plan.updatedAt || '';
        countsPanel && (countsPanel.textContent = (countsPanel.textContent || '') + (updatedAt ? ' | updated: ' + updatedAt : ''));
      }
    } catch(e){
      errorPanel && (errorPanel.textContent = 'Init error: ' + (e && e.message ? e.message : e));
    }
  }

  // Save plan to backend
  savePlanBtn && savePlanBtn.addEventListener('click', async ()=>{
    try {
      const parsed = JSON.parse(planEditor.value || '{}');
      const res = await api.savePlan ? api.savePlan(parsed) : null;
      if(res && typeof res === 'object'){
        const updatedAt = res.updatedAt || (res as any).updatedAt;
        errorPanel && (errorPanel.textContent = 'Plan saved';);
        countsPanel && (countsPanel.textContent = 'Last saved: ' + (updatedAt || 'OK'));
      } else {
        errorPanel && (errorPanel.textContent = 'Plan saved');
      }
    } catch(e){
      errorPanel && (errorPanel.textContent = 'Failed to save plan: ' + (e?.message || e));
    }
  });

  // Real-time plan progress display (poll backend)
  async function pollPlanProgress(){
    try {
      const plan = await (api.getPlan ? api.getPlan() : Promise.resolve(null));
      if(plan && typeof plan === 'object'){
        const status = plan.status || 'unknown';
        const updatedAt = plan.updatedAt || '';
        if(liveStatus) liveStatus.textContent = status + (updatedAt ? ' @ ' + updatedAt : '');
        // simple progress indicator in countsPanel for visibility
        const p = status === 'draft' ? 25 : status === 'review' ? 60 : status === 'ready' ? 100 : 40;
        if(countsPanel){ countsPanel.style.minWidth = '0'; countsPanel.textContent = (countsPanel.textContent || '') + ' | progress: ' + p + '%'; }
      }
    } catch(e){ /* ignore */ }
  }

  // Init
  ensureAuth();
  initFromBackend();
  pollPlanProgress();
  setInterval(pollPlanProgress, 5000);
})();
