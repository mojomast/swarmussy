import { useState, useEffect } from 'preact/hooks';
import { 
  fetchProviders, 
  fetchAvailableModels, 
  updateApiKey, 
  testApiKey,
  updateSettings,
  fetchSettings
} from '../lib/api';
import { 
  Key, 
  Check, 
  X, 
  AlertCircle, 
  Loader2, 
  Eye, 
  EyeOff,
  Server,
  Bot,
  Sparkles,
  ChevronDown,
  RefreshCw
} from 'lucide-preact';

interface Provider {
  id: string;
  name: string;
  has_key: boolean;
  key_env_var: string;
  base_url?: string;
}

interface Model {
  id: string;
  name: string;
  provider: string;
}

interface Props {
  onClose: () => void;
}

export function ProviderSettings({ onClose }: Props) {
  const [activeTab, setActiveTab] = useState<'providers' | 'models' | 'agents'>('providers');
  const [providers, setProviders] = useState<Provider[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [settings, setSettings] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, 'success' | 'error' | null>>({});
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [keyInputs, setKeyInputs] = useState<Record<string, string>>({});
  const [error, setError] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [providersData, modelsData, settingsData] = await Promise.all([
        fetchProviders(),
        fetchAvailableModels(),
        fetchSettings()
      ]);
      
      setProviders(providersData.providers || []);
      setModels(modelsData.models || []);
      setSettings(settingsData || {});
    } catch (e) {
      setError('Failed to load settings');
      // Fallback data
      setProviders([
        { id: 'requesty', name: 'Requesty Router', has_key: false, key_env_var: 'REQUESTY_API_KEY' },
        { id: 'openai', name: 'OpenAI', has_key: false, key_env_var: 'OPENAI_API_KEY' },
        { id: 'anthropic', name: 'Anthropic', has_key: false, key_env_var: 'ANTHROPIC_API_KEY' },
        { id: 'zai', name: 'Z.AI', has_key: false, key_env_var: 'ZAI_API_KEY' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveKey = async (providerId: string) => {
    const key = keyInputs[providerId];
    if (!key?.trim()) return;

    try {
      setSaving(true);
      await updateApiKey(providerId, key.trim());
      setKeyInputs({ ...keyInputs, [providerId]: '' });
      setProviders(providers.map(p => 
        p.id === providerId ? { ...p, has_key: true } : p
      ));
      setTestResults({ ...testResults, [providerId]: null });
    } catch (e) {
      setError('Failed to save API key');
    } finally {
      setSaving(false);
    }
  };

  const handleTestKey = async (providerId: string) => {
    try {
      setTesting(providerId);
      const result = await testApiKey(providerId, keyInputs[providerId] || undefined);
      setTestResults({ ...testResults, [providerId]: result.success ? 'success' : 'error' });
    } catch (e) {
      setTestResults({ ...testResults, [providerId]: 'error' });
    } finally {
      setTesting(null);
    }
  };

  const handleUpdateSetting = async (key: string, value: any) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    
    try {
      await updateSettings({ [key]: value });
    } catch (e) {
      setError('Failed to save setting');
    }
  };

  // Helper to get the API source provider label for a model
  const getProviderLabel = (modelId: string): string => {
    if (!modelId) return '';
    // Find the model in our list to get its actual API provider
    const model = models.find(m => m.id === modelId);
    if (model?.provider) {
      const labels: Record<string, string> = {
        'requesty': 'Requesty',
        'zai': 'Z.AI',
        'openai': 'OpenAI Direct',
        'anthropic': 'Anthropic Direct',
        'fallback': 'Fallback',
      };
      return labels[model.provider] || model.provider;
    }
    return '';
  };

  // Helper to get the model vendor (for display in option text)
  const getModelVendor = (modelId: string): string => {
    if (!modelId) return '';
    if (modelId.includes('/')) {
      const vendor = modelId.split('/')[0].toLowerCase();
      const labels: Record<string, string> = {
        'anthropic': 'Anthropic',
        'openai': 'OpenAI',
        'google': 'Google',
        'meta': 'Meta',
        'mistral': 'Mistral',
        'cohere': 'Cohere',
        'deepseek': 'DeepSeek',
        'x-ai': 'xAI',
      };
      return labels[vendor] || vendor.charAt(0).toUpperCase() + vendor.slice(1);
    }
    // Z.AI GLM models
    if (modelId.startsWith('glm-')) return 'Z.AI';
    return '';
  };

  const getProviderColor = (provider: string): string => {
    const colors: Record<string, string> = {
      'Requesty': 'bg-purple-900/40 text-purple-300',
      'Z.AI': 'bg-cyan-900/40 text-cyan-300',
      'OpenAI Direct': 'bg-green-900/40 text-green-300',
      'Anthropic Direct': 'bg-orange-900/40 text-orange-300',
      'Fallback': 'bg-gray-700 text-gray-400',
    };
    return colors[provider] || 'bg-gray-700 text-gray-300';
  };

  const ModelSelect = ({ 
    settingKey, 
    label, 
    description 
  }: { 
    settingKey: string; 
    label: string; 
    description?: string;
  }) => {
    const currentValue = settings[settingKey] || '';
    const selectedProvider = getProviderLabel(currentValue);
    
    return (
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <label className="font-medium text-white">{label}</label>
          {selectedProvider && (
            <span className={`text-xs px-2 py-0.5 rounded ${getProviderColor(selectedProvider)}`}>
              {selectedProvider}
            </span>
          )}
        </div>
        {description && (
          <p className="text-xs text-gray-500 mb-2">{description}</p>
        )}
        <div className="relative">
          <select
            value={currentValue}
            onChange={(e) => handleUpdateSetting(settingKey, e.currentTarget.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white appearance-none focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Use default</option>
            {models.map((m) => {
              const vendor = getModelVendor(m.id);
              return (
                <option key={m.id} value={m.id}>
                  {vendor ? `${vendor}: ` : ''}{m.name || m.id}
                </option>
              );
            })}
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" size={16} />
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
        <div className="bg-gray-900 rounded-xl p-8">
          <Loader2 className="animate-spin text-blue-500 mx-auto" size={32} />
          <p className="text-gray-400 mt-4">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="p-4 border-b border-gray-800 flex items-center justify-between">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Server size={20} />
            Provider & Model Settings
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white p-2">
            <X size={20} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-800">
          {[
            { id: 'providers', label: 'API Keys', icon: Key },
            { id: 'models', label: 'Pipeline Models', icon: Sparkles },
            { id: 'agents', label: 'Agent Models', icon: Bot },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex-1 px-4 py-3 flex items-center justify-center gap-2 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-blue-400 border-b-2 border-blue-400 bg-blue-900/20'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              <tab.icon size={16} />
              {tab.label}
            </button>
          ))}
        </div>

        {error && (
          <div className="mx-4 mt-4 p-3 bg-red-900/30 border border-red-700 rounded-lg flex items-center gap-2 text-red-300 text-sm">
            <AlertCircle size={16} />
            {error}
            <button onClick={() => setError('')} className="ml-auto">×</button>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {activeTab === 'providers' && (
            <div className="space-y-4">
              <p className="text-gray-400 text-sm mb-4">
                Configure API keys for different providers. Keys are stored securely and used for AI model access.
              </p>
              
              {providers.map((provider) => (
                <div key={provider.id} className="bg-gray-800 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h3 className="font-medium text-white">{provider.name}</h3>
                      <p className="text-xs text-gray-500">{provider.key_env_var}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      {provider.has_key && (
                        <span className="text-xs bg-green-900/40 text-green-400 px-2 py-1 rounded flex items-center gap-1">
                          <Check size={12} />
                          Configured
                        </span>
                      )}
                      {testResults[provider.id] === 'success' && (
                        <span className="text-xs bg-green-900/40 text-green-400 px-2 py-1 rounded">
                          ✓ Working
                        </span>
                      )}
                      {testResults[provider.id] === 'error' && (
                        <span className="text-xs bg-red-900/40 text-red-400 px-2 py-1 rounded">
                          ✗ Failed
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex gap-2">
                    <div className="flex-1 relative">
                      <input
                        type={showKeys[provider.id] ? 'text' : 'password'}
                        value={keyInputs[provider.id] || ''}
                        onInput={(e) => setKeyInputs({ ...keyInputs, [provider.id]: e.currentTarget.value })}
                        placeholder={provider.has_key ? '••••••••••••••••' : 'Enter API key...'}
                        className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 pr-10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <button
                        onClick={() => setShowKeys({ ...showKeys, [provider.id]: !showKeys[provider.id] })}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                      >
                        {showKeys[provider.id] ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                    <button
                      onClick={() => handleTestKey(provider.id)}
                      disabled={testing === provider.id}
                      className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition-colors disabled:opacity-50"
                    >
                      {testing === provider.id ? (
                        <Loader2 className="animate-spin" size={16} />
                      ) : (
                        'Test'
                      )}
                    </button>
                    <button
                      onClick={() => handleSaveKey(provider.id)}
                      disabled={saving || !keyInputs[provider.id]?.trim()}
                      className="px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm transition-colors disabled:opacity-50"
                    >
                      Save
                    </button>
                  </div>
                </div>
              ))}

              <div className="mt-6 p-4 bg-gray-800/50 rounded-lg">
                <h4 className="font-medium text-white mb-2 flex items-center gap-2">
                  <RefreshCw size={16} />
                  Refresh Models
                </h4>
                <p className="text-xs text-gray-500 mb-3">
                  After adding or updating API keys, refresh to fetch available models from providers.
                </p>
                <button
                  onClick={loadData}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition-colors"
                >
                  Refresh Available Models
                </button>
              </div>
            </div>
          )}

          {activeTab === 'models' && (
            <div className="space-y-4">
              <p className="text-gray-400 text-sm mb-4">
                Configure which models to use for each stage of the Devussy pipeline.
              </p>
              
              <ModelSelect
                settingKey="devussy_model"
                label="Default Devussy Model"
                description="Used for all pipeline stages unless overridden"
              />
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <ModelSelect
                  settingKey="interview_model"
                  label="Interview Model"
                  description="For project requirement gathering"
                />
                <ModelSelect
                  settingKey="design_model"
                  label="Design Model"
                  description="For architecture and design generation"
                />
                <ModelSelect
                  settingKey="devplan_model"
                  label="DevPlan Model"
                  description="For task breakdown and planning"
                />
                <ModelSelect
                  settingKey="handoff_model"
                  label="Handoff Model"
                  description="For generating handoff documents"
                />
              </div>
            </div>
          )}

          {activeTab === 'agents' && (
            <div className="space-y-4">
              <p className="text-gray-400 text-sm mb-4">
                Configure which models each swarm agent uses. Leave empty to use the default swarm model.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <ModelSelect
                  settingKey="architect_model"
                  label="🏗️ Architect Model"
                  description="Bossy McArchitect - orchestration & planning"
                />
                <ModelSelect
                  settingKey="swarm_model"
                  label="🐝 Default Swarm Model"
                  description="Used by all worker agents unless overridden"
                />
              </div>

              <h4 className="font-medium text-white mt-6 mb-3">Worker Agent Models</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <ModelSelect
                  settingKey="agent_models.backend_dev"
                  label="⚙️ Backend Dev"
                  description="Codey McBackend"
                />
                <ModelSelect
                  settingKey="agent_models.frontend_dev"
                  label="🎨 Frontend Dev"
                  description="Pixel McFrontend"
                />
                <ModelSelect
                  settingKey="agent_models.qa_engineer"
                  label="🐛 QA Engineer"
                  description="Bugsy McTester"
                />
                <ModelSelect
                  settingKey="agent_models.devops"
                  label="🚀 DevOps"
                  description="Deployo McOps"
                />
                <ModelSelect
                  settingKey="agent_models.tech_writer"
                  label="📝 Tech Writer"
                  description="Docy McWriter"
                />
                <ModelSelect
                  settingKey="agent_models.database_specialist"
                  label="🗄️ Database Specialist"
                  description="Schema McDatabase"
                />
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
