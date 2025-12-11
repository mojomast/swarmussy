import { useState, useEffect } from 'preact/hooks';
import { updateSettings, setDevussyMode, fetchDevussyStatus } from '../lib/api';
import { ThemeSelector } from './ThemeSelector';
import { X, Sliders, Palette, Bot, Zap, Database, RotateCcw } from 'lucide-preact';

export function SettingsModal({ onClose, settings: initialSettings }: any) {
  const [localSettings, setLocalSettings] = useState(initialSettings || {});
  const [devussyStatus, setDevussyStatus] = useState<any>({});
  const [activeTab, setActiveTab] = useState<'general' | 'models' | 'efficiency' | 'theme'>('general');

  useEffect(() => {
    fetchDevussyStatus().then(setDevussyStatus);
  }, []);

  const handleSave = async () => {
    await updateSettings(localSettings);
    onClose();
  };

  const toggleDevussy = async () => {
    const newState = !devussyStatus.mode_enabled;
    await setDevussyMode(newState);
    setDevussyStatus({ ...devussyStatus, mode_enabled: newState });
  };

  const handleResetDefaults = () => {
    setLocalSettings({
      username: 'User',
      architect_model: 'openrouter/anthropic/claude-sonnet-4',
      swarm_model: 'openrouter/anthropic/claude-sonnet-4',
      efficient_mode: true,
      context_messages: 5,
      max_tokens: 16000,
      max_tool_retries: 3
    });
  };

  const tabs = [
    { id: 'general', label: 'General', icon: Sliders },
    { id: 'models', label: 'Models', icon: Bot },
    { id: 'efficiency', label: 'Efficiency', icon: Zap },
    { id: 'theme', label: 'Theme', icon: Palette }
  ] as const;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-theme-secondary border border-theme rounded-xl w-[600px] max-h-[85vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="p-4 border-b border-theme flex justify-between items-center">
          <h2 className="text-lg font-bold text-theme-primary">Settings</h2>
          <button onClick={onClose} className="text-theme-muted hover:text-theme-primary transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-theme px-4">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2 -mb-px ${
                activeTab === tab.id
                  ? 'border-theme-accent text-theme-accent'
                  : 'border-transparent text-theme-muted hover:text-theme-primary'
              }`}
            >
              <tab.icon size={16} />
              {tab.label}
            </button>
          ))}
        </div>
        
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {/* General Tab */}
          {activeTab === 'general' && (
            <>
              <div className="space-y-2">
                <label className="text-sm text-theme-muted">Username</label>
                <input 
                  type="text" 
                  value={localSettings.username || ''}
                  onInput={(e) => setLocalSettings({...localSettings, username: e.currentTarget.value})}
                  className="w-full bg-theme-tertiary border border-theme rounded-lg px-3 py-2 text-theme-primary focus:outline-none focus:ring-2 focus:ring-theme-accent"
                />
              </div>

              <div className="space-y-4 pt-4 border-t border-theme">
                <h3 className="text-theme-primary font-bold flex items-center gap-2">
                  <Database size={16} />
                  Devussy Integration
                </h3>
                <div className="flex items-center justify-between bg-theme-tertiary/50 p-3 rounded-lg">
                  <div>
                    <span className="text-theme-secondary">Devussy Mode</span>
                    <p className="text-xs text-theme-muted mt-0.5">Enable AI-driven development planning</p>
                  </div>
                  <button 
                    onClick={toggleDevussy}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                      devussyStatus.mode_enabled 
                        ? 'bg-purple-600 text-white' 
                        : 'bg-theme-tertiary text-theme-muted hover:bg-theme-tertiary/70'
                    }`}
                  >
                    {devussyStatus.mode_enabled ? 'Enabled' : 'Disabled'}
                  </button>
                </div>
                {devussyStatus.available ? (
                  <div className="text-xs text-green-400 flex items-center gap-1">
                    <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                    Devussy core is available
                  </div>
                ) : (
                  <div className="text-xs text-red-400 flex items-center gap-1">
                    <span className="w-2 h-2 bg-red-400 rounded-full"></span>
                    Devussy core not found
                  </div>
                )}
              </div>
            </>
          )}

          {/* Models Tab */}
          {activeTab === 'models' && (
            <div className="space-y-4">
              <p className="text-sm text-theme-muted">Configure the AI models used by different agent roles.</p>
              
              <div className="space-y-4">
                <div className="bg-theme-tertiary/50 p-4 rounded-lg space-y-3">
                  <label className="text-sm font-medium text-theme-secondary">Architect Model</label>
                  <input 
                    type="text" 
                    value={localSettings.architect_model || ''}
                    onInput={(e) => setLocalSettings({...localSettings, architect_model: e.currentTarget.value})}
                    className="w-full bg-theme-tertiary border border-theme rounded-lg px-3 py-2 text-theme-primary font-mono text-sm focus:outline-none focus:ring-2 focus:ring-theme-accent"
                    placeholder="openrouter/anthropic/claude-sonnet-4"
                  />
                  <p className="text-xs text-theme-muted">Used for high-level planning and orchestration</p>
                </div>

                <div className="bg-theme-tertiary/50 p-4 rounded-lg space-y-3">
                  <label className="text-sm font-medium text-theme-secondary">Swarm Worker Model</label>
                  <input 
                    type="text" 
                    value={localSettings.swarm_model || ''}
                    onInput={(e) => setLocalSettings({...localSettings, swarm_model: e.currentTarget.value})}
                    className="w-full bg-theme-tertiary border border-theme rounded-lg px-3 py-2 text-theme-primary font-mono text-sm focus:outline-none focus:ring-2 focus:ring-theme-accent"
                    placeholder="openrouter/anthropic/claude-sonnet-4"
                  />
                  <p className="text-xs text-theme-muted">Used for backend, frontend, QA, and other worker agents</p>
                </div>
              </div>
            </div>
          )}

          {/* Efficiency Tab */}
          {activeTab === 'efficiency' && (
            <div className="space-y-4">
              <p className="text-sm text-theme-muted">Configure token usage and performance settings.</p>
              
              <div className="flex items-center justify-between bg-theme-tertiary/50 p-4 rounded-lg">
                <div>
                  <span className="text-theme-secondary font-medium">Efficient Mode</span>
                  <p className="text-xs text-theme-muted mt-0.5">Uses slim tools and lean prompts to reduce token usage</p>
                </div>
                <button 
                  onClick={() => setLocalSettings({...localSettings, efficient_mode: !localSettings.efficient_mode})}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    localSettings.efficient_mode 
                      ? 'bg-green-600 text-white' 
                      : 'bg-theme-tertiary text-theme-muted'
                  }`}
                >
                  {localSettings.efficient_mode ? 'On' : 'Off'}
                </button>
              </div>

              <div className="space-y-3">
                <label className="text-sm font-medium text-theme-secondary">Context Messages</label>
                <input
                  type="range"
                  min={1}
                  max={20}
                  value={localSettings.context_messages || 5}
                  onChange={(e) => setLocalSettings({...localSettings, context_messages: parseInt(e.currentTarget.value)})}
                  className="w-full accent-theme-accent"
                />
                <div className="flex justify-between text-xs text-theme-muted">
                  <span>Minimal (1)</span>
                  <span className="font-bold text-theme-primary">{localSettings.context_messages || 5} messages</span>
                  <span>Full (20)</span>
                </div>
              </div>

              <div className="space-y-3">
                <label className="text-sm font-medium text-theme-secondary">Max Tokens per Response</label>
                <input
                  type="number"
                  min={1000}
                  max={128000}
                  step={1000}
                  value={localSettings.max_tokens || 16000}
                  onChange={(e) => setLocalSettings({...localSettings, max_tokens: parseInt(e.currentTarget.value)})}
                  className="w-full bg-theme-tertiary border border-theme rounded-lg px-3 py-2 text-theme-primary focus:outline-none focus:ring-2 focus:ring-theme-accent"
                />
              </div>

              <div className="space-y-3">
                <label className="text-sm font-medium text-theme-secondary">Max Tool Retries</label>
                <input
                  type="range"
                  min={1}
                  max={10}
                  value={localSettings.max_tool_retries || 3}
                  onChange={(e) => setLocalSettings({...localSettings, max_tool_retries: parseInt(e.currentTarget.value)})}
                  className="w-full accent-theme-accent"
                />
                <div className="flex justify-between text-xs text-theme-muted">
                  <span>Conservative (1)</span>
                  <span className="font-bold text-theme-primary">{localSettings.max_tool_retries || 3} retries</span>
                  <span>Persistent (10)</span>
                </div>
              </div>
            </div>
          )}

          {/* Theme Tab */}
          {activeTab === 'theme' && (
            <div className="space-y-4">
              <p className="text-sm text-theme-muted">Customize the appearance of the dashboard.</p>
              <ThemeSelector />
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-theme flex items-center justify-between">
          <button 
            onClick={handleResetDefaults}
            className="flex items-center gap-2 px-3 py-2 text-theme-muted hover:text-theme-primary transition-colors"
          >
            <RotateCcw size={16} />
            Reset Defaults
          </button>
          <div className="flex gap-2">
            <button 
              onClick={onClose} 
              className="px-4 py-2 text-theme-muted hover:text-theme-primary transition-colors"
            >
              Cancel
            </button>
            <button 
              onClick={handleSave} 
              className="px-4 py-2 bg-theme-accent text-white rounded-lg hover:bg-theme-accent-hover transition-colors"
            >
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
