/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          950: '#070a13',
          900: '#0B0F19',
          850: '#0f172a',
          800: '#111827',
          700: '#1e293b',
          600: '#334155',
          500: '#475569',
        },
        brand: {
          cyan: '#06b6d4',
          emerald: '#10b981',
          teal: '#14b8a6',
        }
      }
    },
  },
  plugins: [],
}
