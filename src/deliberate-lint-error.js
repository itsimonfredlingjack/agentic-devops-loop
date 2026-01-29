// Deliberate lint error: missing semicolons (ESLint semi: error)
// This file exists solely to trigger a CI failure for self-healing testing.

const unusedVar = 42

function brokenFunction() {
  const result = "double quotes instead of single"
  return result
}

module.exports = { brokenFunction }
