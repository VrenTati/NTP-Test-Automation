module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html",
  ],
  theme: {
    extend: {
      colors: {
        'currency-gold': '#FFD700',
        'currency-silver': '#C0C0C0',
        'ai-blue': '#3B82F6',
        'ai-green': '#10B981',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { 
            opacity: '0',
            transform: 'translateY(20px)'
          },
          '100%': { 
            opacity: '1',
            transform: 'translateY(0)'
          },
        }
      },
      boxShadow: {
        'ai': '0 4px 14px 0 rgba(59, 130, 246, 0.15)',
        'currency': '0 8px 25px 0 rgba(255, 215, 0, 0.3)',
      }
    },
  },
  plugins: [],
}
