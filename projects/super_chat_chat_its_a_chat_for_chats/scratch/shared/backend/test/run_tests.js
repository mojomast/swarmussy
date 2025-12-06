const { exec } = require('child_process');

console.log('Running backend smoke tests...');
exec('node -e "require(\'./server.js\')"', (error, stdout, stderr) => {
  if (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }
  console.log(stdout);
  console.log(stderr);
  console.log('Backend smoke tests completed.');
});
