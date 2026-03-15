/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        critical: '#DC2626',
        high: '#EA580C',
        medium: '#D97706',
        low: '#2563EB',
        info: '#6B7280',
      },
    },
  },
  plugins: [],
}
