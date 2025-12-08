"use strict";
// Simple Node.js test to verify app shell event handling for doom-core-profile-updated

const assert = require('assert');

// Import the app shell event utilities (CommonJS export)
const { handleDoomCoreProfileUpdated, onProfileRefreshed, getCurrentProfile } = require('../frontend/src/appShellEvents.js');

function runTests() {
  let received = [];
  const unsubscribe = onProfileRefreshed((profile) => {
    received.push(profile);
  });

  const testProfile = { name: 'Alice', avatar: '😀' };
  handleDoomCoreProfileUpdated(testProfile);

  try {
    assert.strictEqual(received.length, 1, 'Listener should have been called exactly once');
    assert.deepStrictEqual(received[0], testProfile, 'Listener received correct profile');
    assert.deepStrictEqual(getCurrentProfile(), testProfile, 'Current profile should reflect the update');

    unsubscribe();

    console.log('app_shell_events.test.js PASSED');
  } catch (e) {
    console.error('app_shell_events.test.js FAILED', e && e.message ? e.message : e);
    process.exitCode = 1;
  }
}

if (require.main === module) {
  runTests();
}
