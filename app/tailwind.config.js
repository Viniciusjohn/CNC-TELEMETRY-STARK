/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
        colors: {
            slate: {
                850: '#151f2e',
                900: '#0f172a',
                950: '#020617',
            }
        }
    },
  },
  plugins: [],
}
