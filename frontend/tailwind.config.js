const defaultTheme = require("tailwindcss/defaultTheme");
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "Noto Sans", ...defaultTheme.fontFamily.sans],
        montserrat: ["Montserrat", "Inter", "Noto Sans", ...defaultTheme.fontFamily.sans],
      },
    },
    colors: {
      transparent: "transparent",
      current: "currentColor",
      white: "#ffffff",
      purple: "#3f3cbb",
      midnight: "#121063",
      metal: "#565584",
      tahiti: "#3ab7bf",
      silver: "#ecebff",
      "bubble-gum": "#ff77e9",
      bermuda: "#78dcca",
      "main-blue": "#4FACFE",
      "normal-text": "#6C7580",
      "main-text": "#4B5563",
      "second-blue": "#00F2FE",
      "gray-main": "#4b5563",
      "gray-normal": "#6c7580",
      "gray-text": "#6C7580",
      "gray-heading": "#4B5563",
      "main-cyan": "#00F2FE",
      background: "#f6f7fb",
      "main-start": "#00F2FE",
      "main-end": "#4FACFE",
      border: "#e5e7eb",
      "red-400": "#f77170",
      "orange-200": "#f8d8b7",
    },
  },
  plugins: [],
};
