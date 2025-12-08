export function sum(a: number, b: number): number {
  return a + b;
}

export function isEven(n: number): boolean {
  return n % 2 === 0;
}

export const TESTS_RUN = true;

// Smoke runner for CI: run in ts-node
try {
  if (sum(2, 3) === 5 && isEven(2) === true) {
    console.log('ci-sample-tests: PASSED');
  } else {
    console.error('ci-sample-tests: FAILED assertion');
    process.exit(1);
  }
} catch (e) {
  console.error('ci-sample-tests: ERROR', e);
  process.exit(1);
}
