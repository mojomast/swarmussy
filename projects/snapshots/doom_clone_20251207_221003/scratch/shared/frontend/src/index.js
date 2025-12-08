import React from 'react';
import ReactDOM from 'react-dom/client';
import ProfilePanel from './ProfilePanel.jsx';
import { doomBootstrapping } from './doomBootstrapping.js';

// Hydration helper to connect profile data with the app shell
function hydrateProfile(profile) {
  window.__DOOM_APP_STATE__ = window.__DOOM_APP_STATE__ || {};
  window.__DOOM_APP_STATE__.profile = profile;

  // Notify app shell listeners that the profile has been hydrated
  try {
    const evt = new CustomEvent('doom-app-profile-hydrated', { detail: profile });
    window.dispatchEvent(evt);
  } catch (e) {
    // Ignore if CustomEvent is unavailable
  }

  // Optional dev log for visibility
  if (typeof console !== 'undefined' && typeof console.log === 'function') {
    console.log('Doom App: hydrated profile', profile);
  }
}

// Ensure we capture bootstrap events even if fired before listener is attached
window.addEventListener('doom-bootstrap-profile', (e) => {
  if (e && e.detail) {
    hydrateProfile(e.detail);
  }
});

// Bootstrapping: auto-load profile on startup
(async () => {
  try {
    const profile = await doomBootstrapping();
    if (profile) {
      hydrateProfile(profile);
    }
  } catch (e) {
    // ignore bootstrap errors
  }
})();

function App() {
  return (
    <div style={{ padding: 20 }}>
      <ProfilePanel onBootstrapped={hydrateProfile} />
    </div>
  );
}

const root = document.getElementById('root');
if (root) {
  ReactDOM.createRoot(root).render(<App />);
}
