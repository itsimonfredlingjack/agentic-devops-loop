module.exports = {
  testEnvironment: 'jsdom',
  testMatch: ['**/tests/task-tracker.test.js'],
  collectCoverageFrom: [
    'src/task-tracker.js'
  ],
  forceExit: true,
  detectOpenHandles: false
};
