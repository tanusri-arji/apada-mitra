/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bento: {
          bg: '#08090B',            // Deep Charcoal Black
          bgAlt: '#0B0D10',         // Dark Charcoal Secondary
          card: '#14181D',          // Dark Slate Gray card
          cardElevated: '#1C2228',  // Elevated glass card
          cardLight: '#242C34',     // Slightly lighter card
          border: 'rgba(255, 255, 255, 0.08)',
          borderHover: 'rgba(255, 255, 255, 0.16)',
          borderActive: 'rgba(255, 122, 24, 0.5)',
          orange: '#FF7A18',        // Primary Gradient Start
          yellow: '#FFB703',        // Primary Gradient End
          amber: '#F59E0B',         // Warning / Score Gold
          gold: '#FBBF24',
          emerald: '#10B981',       // Success / Healthy / Safe
          emeraldBright: '#22C55E',
          red: '#EF4444',           // Critical Danger
          orangeAccent: '#F97316',
          text: '#FFFFFF',          // Primary Pure White
          secondary: '#9CA3AF',     // Secondary Muted Gray
          muted: '#6B7280',         // Dark Muted Gray
        },
        // Mapped aliases for maximum backward compatibility across components
        command: {
          bg: '#08090B',
          card: '#14181D',
          panel: '#181D22',
          surface: '#1C2228',
          border: 'rgba(255, 255, 255, 0.08)',
          borderLight: 'rgba(255, 255, 255, 0.15)',
          accent: '#FF7A18',
          accentHover: '#FFB703',
          forest: '#10B981',
          text: '#FFFFFF',
          muted: '#9CA3AF',
          darkMuted: '#6B7280',
        },
        earth: {
          bg: '#08090B',
          bgAlt: '#0B0D10',
          surface: '#14181D',
          elevated: '#1C2228',
          border: 'rgba(255, 255, 255, 0.08)',
          borderLight: 'rgba(255, 255, 255, 0.15)',
          text: '#FFFFFF',
          muted: '#9CA3AF',
          darkMuted: '#6B7280',
          accent: '#FF7A18',
          accentHover: '#FFB703',
          forest: '#10B981',
          info: '#FBBF24',
          warning: '#F59E0B',
          high: '#F97316',
          critical: '#EF4444',
          safe: '#10B981',
        },
        risk: {
          low: '#10B981',
          moderate: '#F59E0B',
          high: '#F97316',
          critical: '#EF4444',
        },
      },
      backgroundImage: {
        'gradient-orange-yellow': 'linear-gradient(135deg, #FF7A18 0%, #FFB703 100%)',
        'gradient-card-glow': 'radial-gradient(ellipse at 50% 0%, rgba(255, 122, 24, 0.12) 0%, transparent 70%)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
};
