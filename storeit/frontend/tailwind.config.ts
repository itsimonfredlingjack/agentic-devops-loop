import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#0a0a0a",
          raised: "#141414",
          overlay: "#1a1a1a",
          border: "#262626",
        },
        text: {
          primary: "#e8e4de",
          secondary: "#8a8580",
          muted: "#5a5550",
        },
        accent: {
          DEFAULT: "#ff4f00",
          hover: "#ff6b2b",
        },
      },
      fontFamily: {
        mono: ["var(--font-geist-mono)", "ui-monospace", "monospace"],
        sans: ["var(--font-geist-sans)", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
