"use strict";
// Lightweight app shell event bridge for Doom Clone profile updates.

let currentProfile = null;
const listeners = new Set();

function notify(profile) {
  for (const cb of listeners) {
    try {
      cb(profile);
    } catch (e) {
      // swallow to avoid breaking app shell tests
    }
  }
}

function handleDoomCoreProfileUpdated(profile) {
  currentProfile = profile;
  notify(profile);
}

function onProfileRefreshed(callback) {
  listeners.add(callback);
  return () => {
    listeners.delete(callback);
  };
}

function getCurrentProfile() {
  return currentProfile;
}

module.exports = { handleDoomCoreProfileUpdated, onProfileRefreshed, getCurrentProfile };
