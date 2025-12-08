#!/usr/bin/env node
// Lightweight Vitest-like test runner for local quick checks
import { promises as fs } from 'fs';
import path from 'path';
import { fileURLToPath, pathToFileURL } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const testsDir = path.resolve(__dirname, 'tests');

async function runTests() {
  let total = 0, passed = 0, failed = 0;
  try {
    const files = await fs.readdir(testsDir);
    for (const file of files) {
      if (!file.endsWith('.test.js')) continue;
      total++;
      const modPath = path.resolve(testsDir, file);
      const mod = await import(pathToFileURL(modPath).href);
      if (typeof mod.run !== 'function') {
        console.warn(`Skipping ${file}: no export 'run' function`);
        continue;
      }
      try {
        await mod.run();
        console.log(`PASS: ${file}`);
        passed++;
      } catch (e) {
        console.error(`FAIL: ${file} - ${e?.message ?? e}`);
        failed++;
      }
    }
  } catch (e) {
    console.error('Error scanning tests:', e);
  }
  console.log(`Tests run: ${total}, Passed: ${passed}, Failed: ${failed}`);
  if (failed>0) process.exitCode = 1;
}

runTests();
