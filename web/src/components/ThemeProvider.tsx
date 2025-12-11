import { createContext } from 'preact';
import { useState, useEffect, useContext } from 'preact/hooks';

export type ThemeName = 'dark' | 'midnight' | 'cyberpunk' | 'forest' | 'sunset';

interface Theme {
  name: ThemeName;
  displayName: string;
  colors: {
    bgPrimary: string;
    bgSecondary: string;
    bgTertiary: string;
    border: string;
    textPrimary: string;
    textSecondary: string;
    textMuted: string;
    accent: string;
    accentHover: string;
    success: string;
    warning: string;
    error: string;
  };
}

export const themes: Record<ThemeName, Theme> = {
  dark: {
    name: 'dark',
    displayName: 'Dark',
    colors: {
      bgPrimary: '#030712',
      bgSecondary: '#111827',
      bgTertiary: '#1f2937',
      border: '#374151',
      textPrimary: '#f9fafb',
      textSecondary: '#e5e7eb',
      textMuted: '#9ca3af',
      accent: '#3b82f6',
      accentHover: '#2563eb',
      success: '#22c55e',
      warning: '#eab308',
      error: '#ef4444',
    },
  },
  midnight: {
    name: 'midnight',
    displayName: 'Midnight Blue',
    colors: {
      bgPrimary: '#0f172a',
      bgSecondary: '#1e293b',
      bgTertiary: '#334155',
      border: '#475569',
      textPrimary: '#f1f5f9',
      textSecondary: '#e2e8f0',
      textMuted: '#94a3b8',
      accent: '#6366f1',
      accentHover: '#4f46e5',
      success: '#10b981',
      warning: '#f59e0b',
      error: '#f43f5e',
    },
  },
  cyberpunk: {
    name: 'cyberpunk',
    displayName: 'Cyberpunk',
    colors: {
      bgPrimary: '#0a0a0f',
      bgSecondary: '#12121a',
      bgTertiary: '#1a1a25',
      border: '#ff00ff30',
      textPrimary: '#00ffff',
      textSecondary: '#e0e0ff',
      textMuted: '#8080a0',
      accent: '#ff00ff',
      accentHover: '#cc00cc',
      success: '#00ff88',
      warning: '#ffff00',
      error: '#ff0055',
    },
  },
  forest: {
    name: 'forest',
    displayName: 'Forest',
    colors: {
      bgPrimary: '#0f1a14',
      bgSecondary: '#162419',
      bgTertiary: '#1e3022',
      border: '#2d4a35',
      textPrimary: '#e8f5e9',
      textSecondary: '#c8e6c9',
      textMuted: '#81c784',
      accent: '#4caf50',
      accentHover: '#388e3c',
      success: '#66bb6a',
      warning: '#ffd54f',
      error: '#ef5350',
    },
  },
  sunset: {
    name: 'sunset',
    displayName: 'Sunset',
    colors: {
      bgPrimary: '#1a1210',
      bgSecondary: '#261a15',
      bgTertiary: '#33231c',
      border: '#4d3527',
      textPrimary: '#fff3e0',
      textSecondary: '#ffcc80',
      textMuted: '#a1887f',
      accent: '#ff7043',
      accentHover: '#f4511e',
      success: '#66bb6a',
      warning: '#ffb74d',
      error: '#ef5350',
    },
  },
};

const THEME_STORAGE_KEY = 'swarm_theme';

interface ThemeContextValue {
  theme: Theme;
  themeName: ThemeName;
  setTheme: (name: ThemeName) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: any }) {
  const [themeName, setThemeName] = useState<ThemeName>(() => {
    const stored = localStorage.getItem(THEME_STORAGE_KEY) as ThemeName;
    return stored && themes[stored] ? stored : 'dark';
  });

  useEffect(() => {
    const theme = themes[themeName];
    const root = document.documentElement;
    
    // Apply CSS custom properties
    Object.entries(theme.colors).forEach(([key, value]) => {
      root.style.setProperty(`--color-${key}`, value);
    });
    
    // Also set body background directly for immediate effect
    document.body.style.backgroundColor = theme.colors.bgPrimary;
    document.body.style.color = theme.colors.textSecondary;
    
    localStorage.setItem(THEME_STORAGE_KEY, themeName);
  }, [themeName]);

  const value: ThemeContextValue = {
    theme: themes[themeName],
    themeName,
    setTheme: setThemeName,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
