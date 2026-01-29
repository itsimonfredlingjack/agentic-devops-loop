// Intentional lint failures to trigger CI failure and test self-healing pipeline
export const bad = 'double quotes instead of single';
export const unused = 'this variable is never used';

export function brokenFunction() {
  const x = 1;
  return x;
}
