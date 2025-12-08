// Node.js unit tests for user API validation
const assert = require('assert');

// Import the validation helper from the Express+SQLite API module
const { validateNewUser } = require('../src/users.js');

function runTests() {
  // Valid input should produce no validation errors
  const ok = validateNewUser({ name: 'Alice', email: 'alice@example.com' });
  try {
    assert.ok(Array.isArray(ok));
    assert.strictEqual(ok.length, 0, `Expected no errors, got: ${JSON.stringify(ok)}`);
  } catch (e) {
    console.error('Validation failed for valid input', ok, e);
    process.exitCode = 1;
  }

  // Invalid input should produce errors for missing name and invalid email
  const errs = validateNewUser({ name: '', email: 'not-an-email' });
  try {
    assert.ok(Array.isArray(errs));
    assert.ok(errs.includes('name_required'), 'Expected name_required error');
    assert.ok(errs.includes('email_invalid'), 'Expected email_invalid error');
  } catch (e) {
    console.error('Validation did not produce expected errors', errs);
    process.exitCode = 1;
  }

  if (process.exitCode === 1) {
    console.error('users_unit_test FAILED');
    process.exit(1);
  } else {
    console.log('users_unit_test PASSED');
  }
}

if (require.main === module) {
  runTests();
}

module.exports = { runTests };
