// Deliberate failing test to trigger CI failure for self-healing testing.

describe('Controlled CI Failure', () => {
  test('this test deliberately fails', () => {
    expect(1 + 1).toBe(3);
  });
});
