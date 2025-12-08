// Robust fetch-based API client for frontend editor
(function(global){
  // Safe storage wrapper for environments without window/localStorage
  const storage = (typeof (global.window) !== 'undefined' && global.window && global.window.localStorage)
    ? global.window.localStorage
    : {
        getItem: function(){ return null; },
        setItem: function(){},
        removeItem: function(){}
      };

  class ApiClient {
    constructor(baseURL = '') {
      this.baseURL = baseURL.endsWith('/') ? baseURL.slice(0, -1) : baseURL;
    }
    async _get(path) {
      const url = path.startsWith('/') ? path : (this.baseURL + '/' + path);
      const r = await fetch(url, { method: 'GET', credentials: 'same-origin' });
      if (!r.ok) {
        throw new Error('Request failed: ' + url);
      }
      return r.json();
    }
    async _post(path, body) {
      const url = (this.baseURL ? this.baseURL : '') + (path.startsWith('/') ? path : ('/' + path));
      const r = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        credentials: 'same-origin'
      });
      if (!r.ok) throw new Error('Request failed: ' + url);
      return r.json();
    }
    // High-level API surface
    async getEditorState() { return this._get('/api/editor/state'); }
    async getPlan() { return this._get('/api/editor/plan'); }
    async getAssets() { return this._get('/api/editor/assets'); }
    async getLevels() { return this._get('/api/editor/levels'); }
    async getEntities() { return this._get('/api/editor/entities'); }
    async savePlan(plan) { return this._post('/api/editor/plan', plan); }
    async login(username, password){
      // Simple placeholder that stores a token
      const token = 'demo-token';
      try { storage.setItem('authToken', token); } catch(e) {}
      return token;
    }
  }

  // Expose on the global object for legacy code compatibility
  const target = typeof window !== 'undefined' ? window : global;
  target.ApiClient = ApiClient;
  // Also expose a simple instance wrapper if desired by inline scripts
  target.apiClient = {
    // generic get/post for arbitrary endpoints
    get: (path) => new ApiClient('/').getRaw(path),
    post: (path, body) => new ApiClient('/').postRaw(path, body),
    // convenience wrappers for common endpoints
    getEditorState: () => new ApiClient('/').getEditorState(),
    getPlan: () => new ApiClient('/').getPlan(),
    getAssets: () => new ApiClient('/').getAssets(),
    getLevels: () => new ApiClient('/').getLevels(),
    getEntities: () => new ApiClient('/').getEntities(),
    savePlan: (p) => new ApiClient('/').savePlan(p)
  };
  // internal helpers bound to ApiClient to support generic get/post
  ApiClient.prototype.getRaw = function(path){ return this._get(path); };
  ApiClient.prototype.postRaw = function(path, body){ return this._post(path, body); };
  // module export for tests
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = ApiClient;
  }
})(typeof self !== 'undefined' ? self : this);
