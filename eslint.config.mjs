export default [
  {
    ignores: [
      "node_modules/**",
      "docs/**",
      "monitor-server/**",
      "dist/**",
    ],
  },
  {
    files: ["**/*.{js,mjs,cjs}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
    },
    rules: {},
  },
];
