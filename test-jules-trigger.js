// Intentional failing test to trigger Jules self-healing
// This file should be automatically fixed by Jules when CI fails

console.log("Running test...");

// Deliberate assertion failure
const expected = 42;
const actual = 0;

if (actual !== expected) {
  console.error(`FAIL: Expected ${expected} but got ${actual}`);
  process.exit(1);
}

console.log("PASS");
