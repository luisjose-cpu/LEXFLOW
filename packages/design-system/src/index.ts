export const colors = {
  white: "#ffffff",
  mist: "#f5f8fb",
  gray: {
    50: "#f8fafc",
    100: "#eef2f7",
    200: "#d9e2ec",
    500: "#64748b",
    700: "#334155",
    900: "#102033"
  },
  legal: {
    50: "#eef8ff",
    100: "#d9efff",
    500: "#2499e8",
    700: "#1264a3",
    900: "#0c355c"
  }
} as const;

export const spacing = {
  xs: "0.5rem",
  sm: "0.75rem",
  md: "1rem",
  lg: "1.5rem",
  xl: "2rem",
  "2xl": "3rem"
} as const;

export const typography = {
  fontFamily: "Inter, Geist, Arial, sans-serif",
  display: { fontSize: "3rem", lineHeight: "1.05", fontWeight: 650 },
  title: { fontSize: "1.75rem", lineHeight: "1.2", fontWeight: 650 },
  body: { fontSize: "1rem", lineHeight: "1.65", fontWeight: 400 },
  caption: { fontSize: "0.8125rem", lineHeight: "1.4", fontWeight: 500 }
} as const;

export const radius = {
  sm: "0.375rem",
  md: "0.5rem",
  lg: "0.75rem"
} as const;

export const shadows = {
  soft: "0 18px 60px rgba(16, 32, 51, 0.08)",
  focus: "0 0 0 3px rgba(36, 153, 232, 0.22)"
} as const;

export const breakpoints = {
  sm: "640px",
  md: "768px",
  lg: "1024px",
  xl: "1280px"
} as const;
