/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          50: '#e6e9f0',
          100: '#cdd3e1',
          200: '#9ba7c3',
          300: '#697ba5',
          400: '#374f87',
          500: '#052369',
          600: '#041c54',
          700: '#03153f',
          800: '#020e2a',
          900: '#010715',
        },
      },
    },
  },
  plugins: [],
}
