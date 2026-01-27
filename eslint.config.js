import js from '@eslint/js';

export default [
  {
    ignores: ['node_modules', '.git', 'dist', 'build', '.pytest_cache', '.claude']
  },
  {
    files: ['src/**/*.js'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        console: 'readonly',
        HTMLElement: 'readonly',
        customElements: 'readonly',
        setInterval: 'readonly',
        clearInterval: 'readonly',
        module: 'readonly'
      }
    },
    rules: {
      ...js.configs.recommended.rules,
      'semi': ['error', 'always'],
      'quotes': ['error', 'single'],
      'indent': ['error', 2],
      'no-unused-vars': 'warn'
    }
  },
  {
    files: ['tests/**/*.js', 'jest.config.js'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'commonjs',
      globals: {
        console: 'readonly',
        process: 'readonly',
        Buffer: 'readonly',
        global: 'readonly',
        jest: 'readonly',
        describe: 'readonly',
        test: 'readonly',
        expect: 'readonly',
        beforeEach: 'readonly',
        afterEach: 'readonly',
        setInterval: 'readonly',
        clearInterval: 'readonly',
        HTMLElement: 'readonly',
        EventTarget: 'readonly',
        customElements: 'readonly',
        document: 'readonly',
        window: 'readonly',
        require: 'readonly',
        module: 'readonly'
      }
    },
    rules: {
      ...js.configs.recommended.rules,
      'semi': ['error', 'always'],
      'quotes': ['error', 'single'],
      'indent': ['error', 2],
      'no-unused-vars': 'warn'
    }
  }
];
