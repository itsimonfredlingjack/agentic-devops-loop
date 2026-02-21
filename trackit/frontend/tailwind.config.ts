import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        terminal: {
          black: "#000000",
          green: "#33ff33",
          "green-dim": "#1a8c1a",
          amber: "#ffb000",
          "amber-dim": "#8c6000",
          white: "#ffffff",
          gray: "#555555",
          "dark-gray": "#222222",
          red: "#ff3333",
        },
      },
      fontFamily: {
        mono: [
          "JetBrains Mono",
          "Fira Code",
          "SF Mono",
          "ui-monospace",
          "monospace",
        ],
      },
    },
  },
  plugins: [],
};

export default config;
