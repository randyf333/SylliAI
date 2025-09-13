/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        'sylliai': {
          light: '#e8e6ff',
          DEFAULT: '#8a7fff',
          dark: '#6a5aff'
        }
      }
    },
  },
  plugins: [],
}