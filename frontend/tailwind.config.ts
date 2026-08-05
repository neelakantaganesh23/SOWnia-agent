import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f0ff",
          100: "#e0e0ff",
          200: "#c7c5ff",
          300: "#a5a0ff",
          400: "#8579ff",
          500: "#6c54fc",
          600: "#5e35f1",
          700: "#5028d4",
          800: "#4220ab",
          900: "#371d8a",
          950: "#1f0c5e",
        },
        // Vivid design-handoff risk palette (see
        // "Redesigning SOWnia into classical editorial/design_handoff_sownia_vivid/README.md")
        risk: {
          high: "#FB4E6D",
          medium: "#FBBF24",
          low: "#34D399",
        },
        surface: {
          50: "#f8f9fc",
          100: "#f1f3f9",
          200: "#e8eaf3",
          700: "#2a2d3a",
          800: "#1e2030",
          900: "#151725",
          950: "#0a0a11",
        },
        ink: "#f4f5fb",
        accent: "#C084FC",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        display: ["var(--font-plus-jakarta)", "var(--font-inter)", "system-ui", "sans-serif"],
      },
      maxWidth: {
        page: "1180px",
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out",
        "slide-up": "slideUp 0.4s ease-out",
        "pulse-slow": "pulse 3s ease-in-out infinite",
        shimmer: "shimmer 2s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        shimmer:
          "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.05) 50%, transparent 100%)",
        vivid:
          "linear-gradient(120deg,#38BDF8 0%,#A855F7 34%,#EC4899 66%,#FB923C 100%)",
      },
    },
  },
  plugins: [],
};

export default config;
