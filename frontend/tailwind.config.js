/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Warm, paper-like palette - deliberately not a stark white/black
        // "generic AI app" look. See architecture doc's Design Direction.
        cream: '#FBF9F4',
        'cream-dark': '#F1ECE1',
        ink: '#2B2620',
        'ink-soft': '#6B6355',
        accent: '#8A5A34',          // used sparingly, for action/emphasis only
        'status-good': '#3F7A4E',
        'status-low': '#B7791F',
        'status-critical': '#B03A2E',
      },
      fontFamily: {
        heading: ['Georgia', 'serif'],
        body: ['system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}