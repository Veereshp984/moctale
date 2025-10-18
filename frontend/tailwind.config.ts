import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: "#6366f1",
          accent: "#a855f7",
        },
      },
    },
  },
  plugins: [],
};

export default config;
