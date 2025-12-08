"use strict";
// Regression test: ensure delayed doom-core-profile-updated events are honored by app shell

const assert = require('assert');

const { handleDoomCoreProfileUpdated, onProfileRefreshed, getCurrentProfile } = require('../frontend/src/appShellEvents.js');

function runTests() {
  let received = [];
  const unsubscribe = onProfileRefreshed((profile) => {
    received.push(profile);
  });

  // Schedule a delayed update
  setTimeout(() => {
    const delayedProfile = { name: 'DelayedUser', avatar: '🪪' };
    handleDoomCoreProfileUpdated(delayedProfile);
  }, 50);

  // After a bit, verify the delayed event was processed
  setTimeout(() => {
    try {
      if (received.length !== 1) throw new Error(`Expected 1 update, got ${received.length}`);
      const upd = received[0];
      if (!upd || upd.name !== 'DelayedUser' || upd.avatar !== '🪪') {
        throw new Error('Received wrong profile data');
      }
      if (getCurrentProfile() == null || getCurrentProfile().name !== 'DelayedUser') {
        throw new Error('Current profile not updated correctly');
      }
      unsubscribe();
      console.log('app_shell_delayed_events.test.js PASSED');
    } catch (e) {
      console.error('app_shell_delayed_events.test.js FAILED', e && e.message ? e.message : e);
      process.exitCode = 1;
    }
  }, 120);
}

if (require.main === module) {
  runTests();
}
