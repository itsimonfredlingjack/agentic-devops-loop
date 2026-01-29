const { spawnSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const repoRoot = path.resolve(__dirname, '..');
const stopHookPath = path.join(repoRoot, '.claude', 'hooks', 'stop-hook.py');

describe('stop-hook cleanup when loop is inactive', () => {
  test('removes stale Ralph state and promise flag on exit', () => {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ralph-stop-hook-'));
    const claudeDir = path.join(tmpDir, '.claude');
    fs.mkdirSync(claudeDir, { recursive: true });

    const stateFile = path.join(claudeDir, 'ralph-state.json');
    const promiseFile = path.join(claudeDir, '.promise_done');

    fs.writeFileSync(stateFile, JSON.stringify({ iterations: 5 }));
    fs.writeFileSync(promiseFile, '<promise>DONE</promise>');

    const result = spawnSync('python3', [stopHookPath], {
      cwd: tmpDir,
      input: '',
      encoding: 'utf-8'
    });

    if (result.error && result.error.code === 'ENOENT') {
      throw new Error('python3 not found; stop-hook requires Python');
    }

    expect(result.status).toBe(0);
    expect(fs.existsSync(stateFile)).toBe(false);
    expect(fs.existsSync(promiseFile)).toBe(false);

    fs.rmSync(tmpDir, { recursive: true, force: true });
  });
});
