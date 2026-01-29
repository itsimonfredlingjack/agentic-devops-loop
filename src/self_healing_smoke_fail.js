// Intentional lint failures to trigger CI failure and test self-healing pipeline
const bad = "double quotes instead of single"
const unused = "this variable is never used"

function brokenFunction() {
  var x = 1
  return
  console.log("unreachable code")
}
