/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          light: '#8B5CF6', // purple-500
          dark: '#A78BFA',  // purple-400
        },
        secondary: {
          light: '#2563EB', // blue-600
          dark: '#3B82F6',  // blue-500
        },
      },
      gradientColorStops: {
        'gradient-1-light': '#f9fafb',
        'gradient-2-light': '#eff6ff',
        'gradient-3-light': '#dbeafe',
        'gradient-1-dark': '#111827',
        'gradient-2-dark': '#1e3a8a',
        'gradient-3-dark': '#172554',
      },
    },
  },
  plugins: [],
}