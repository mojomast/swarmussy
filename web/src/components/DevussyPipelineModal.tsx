import { useState, useEffect, useRef } from 'preact/hooks';
import { 
  startDevussyPipeline, 
  sendDevussyMessage, 
  fetchAvailableModels,
  fetchDevussyStatus 
} from '../lib/api';
import { 
  X, 
  Send, 
  Sparkles, 
  MessageSquare, 
  CheckCircle2, 
  Circle, 
  Loader2,
  ChevronDown,
  Bot
} from 'lucide-preact';

interface Props {
  onClose: () => void;
  onComplete: () => void;
  projectName: string;
}

interface PipelineStage {
  id: string;
  name: string;
  status: 'pending' | 'active' | 'complete';
}

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

export function DevussyPipelineModal({ onClose, onComplete, projectName }: Props) {
  const [stage, setStage] = useState<'config' | 'interview' | 'processing' | 'complete'>('config');
  const [models, setModels] = useState<{ id: string; name: string; provider?: string }[]>([]);
  const [loadingModels, setLoadingModels] = useState(true);
  
  // Model configuration
  const [interviewModel, setInterviewModel] = useState('');
  const [designModel, setDesignModel] = useState('');
  const [devplanModel, setDevplanModel] = useState('');
  
  // Interview state
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [pipelineStages, setPipelineStages] = useState<PipelineStage[]>([
    { id: 'interview', name: 'Project Interview', status: 'pending' },
    { id: 'design', name: 'Design Generation', status: 'pending' },
    { id: 'devplan', name: 'DevPlan Creation', status: 'pending' },
    { id: 'phases', name: 'Phase Breakdown', status: 'pending' },
    { id: 'handoff', name: 'Handoff Document', status: 'pending' },
  ]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    loadModels();
    return () => {
      wsRef.current?.close();
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadModels = async () => {
    try {
      setLoadingModels(true);
      const data = await fetchAvailableModels();
      setModels(data.models || []);
      
      // Set defaults
      if (data.models?.length > 0) {
        const defaultModel = data.models.find((m: any) => 
          m.id.includes('claude-sonnet') || m.id.includes('gpt-4o')
        )?.id || data.models[0].id;
        
        setInterviewModel(defaultModel);
        setDesignModel(defaultModel);
        setDevplanModel(defaultModel);
      }
    } catch (e) {
      console.error('Failed to load models', e);
      // Fallback models
      setModels([
        { id: 'anthropic/claude-sonnet-4-20250514', name: 'Claude Sonnet 4' },
        { id: 'openai/gpt-4o', name: 'GPT-4o' },
        { id: 'openai/gpt-4o-mini', name: 'GPT-4o Mini' },
      ]);
      setInterviewModel('anthropic/claude-sonnet-4-20250514');
      setDesignModel('anthropic/claude-sonnet-4-20250514');
      setDevplanModel('anthropic/claude-sonnet-4-20250514');
    } finally {
      setLoadingModels(false);
    }
  };

  const connectWebSocket = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/devussy`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'message') {
        setMessages(prev => [...prev, {
          role: data.role || 'assistant',
          content: data.content,
          timestamp: new Date()
        }]);
      } else if (data.type === 'stage_update') {
        setPipelineStages(prev => prev.map(s => 
          s.id === data.stage_id ? { ...s, status: data.status } : s
        ));
        
        if (data.stage_id === 'interview' && data.status === 'complete') {
          setStage('processing');
        }
      } else if (data.type === 'complete') {
        setStage('complete');
        setPipelineStages(prev => prev.map(s => ({ ...s, status: 'complete' })));
      } else if (data.type === 'error') {
        setMessages(prev => [...prev, {
          role: 'system',
          content: `Error: ${data.message}`,
          timestamp: new Date()
        }]);
      }
    };
    
    ws.onerror = () => {
      setMessages(prev => [...prev, {
        role: 'system',
        content: 'Connection error. Please try again.',
        timestamp: new Date()
      }]);
    };
    
    wsRef.current = ws;
  };

  const handleStartPipeline = async () => {
    try {
      setStage('interview');
      setPipelineStages(prev => prev.map((s, i) => 
        i === 0 ? { ...s, status: 'active' } : s
      ));
      
      // Connect WebSocket for real-time updates
      connectWebSocket();
      
      // Start the pipeline
      await startDevussyPipeline({
        interview_model: interviewModel,
        design_model: designModel,
        devplan_model: devplanModel,
      });
      
      // Add initial message
      setMessages([{
        role: 'assistant',
        content: `Welcome to the Devussy Pipeline! I'll help you define your project "${projectName}". Let's start with some questions about what you want to build.\n\nWhat kind of project are you building? (e.g., web app, CLI tool, game, API service)`,
        timestamp: new Date()
      }]);
    } catch (e) {
      console.error('Failed to start pipeline', e);
      setMessages([{
        role: 'system',
        content: 'Failed to start pipeline. Please check your API configuration.',
        timestamp: new Date()
      }]);
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() || sending) return;
    
    const userMessage = input.trim();
    setInput('');
    setSending(true);
    
    setMessages(prev => [...prev, {
      role: 'user',
      content: userMessage,
      timestamp: new Date()
    }]);
    
    try {
      await sendDevussyMessage(userMessage);
    } catch (e) {
      setMessages(prev => [...prev, {
        role: 'system',
        content: 'Failed to send message. Please try again.',
        timestamp: new Date()
      }]);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Helper to get the API source provider label for a model
  const getProviderLabel = (modelId: string): string => {
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
    return 'Unknown';
  };

  // Helper to get the model vendor (for display in option text)
  const getModelVendor = (modelId: string): string => {
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

  const ModelSelect = ({ value, onChange, label }: { value: string; onChange: (v: string) => void; label: string }) => {
    const selectedProvider = getProviderLabel(value);
    
    return (
      <div>
        <label className="block text-sm text-gray-400 mb-1">{label}</label>
        <div className="relative">
          <select
            value={value}
            onChange={(e) => onChange(e.currentTarget.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 pr-10 text-white appearance-none focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
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
        <div className="mt-1">
          <span className={`text-xs px-2 py-0.5 rounded ${getProviderColor(selectedProvider)}`}>
            {selectedProvider}
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="p-4 border-b border-gray-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Sparkles className="text-purple-400" size={24} />
            <div>
              <h2 className="text-lg font-bold text-white">Devussy Pipeline</h2>
              <p className="text-sm text-gray-400">Project: {projectName}</p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="text-gray-400 hover:text-white p-2 rounded-lg hover:bg-gray-800 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="px-4 py-3 border-b border-gray-800 bg-gray-900/50">
          <div className="flex items-center gap-2 overflow-x-auto">
            {pipelineStages.map((s, i) => (
              <div key={s.id} className="flex items-center">
                <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs whitespace-nowrap ${
                  s.status === 'complete' ? 'bg-green-900/40 text-green-300' :
                  s.status === 'active' ? 'bg-blue-900/40 text-blue-300' :
                  'bg-gray-800 text-gray-500'
                }`}>
                  {s.status === 'complete' ? <CheckCircle2 size={14} /> :
                   s.status === 'active' ? <Loader2 size={14} className="animate-spin" /> :
                   <Circle size={14} />}
                  {s.name}
                </div>
                {i < pipelineStages.length - 1 && (
                  <div className={`w-4 h-0.5 mx-1 ${
                    s.status === 'complete' ? 'bg-green-600' : 'bg-gray-700'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden flex flex-col">
          {stage === 'config' && (
            <div className="p-6 space-y-6">
              <div>
                <h3 className="text-lg font-bold text-white mb-2">Configure Pipeline Models</h3>
                <p className="text-gray-400 text-sm">
                  Select which AI models to use for each stage of the pipeline. 
                  More capable models produce better results but cost more.
                </p>
              </div>

              {loadingModels ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="animate-spin text-blue-500" size={32} />
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <ModelSelect 
                    label="Interview Model" 
                    value={interviewModel} 
                    onChange={setInterviewModel} 
                  />
                  <ModelSelect 
                    label="Design Model" 
                    value={designModel} 
                    onChange={setDesignModel} 
                  />
                  <ModelSelect 
                    label="DevPlan Model" 
                    value={devplanModel} 
                    onChange={setDevplanModel} 
                  />
                </div>
              )}

              <div className="bg-gray-800/50 rounded-lg p-4 text-sm text-gray-400">
                <p className="font-medium text-gray-300 mb-2">💡 What happens next:</p>
                <ol className="list-decimal list-inside space-y-1">
                  <li>Interactive interview about your project requirements</li>
                  <li>AI generates a comprehensive project design</li>
                  <li>DevPlan with phases and tasks is created</li>
                  <li>Tasks are assigned to swarm agents</li>
                  <li>Handoff document prepared for execution</li>
                </ol>
              </div>

              <button
                onClick={handleStartPipeline}
                disabled={loadingModels}
                className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 disabled:opacity-50 text-white font-bold py-3 px-4 rounded-lg transition-all flex items-center justify-center gap-2"
              >
                <Sparkles size={20} />
                Start Pipeline Interview
              </button>
            </div>
          )}

          {(stage === 'interview' || stage === 'processing') && (
            <>
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] rounded-lg p-3 ${
                      msg.role === 'user' 
                        ? 'bg-blue-600 text-white' 
                        : msg.role === 'system'
                        ? 'bg-yellow-900/30 text-yellow-300 border border-yellow-800'
                        : 'bg-gray-800 text-gray-200 border border-gray-700'
                    }`}>
                      {msg.role === 'assistant' && (
                        <div className="flex items-center gap-2 mb-2 text-purple-400 text-xs font-medium">
                          <Bot size={14} />
                          Devussy
                        </div>
                      )}
                      <div className="whitespace-pre-wrap text-sm">{msg.content}</div>
                    </div>
                  </div>
                ))}
                
                {stage === 'processing' && (
                  <div className="flex justify-start">
                    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                      <div className="flex items-center gap-3">
                        <Loader2 className="animate-spin text-purple-400" size={20} />
                        <span className="text-gray-300">Generating project artifacts...</span>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              {stage === 'interview' && (
                <div className="p-4 border-t border-gray-800">
                  <div className="flex gap-2">
                    <textarea
                      value={input}
                      onInput={(e) => setInput(e.currentTarget.value)}
                      onKeyDown={handleKeyDown}
                      placeholder="Type your response..."
                      rows={2}
                      className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <button
                      onClick={handleSendMessage}
                      disabled={sending || !input.trim()}
                      className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white p-3 rounded-lg transition-colors"
                    >
                      {sending ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
                    </button>
                  </div>
                </div>
              )}
            </>
          )}

          {stage === 'complete' && (
            <div className="p-6 text-center">
              <div className="w-16 h-16 bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle2 className="text-green-400" size={32} />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Pipeline Complete!</h3>
              <p className="text-gray-400 mb-6">
                Your project has been designed and the devplan is ready. 
                The swarm agents can now start working on your project.
              </p>
              <div className="flex gap-4 justify-center">
                <button
                  onClick={onClose}
                  className="px-6 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                >
                  Close
                </button>
                <button
                  onClick={onComplete}
                  className="px-6 py-2 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white font-bold rounded-lg transition-all"
                >
                  Start Swarm Execution
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
