// Optional: bootstrap hook to hydrate app state on startup using profile
import { loadProfile } from './profile.js';

export async function doomBootstrapping() {
  try {
    const profile = await loadProfile();
    if (profile) {
      // Dispatch an event for app shell to listen to
      try {
        const evt = new CustomEvent('doom-bootstrap-profile', { detail: profile });
        window.dispatchEvent(evt);
      } catch (e) {
        (window.__DOOM_BOOTSTRAP_PROFILE__ = profile);
      }
      return profile;
    }
    return null;
  } catch (e) {
    return null;
  }
}
