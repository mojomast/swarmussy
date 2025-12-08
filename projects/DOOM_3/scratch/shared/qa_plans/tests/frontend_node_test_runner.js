// Node.js frontend tests runner that executes skeletons
const { testPlaceholder } = require('./frontend_unit_skeleton.js');
const { testIntegrationPlaceholder } = require('./frontend_integration_skeleton.js');
const { testE2ESkeleton } = require('./frontend_e2e_skeleton.js');

function run() {
  let ok = true;
  try {
    ok = ok && Boolean(testPlaceholder());
  } catch (e) {
    ok = false;
  }
  try {
    ok = ok && Boolean(testIntegrationPlaceholder());
  } catch (e) {
    ok = false;
  }
  try {
    ok = ok && Boolean(testE2ESkeleton());
  } catch (e) {
    ok = false;
  }
  console.log("Frontend Node tests: ", ok ? 'PASS' : 'FAIL');
  process.exit(ok ? 0 : 1);
}

run();
