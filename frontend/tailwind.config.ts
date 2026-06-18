import type { Config } from "tailwindcss";

// Tokens do design system (.specs/DESIGN.md): 2 cores por tela, bordas 1px, sem gradientes.
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        page: "#fafafa",
        ink: "#1a1a1a",
        muted: "#6b7280",
        line: "#e6e6e6",
        accent: "#5e6ad2",
        "accent-hover": "#4f5ac0",
        "accent-soft": "#eef0fb",
        ok: "#16a34a",
        "ok-soft": "#e7f5ec",
        danger: "#dc2626",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      borderRadius: { lg: "8px", xl: "12px" },
      boxShadow: { sm: "0 1px 2px 0 rgba(16,24,40,0.04)" },
      transitionTimingFunction: { out: "cubic-bezier(0.16, 1, 0.3, 1)" },
    },
  },
  plugins: [],
};

export default config;
