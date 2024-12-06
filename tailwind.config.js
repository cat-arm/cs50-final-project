/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html", // Adjust this to your project structure
    "./static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          light: "#a7f3d0",
          DEFAULT: "#10b981",
          dark: "#047857",
        },
        secondary: {
          light: "#d1fae5",
          DEFAULT: "#34d399",
          dark: "#065f46",
        },
        neutral: {
          light: "#f3f4f6",
          DEFAULT: "#d1d5db",
          dark: "#374151",
        },
      },
      borderRadius: {
        lg: "1rem",
      },
    },
  },
  plugins: [],
};
