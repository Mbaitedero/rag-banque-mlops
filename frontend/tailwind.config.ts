import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          900: "#14243a",
          950: "#0c1727",
        },
        institutional: {
          green: "#247a57",
          gray: "#f3f5f7",
        },
      },
    },
  },
  plugins: [],
};

export default config;
