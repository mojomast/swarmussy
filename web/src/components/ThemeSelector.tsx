import { useTheme, themes, ThemeName } from './ThemeProvider';
import { Palette, Check, Monitor } from 'lucide-preact';

export function ThemeSelector() {
  const { themeName, setTheme, theme: currentTheme } = useTheme();

  const handleThemeChange = (name: ThemeName) => {
    setTheme(name);
    // Force a re-render by updating CSS variables
    const root = document.documentElement;
    const theme = themes[name];
    Object.entries(theme.colors).forEach(([key, value]) => {
      root.style.setProperty(`--color-${key}`, value);
    });
    document.body.style.backgroundColor = theme.colors.bgPrimary;
    document.body.style.color = theme.colors.textSecondary;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm font-medium text-theme-secondary">
        <Palette size={16} className="text-theme-accent" />
        Choose Theme
      </div>
      
      {/* Current theme preview */}
      <div className="p-4 rounded-lg bg-theme-tertiary/50 border border-theme">
        <div className="flex items-center gap-3 mb-3">
          <Monitor size={16} className="text-theme-muted" />
          <span className="text-sm text-theme-muted">Current:</span>
          <span className="text-sm font-bold text-theme-primary">{currentTheme.displayName}</span>
        </div>
        <div className="flex gap-2">
          <div 
            className="w-8 h-8 rounded-lg border border-white/10" 
            style={{ backgroundColor: currentTheme.colors.bgPrimary }}
            title="Background"
          />
          <div 
            className="w-8 h-8 rounded-lg border border-white/10" 
            style={{ backgroundColor: currentTheme.colors.bgSecondary }}
            title="Secondary"
          />
          <div 
            className="w-8 h-8 rounded-lg border border-white/10" 
            style={{ backgroundColor: currentTheme.colors.accent }}
            title="Accent"
          />
          <div 
            className="w-8 h-8 rounded-lg border border-white/10" 
            style={{ backgroundColor: currentTheme.colors.success }}
            title="Success"
          />
          <div 
            className="w-8 h-8 rounded-lg border border-white/10" 
            style={{ backgroundColor: currentTheme.colors.error }}
            title="Error"
          />
        </div>
      </div>

      {/* Theme grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {(Object.keys(themes) as ThemeName[]).map((name) => {
          const theme = themes[name];
          const isActive = name === themeName;
          
          return (
            <button
              key={name}
              onClick={() => handleThemeChange(name)}
              className={`relative p-3 rounded-lg border-2 transition-all hover:scale-[1.02] ${
                isActive 
                  ? 'ring-2 ring-offset-2 ring-offset-transparent' 
                  : 'hover:border-opacity-70'
              }`}
              style={{ 
                backgroundColor: theme.colors.bgSecondary,
                borderColor: isActive ? theme.colors.accent : theme.colors.border,
                ringColor: isActive ? theme.colors.accent : 'transparent'
              }}
            >
              {/* Color preview dots */}
              <div className="flex gap-1.5 mb-2">
                <div 
                  className="w-4 h-4 rounded-full shadow-sm" 
                  style={{ backgroundColor: theme.colors.accent }} 
                />
                <div 
                  className="w-4 h-4 rounded-full shadow-sm" 
                  style={{ backgroundColor: theme.colors.success }} 
                />
                <div 
                  className="w-4 h-4 rounded-full shadow-sm" 
                  style={{ backgroundColor: theme.colors.warning }} 
                />
                <div 
                  className="w-4 h-4 rounded-full shadow-sm" 
                  style={{ backgroundColor: theme.colors.error }} 
                />
              </div>
              
              <span 
                className="text-xs font-medium block text-left"
                style={{ color: theme.colors.textPrimary }}
              >
                {theme.displayName}
              </span>
              
              {isActive && (
                <div 
                  className="absolute top-1.5 right-1.5 w-5 h-5 rounded-full flex items-center justify-center"
                  style={{ backgroundColor: theme.colors.accent }}
                >
                  <Check size={12} className="text-white" />
                </div>
              )}
            </button>
          );
        })}
      </div>
      
      <p className="text-xs text-theme-muted">
        Theme changes are applied immediately and saved to your browser.
      </p>
    </div>
  );
}
