import { useState, useEffect } from 'preact/hooks';
import { 
  X, Bot, Cpu, Repeat, Hash, Thermometer, Clock, Save, 
  RotateCcw, ChevronDown, ChevronRight, Settings2
} from 'lucide-preact';

interface AgentConfig {
  name: string;
  model: string;
  max_tokens: number;
  max_tool_retries: number;
  temperature: number;
  timeout_seconds: number;
  enabled: boolean;
}

interface Props {
  agent: any;
  onClose: () => void;
  onSave: (agentId: string, config: Partial<AgentConfig>) => Promise<void>;
  availableModels?: string[];
}

const DEFAULT_MODELS = [
  'openrouter/anthropic/claude-sonnet-4',
  'openrouter/anthropic/claude-3.5-sonnet',
  'openrouter/google/gemini-2.0-flash-001',
  'openrouter/openai/gpt-4o',
  'openrouter/openai/gpt-4o-mini',
  'openrouter/deepseek/deepseek-chat',
  'openrouter/meta-llama/llama-3.1-70b-instruct',
];

export function AgentSettingsPanel({ agent, onClose, onSave, availableModels = DEFAULT_MODELS }: Props) {
  const [config, setConfig] = useState<AgentConfig>({
    name: agent.name || '',
    model: agent.model || 'openrouter/anthropic/claude-sonnet-4',
    max_tokens: agent.max_tokens || 16000,
    max_tool_retries: agent.max_tool_retries || 3,
    temperature: agent.temperature || 0.7,
    timeout_seconds: agent.timeout_seconds || 120,
    enabled: agent.enabled !== false
  });
  const [saving, setSaving] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(agent.agent_id, config);
      onClose();
    } catch (e) {
      console.error('Failed to save agent config', e);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setConfig({
      name: agent.name || '',
      model: agent.model || 'openrouter/anthropic/claude-sonnet-4',
      max_tokens: 16000,
      max_tool_retries: 3,
      temperature: 0.7,
      timeout_seconds: 120,
      enabled: true
    });
  };

  const getAgentColor = (name: string) => {
    const colors: Record<string, string> = {
      'Bossy McArchitect': 'text-purple-400 bg-purple-900/20 border-purple-500/30',
      'Codey McBackend': 'text-blue-400 bg-blue-900/20 border-blue-500/30',
      'Pixel McFrontend': 'text-pink-400 bg-pink-900/20 border-pink-500/30',
      'Bugsy McTester': 'text-green-400 bg-green-900/20 border-green-500/30',
      'Deployo McOps': 'text-yellow-400 bg-yellow-900/20 border-yellow-500/30',
      'Checky McManager': 'text-cyan-400 bg-cyan-900/20 border-cyan-500/30',
      'Docy McWriter': 'text-red-400 bg-red-900/20 border-red-500/30'
    };
    return colors[name] || 'text-gray-400 bg-gray-900/20 border-gray-500/30';
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-theme-secondary border border-theme rounded-xl w-[450px] max-h-[85vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className={`p-4 border-b border-theme flex items-center justify-between rounded-t-xl ${getAgentColor(agent.name)}`}>
          <div className="flex items-center gap-3">
            <Bot size={24} />
            <div>
              <h2 className="font-bold text-lg">{agent.name}</h2>
              <p className="text-xs opacity-70">{agent.role || 'Swarm Agent'}</p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-2 hover:bg-black/20 rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Model Selection */}
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm text-theme-muted">
              <Cpu size={14} />
              Model
            </label>
            <select
              value={config.model}
              onChange={(e) => setConfig({...config, model: e.currentTarget.value})}
              className="w-full bg-theme-tertiary border border-theme rounded-lg px-3 py-2 text-theme-primary focus:outline-none focus:ring-2 focus:ring-theme-accent"
            >
              {availableModels.map(model => (
                <option key={model} value={model}>{model.split('/').pop()}</option>
              ))}
            </select>
          </div>

          {/* Max Tokens */}
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm text-theme-muted">
              <Hash size={14} />
              Max Tokens
            </label>
            <input
              type="number"
              value={config.max_tokens}
              onChange={(e) => setConfig({...config, max_tokens: parseInt(e.currentTarget.value) || 16000})}
              min={1000}
              max={128000}
              step={1000}
              className="w-full bg-theme-tertiary border border-theme rounded-lg px-3 py-2 text-theme-primary focus:outline-none focus:ring-2 focus:ring-theme-accent"
            />
            <div className="flex justify-between text-xs text-theme-muted">
              <span>Min: 1,000</span>
              <span>Current: {config.max_tokens.toLocaleString()}</span>
              <span>Max: 128,000</span>
            </div>
          </div>

          {/* Max Tool Retries */}
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm text-theme-muted">
              <Repeat size={14} />
              Max Tool Retries
            </label>
            <input
              type="range"
              value={config.max_tool_retries}
              onChange={(e) => setConfig({...config, max_tool_retries: parseInt(e.currentTarget.value)})}
              min={1}
              max={10}
              className="w-full accent-theme-accent"
            />
            <div className="flex justify-between text-xs text-theme-muted">
              <span>Conservative (1)</span>
              <span className="font-bold text-theme-primary">{config.max_tool_retries} retries</span>
              <span>Persistent (10)</span>
            </div>
          </div>

          {/* Advanced Settings */}
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-2 text-sm text-theme-muted hover:text-theme-primary transition-colors"
          >
            <Settings2 size={14} />
            Advanced Settings
            {showAdvanced ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </button>

          {showAdvanced && (
            <div className="space-y-4 pl-4 border-l-2 border-theme">
              {/* Temperature */}
              <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm text-theme-muted">
                  <Thermometer size={14} />
                  Temperature
                </label>
                <input
                  type="range"
                  value={config.temperature}
                  onChange={(e) => setConfig({...config, temperature: parseFloat(e.currentTarget.value)})}
                  min={0}
                  max={1}
                  step={0.1}
                  className="w-full accent-theme-accent"
                />
                <div className="flex justify-between text-xs text-theme-muted">
                  <span>Precise (0)</span>
                  <span className="font-bold text-theme-primary">{config.temperature.toFixed(1)}</span>
                  <span>Creative (1)</span>
                </div>
              </div>

              {/* Timeout */}
              <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm text-theme-muted">
                  <Clock size={14} />
                  Timeout (seconds)
                </label>
                <input
                  type="number"
                  value={config.timeout_seconds}
                  onChange={(e) => setConfig({...config, timeout_seconds: parseInt(e.currentTarget.value) || 120})}
                  min={30}
                  max={600}
                  className="w-full bg-theme-tertiary border border-theme rounded-lg px-3 py-2 text-theme-primary focus:outline-none focus:ring-2 focus:ring-theme-accent"
                />
              </div>

              {/* Enable/Disable */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-theme-muted">Agent Enabled</span>
                <button
                  onClick={() => setConfig({...config, enabled: !config.enabled})}
                  className={`px-3 py-1 rounded-lg text-sm transition-colors ${
                    config.enabled 
                      ? 'bg-green-600 text-white' 
                      : 'bg-gray-700 text-gray-400'
                  }`}
                >
                  {config.enabled ? 'Enabled' : 'Disabled'}
                </button>
              </div>
            </div>
          )}

          {/* Current Stats */}
          <div className="bg-theme-tertiary/50 rounded-lg p-3 border border-theme space-y-2">
            <div className="text-xs font-bold text-theme-muted uppercase tracking-wide">Current Session Stats</div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex justify-between">
                <span className="text-theme-muted">Status:</span>
                <span className={`font-bold ${
                  agent.status === 'working' ? 'text-green-400' : 
                  agent.status === 'idle' ? 'text-gray-400' : 'text-red-400'
                }`}>
                  {agent.status || 'Unknown'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-theme-muted">Messages:</span>
                <span className="text-theme-primary">{agent.message_count || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-theme-muted">Tool Calls:</span>
                <span className="text-theme-primary">{agent.tool_call_count || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-theme-muted">Tokens Used:</span>
                <span className="text-yellow-400">{(agent.tokens_used || 0).toLocaleString()}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-theme flex items-center justify-between">
          <button
            onClick={handleReset}
            className="flex items-center gap-2 px-3 py-2 text-theme-muted hover:text-theme-primary transition-colors"
          >
            <RotateCcw size={16} />
            Reset
          </button>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-theme-muted hover:text-theme-primary transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2 px-4 py-2 bg-theme-accent text-white rounded-lg hover:bg-theme-accent-hover transition-colors disabled:opacity-50"
            >
              <Save size={16} />
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
