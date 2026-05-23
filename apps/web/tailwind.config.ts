import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "../../packages/ui/src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#102033",
        legal: {
          50: "#eef8ff",
          100: "#d9efff",
          500: "#2499e8",
          700: "#1264a3",
          900: "#0c355c"
        },
        mist: "#f5f8fb"
      },
      boxShadow: {
        soft: "0 18px 60px rgba(16, 32, 51, 0.08)"
      }
    }
  },
  plugins: []
};

export default config;
