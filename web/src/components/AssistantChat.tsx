import { useState, useRef, useEffect } from 'preact/hooks';
import { 
  MessageCircle, Send, X, Minimize2, Maximize2, 
  Sparkles, FileText, RefreshCw, Bot, User,
  ChevronDown, Loader2
} from 'lucide-preact';
import { sendAssistantChat } from '../lib/api';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface Props {
  projectName: string;
  onClose: () => void;
}

export function AssistantChat({ projectName, onClose }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: `Hi! I'm your project assistant for **${projectName}**. I have access to the devplan, phases, and task structure.

I can help you:
- Answer questions about the project
- Review and explain tasks
- Suggest improvements to phases
- Request task re-dos or iterations
- Make adjustments to the plan

What would you like to know or change?`,
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [minimized, setMinimized] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const messagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await sendAssistantChat(input.trim());
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.message || response.response || 'I apologize, I encountered an issue processing that request.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (e: any) {
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ Error: ${e.message || 'Failed to get response'}. Please try again.`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const quickActions = [
    { label: 'Show current phase', prompt: 'What phase are we currently on and what tasks are remaining?' },
    { label: 'List blockers', prompt: 'Are there any blocked tasks? What are the blockers?' },
    { label: 'Summarize progress', prompt: 'Give me a brief summary of the project progress so far.' },
    { label: 'Next priorities', prompt: 'What should be the next priorities for the team?' },
  ];

  // Minimized state
  if (minimized) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={() => setMinimized(false)}
          className="bg-purple-600 hover:bg-purple-700 text-white rounded-full p-4 shadow-lg transition-all hover:scale-105"
        >
          <MessageCircle size={24} />
        </button>
      </div>
    );
  }

  return (
    <div 
      className={`fixed z-50 bg-theme-secondary border border-theme rounded-xl shadow-2xl flex flex-col transition-all duration-300 ${
        expanded 
          ? 'inset-4'
          : 'bottom-4 right-4 w-[400px] h-[600px]'
      }`}
    >
      {/* Header */}
      <div className="p-3 border-b border-theme bg-gradient-to-r from-purple-900/40 to-theme-secondary rounded-t-xl flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-purple-600 flex items-center justify-center">
            <Sparkles size={18} className="text-white" />
          </div>
          <div>
            <h3 className="font-bold text-theme-primary text-sm">Project Assistant</h3>
            <p className="text-xs text-purple-400">{projectName}</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-2 text-theme-muted hover:text-theme-primary hover:bg-theme-tertiary rounded-lg transition-colors"
            title={expanded ? 'Shrink' : 'Expand'}
          >
            {expanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
          </button>
          <button
            onClick={() => setMinimized(true)}
            className="p-2 text-theme-muted hover:text-theme-primary hover:bg-theme-tertiary rounded-lg transition-colors"
            title="Minimize"
          >
            <ChevronDown size={16} />
          </button>
          <button
            onClick={onClose}
            className="p-2 text-theme-muted hover:text-red-400 hover:bg-red-900/20 rounded-lg transition-colors"
            title="Close"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="p-2 border-b border-theme bg-theme-tertiary/30 flex gap-1.5 overflow-x-auto">
        {quickActions.map((action, i) => (
          <button
            key={i}
            onClick={() => {
              setInput(action.prompt);
            }}
            className="px-2 py-1 text-xs bg-theme-tertiary hover:bg-purple-900/30 text-theme-muted hover:text-purple-300 rounded-lg whitespace-nowrap transition-colors border border-theme"
          >
            {action.label}
          </button>
        ))}
      </div>

      {/* Messages */}
      <div 
        ref={messagesRef}
        className="flex-1 overflow-y-auto p-4 space-y-4"
      >
        {messages.map(msg => (
          <div 
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`max-w-[85%] flex gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${
                msg.role === 'user' 
                  ? 'bg-blue-600' 
                  : 'bg-purple-600'
              }`}>
                {msg.role === 'user' ? <User size={14} /> : <Bot size={14} />}
              </div>
              <div className={`rounded-xl px-3 py-2 ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-theme-tertiary text-theme-secondary border border-theme'
              }`}>
                <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                <div className={`text-[10px] mt-1 ${
                  msg.role === 'user' ? 'text-blue-200' : 'text-theme-muted'
                }`}>
                  {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="flex gap-2">
              <div className="w-7 h-7 rounded-lg bg-purple-600 flex items-center justify-center flex-shrink-0">
                <Bot size={14} />
              </div>
              <div className="bg-theme-tertiary rounded-xl px-4 py-3 border border-theme">
                <Loader2 size={16} className="animate-spin text-purple-400" />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-3 border-t border-theme bg-theme-tertiary/30">
        <div className="flex gap-2">
          <textarea
            value={input}
            onInput={(e) => setInput(e.currentTarget.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about the project or request changes..."
            rows={2}
            className="flex-1 bg-theme-tertiary border border-theme rounded-lg px-3 py-2 text-theme-primary text-sm resize-none focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="px-4 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center justify-center"
          >
            <Send size={18} />
          </button>
        </div>
        <div className="text-[10px] text-theme-muted mt-1.5 flex items-center gap-1">
          <FileText size={10} />
          Has access to devplan, phases, and task state
        </div>
      </div>
    </div>
  );
}
