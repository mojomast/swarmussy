// Simple auth placeholder for frontend
(function(){
  const authBtn = document.getElementById('authBtn');
  const authStatus = document.getElementById('authStatus');
  if(!authBtn) return;
  authBtn.addEventListener('click', async ()=>{
    const token = 'demo-token';
    localStorage.setItem('authToken', token);
    authStatus.textContent = 'Authenticated';
  });
})();
