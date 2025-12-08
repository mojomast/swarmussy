import React from 'react';
import ReactDOM from 'react-dom/client';
import ProfilePanel from './src/ProfilePanel.jsx';
import ProfilePanelPlaceholder from './src/ProfilePanelPlaceholder.jsx';
import { doomBootstrapping } from './src/doomBootstrapping.js';

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

function AppShellLoader() {
  const [usingSkeleton, setUsingSkeleton] = React.useState(true);

  React.useEffect(() => {
    const onBootstrap = (e) => {
      if (e && e.detail) {
        hydrateProfile(e.detail);
        setUsingSkeleton(false);
      }
    };
    window.addEventListener('doom-bootstrap-profile', onBootstrap);
    return () => window.removeEventListener('doom-bootstrap-profile', onBootstrap);
  }, []);

  // Listen for doom-core-profile-updated to hydrate with external profile updates
  React.useEffect(() => {
    const onUpdated = (e) => {
      if (e && e.detail) {
        hydrateProfile(e.detail);
      }
    };
    window.addEventListener('doom-core-profile-updated', onUpdated);
    return () => window.removeEventListener('doom-core-profile-updated', onUpdated);
  }, []);

  // Bootstrapping: auto-load profile on startup
  React.useEffect(() => {
    (async () => {
      try {
        const profile = await doomBootstrapping();
        if (profile) {
          hydrateProfile(profile);
          setUsingSkeleton(false);
        }
      } catch {
        // ignore bootstrap errors
      }
    })();
  }, []);

  if (usingSkeleton) {
    return <ProfilePanelPlaceholder />;
  }
  return <ProfilePanel onBootstrapped={hydrateProfile} />;
}

function App() {
  return (
    <div style={{ padding: 20 }}>
      <AppShellLoader />
    </div>
  );
}

const root = document.getElementById('root');
if (root) {
  ReactDOM.createRoot(root).render(<App />);
}
