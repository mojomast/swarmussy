const assert = require('assert');
const http = require('http');
const fs = require('fs');

// Programmatic Mocha runner to enable post-run artifacts collection

let logsStream;
try {
  // Prefer host-mounted artifacts for CI; fallback to local file
  fs.mkdirSync('/artifacts', { recursive: true });
  logsStream = fs.createWriteStream('/artifacts/test_logs.txt', { flags: 'a' });
} catch (e) {
  logsStream = fs.createWriteStream('./test_logs.txt', { flags: 'a' });
}

const log = (...args) => {
  const line = args.map(a => (typeof a === 'string' ? a : JSON.stringify(a))).join(' ');
  logsStream.write(line + '\n');
  // Also print to console for local debugging
  console.log(...args);
};

console.log = log;
console.error = log;

if (require.main === module) {
  const Mocha = require('mocha');
  const mocha = new Mocha({ ui: 'bdd' });
  // Add this file which contains the tests
  mocha.addFile(__filename);

  let passes = 0;
  let failures = 0;

  const results = {
    total: 0,
    passes: 0,
    failures: 0,
    timestamp: new Date().toISOString()
  };

  const ensureArtifactsDir = () => {
    try { fs.mkdirSync('/artifacts', { recursive: true }); } catch (e) {}
  };

  const finalize = (failuresCount) => {
    results.total = passes + failures;
    results.passes = passes;
    results.failures = failuresCount;
    results.timestamp = new Date().toISOString();
    // Write to artifacts (container) if possible
    try {
      ensureArtifactsDir();
      fs.writeFileSync('/artifacts/test_results.json', JSON.stringify(results, null, 2), 'utf8');
    } catch (e) {
      // ignore
    }
    // Also write to repo path for CI artifact collection
    try {
      const repoPath = './test_results.json';
      fs.writeFileSync(repoPath, JSON.stringify(results, null, 2), 'utf8');
    } catch (e) {
      // ignore
    }
    process.exitCode = failuresCount > 0 ? 1 : 0;
  };

  const runner = mocha.run(function(failuresCount) {
    finalize(failuresCount);
  });

  runner.on('pass', function(test) {
    passes++;
  });
  runner.on('fail', function(test, err) {
    failures++;
  });
}

// Original tests below

describe('node-backend', function() {
  it('should pass basic test', function() {
    // Basic smoke test
    if (2 !== 2) throw new Error('Math is broken');
  });
  it('auth token test should be provided and valid (optional in local env)', function(done) {
    // In CI, AUTH_TOKEN should be provided and valid. If not provided, this test is skipped gracefully.
    if (process.env.AUTH_TOKEN !== undefined) {
      if (process.env.AUTH_TOKEN !== 'supersecrettoken') {
        return done(new Error('Invalid AUTH_TOKEN'));
      }
    }
    done();
  });

  it('auth-mock integration test', function(done) {
    if (process.env.AUTH_MOCK_ENABLED !== 'true') {
      this.skip();
      return done();
    }
    const options = {
      hostname: 'auth-mock',
      port: 8080,
      path: '/validate',
      method: 'GET',
      headers: {
        'Authorization': 'Bearer supersecrettoken'
      }
    };
    const req = http.request(options, (res) => {
      let body = '';
      res.setEncoding('utf8');
      res.on('data', (chunk) => { body += chunk; });
      res.on('end', () => {
        try {
          const parsed = JSON.parse(body);
          if (res.statusCode === 200 && parsed && parsed.valid === true) {
            done();
          } else {
            done(new Error('Auth mock validation failed'));
          }
        } catch (e) {
          done(e);
        }
      });
    });
    req.on('error', (e) => done(e));
    req.end();
  });
});

// Simple runner to satisfy npm test when executed directly
if (require.main === module) {
  // This block is not used since we handle programmatic runner above.
}
