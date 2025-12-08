// Simple local profile manager for Doom Clone frontend (localStorage)

const STORAGE_KEY = 'doomClone.profile';

function getProfile() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    // Basic validation
    if (!data || typeof data.name !== 'string') return null;
    return data;
  } catch (e) {
    console.error('Failed to read profile', e);
    return null;
  }
}

function saveProfile(profile) {
  const safe = { ...profile };
  if (typeof safe.name !== 'string') return false;
  // basic normalization
  safe.name = safe.name.trim();
  if (safe.name.length === 0) return false;
  safe.lastSaved = typeof safe.lastSaved === 'number' ? safe.lastSaved : Date.now();
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(safe));
    return true;
  } catch (e) {
    console.error('Failed to save profile', e);
    return false;
  }
}

function loadProfile() {
  return getProfile();
}

function deleteProfile() {
  try {
    localStorage.removeItem(STORAGE_KEY);
    return true;
  } catch (e) {
    console.error('Failed to delete profile', e);
    return false;
  }
}

export { getProfile, saveProfile, loadProfile, deleteProfile };
