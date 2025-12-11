import { useState, useRef, useEffect } from 'preact/hooks';
import { sendChat, forceStartDevplan } from '../lib/api';
import { 
  Send, User, Bot, AlertCircle, LayoutGrid, LayoutList, 
  ChevronLeft, ChevronRight, ChevronDown, ChevronUp,
  Zap, Play, Terminal, Hash, Clock
} from 'lucide-preact';

interface Props {
  messages: any[];
  agents: any[];
  tokenStats?: any;
}

export function ChatPanel({ messages, agents, tokenStats }: Props) {
  const [input, setInput] = useState('');
  const [splitView, setSplitView] = useState(true);
  const [collapsedColumns, setCollapsedColumns] = useState<Set<string>>(new Set());
  const [expandedMessages, setExpandedMessages] = useState<Set<string>>(new Set());
  const [forceStarting, setForceStarting] = useState(false);
  const [forceError, setForceError] = useState<string | null>(null);
  const [goRunning, setGoRunning] = useState(false);
  const [showSystemConsole, setShowSystemConsole] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  const toggleColumn = (title: string) => {
    setCollapsedColumns(prev => {
      const next = new Set(prev);
      if (next.has(title)) next.delete(title);
      else next.add(title);
      return next;
    });
  };

  const toggleMessage = (msgId: string) => {
    setExpandedMessages(prev => {
      const next = new Set(prev);
      if (next.has(msgId)) next.delete(msgId);
      else next.add(msgId);
      return next;
    });
  };

  // Get system/console messages
  const getSystemMessages = () => {
    return messages.filter(m => 
      m.role === 'system' || m.sender_name === 'System'
    );
  };

  // Get orchestrator + user messages only (not system, not worker agents)
  const getOrchestratorMessages = () => {
    return messages.filter(m => {
      // User messages
      if (['human', 'user'].includes(m.role) || m.sender_name === 'You') return true;
      
      // Architect and Manager only
      if (['Bossy McArchitect', 'Checky McManager'].includes(m.sender_name)) return true;
      
      // Auto Orchestrator messages
      if (m.sender_name === 'Auto Orchestrator') return true;

      return false;
    });
  };

  // Group messages for split view - agent specific
  const getAgentMessages = (agentName: string) => {
    return messages.filter(m => {
      if (m.sender_name === agentName) {
        if (agentName === "Bossy McArchitect") return false; 
        return true;
      }
      if (m.sender_name === "System" && (m.content || "").startsWith(agentName + ":")) {
        return true;
      }
      return false;
    });
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, splitView]);

  const handleForceStart = async () => {
    try {
      setForceError(null);
      setForceStarting(true);
      await forceStartDevplan();
    } catch (e: any) {
      console.error('Force start failed', e);
      setForceError(e.message || 'Failed to force start swarm');
    } finally {
      setForceStarting(false);
    }
  };

  const handleGo = async () => {
    try {
      setGoRunning(true);
      await sendChat('go');
    } catch (e) {
      console.error('Go command failed', e);
    } finally {
      setGoRunning(false);
    }
  };

  const handleSubmit = async (e: any) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    const msg = input;
    setInput('');
    try {
      await sendChat(msg);
    } catch (err) {
      console.error(err);
      setInput(msg);
    }
  };

  const getAgentColor = (name: string) => {
    const colors: Record<string, string> = {
      'Bossy McArchitect': 'text-purple-400',
      'Codey McBackend': 'text-blue-400',
      'Pixel McFrontend': 'text-pink-400',
      'Bugsy McTester': 'text-green-400',
      'Deployo McOps': 'text-yellow-400',
      'Checky McManager': 'text-cyan-400',
      'Docy McWriter': 'text-red-400',
      'Auto Orchestrator': 'text-orange-400',
      'You': 'text-blue-300'
    };
    return colors[name] || 'text-theme-secondary';
  };

  const getAgentBgColor = (name: string) => {
    const colors: Record<string, string> = {
      'Bossy McArchitect': 'border-purple-500/30 bg-purple-900/10',
      'Codey McBackend': 'border-blue-500/30 bg-blue-900/10',
      'Pixel McFrontend': 'border-pink-500/30 bg-pink-900/10',
      'Bugsy McTester': 'border-green-500/30 bg-green-900/10',
      'Deployo McOps': 'border-yellow-500/30 bg-yellow-900/10',
      'Checky McManager': 'border-cyan-500/30 bg-cyan-900/10',
      'Docy McWriter': 'border-red-500/30 bg-red-900/10'
    };
    return colors[name] || 'border-theme bg-theme-tertiary';
  };

  // Enhanced message bubble with token info and expandable content
  const MessageBubble = ({ msg, showTokens = true }: { msg: any, showTokens?: boolean }) => {
    const isUser = ['human', 'user'].includes(msg.role) || msg.sender_name === 'You';
    const isExpanded = expandedMessages.has(msg.id);
    const content = msg.content || '';
    const isLong = content.length > 300;
    const displayContent = isLong && !isExpanded ? content.slice(0, 300) + '...' : content;
    
    // Token info from message metadata
    const inputTokens = msg.input_tokens || msg.prompt_tokens || 0;
    const outputTokens = msg.output_tokens || msg.completion_tokens || 0;
    const totalTokens = inputTokens + outputTokens;

    return (
      <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
        <div className={`max-w-[95%] rounded-lg overflow-hidden ${
          isUser 
            ? 'bg-blue-600 text-white border border-blue-500' 
            : msg.role === 'system'
            ? 'bg-theme-tertiary/50 text-theme-muted border border-theme text-sm'
            : msg.role === 'tool'
            ? 'bg-black/30 text-theme-secondary border border-theme font-mono text-xs'
            : `${getAgentBgColor(msg.sender_name)} border`
        }`}>
          {/* Header */}
          <div className="px-3 py-1.5 flex items-center justify-between gap-3 border-b border-white/10">
            <div className="flex items-center gap-2">
              <span className={`text-xs font-bold ${isUser ? 'text-blue-200' : getAgentColor(msg.sender_name)}`}>
                {msg.sender_name}
              </span>
              <span className="text-[10px] text-theme-muted flex items-center gap-1">
                <Clock size={10} />
                {new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'})}
              </span>
            </div>
            {showTokens && totalTokens > 0 && (
              <span className="text-[10px] text-yellow-400/70 flex items-center gap-1 bg-yellow-900/20 px-1.5 py-0.5 rounded">
                <Hash size={10} />
                {totalTokens.toLocaleString()} tok
              </span>
            )}
          </div>
          
          {/* Content */}
          <div className="px-3 py-2">
            <div className="whitespace-pre-wrap font-mono text-xs break-words">
              {displayContent}
            </div>
            
            {/* Expand/Collapse for long messages */}
            {isLong && (
              <button
                onClick={() => toggleMessage(msg.id)}
                className="mt-2 flex items-center gap-1 text-[10px] text-theme-muted hover:text-theme-primary transition-colors"
              >
                {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                {isExpanded ? 'Show less' : `Show more (${content.length} chars)`}
              </button>
            )}
          </div>

          {/* Expanded details */}
          {isExpanded && (
            <div className="px-3 py-2 border-t border-white/10 bg-black/20 text-[10px] text-theme-muted space-y-1">
              <div className="flex gap-4">
                <span>Role: {msg.role}</span>
                {inputTokens > 0 && <span>Input: {inputTokens.toLocaleString()}</span>}
                {outputTokens > 0 && <span>Output: {outputTokens.toLocaleString()}</span>}
              </div>
              {msg.tool_calls && (
                <div>Tool calls: {msg.tool_calls.length}</div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  // System Console Column
  const SystemConsoleColumn = () => {
    const listRef = useRef<HTMLDivElement>(null);
    const systemMsgs = getSystemMessages();
    const isCollapsed = !showSystemConsole;

    useEffect(() => {
      if (listRef.current && !isCollapsed) {
        listRef.current.scrollTop = listRef.current.scrollHeight;
      }
    }, [systemMsgs, isCollapsed]);

    if (isCollapsed) {
      return (
        <div className="flex flex-col h-full w-12 border-r border-theme bg-theme-secondary items-center py-2 transition-all duration-300 flex-shrink-0">
          <button 
            onClick={() => setShowSystemConsole(true)}
            className="p-2 text-theme-muted hover:text-theme-primary hover:bg-theme-tertiary rounded mb-4"
            title="Expand System Console"
          >
            <ChevronRight size={20} />
          </button>
          <div className="flex-1 w-full flex justify-center overflow-hidden">
            <div 
              className="text-theme-muted font-bold text-xs tracking-wider whitespace-nowrap flex items-center gap-1" 
              style={{ writingMode: 'vertical-rl', textOrientation: 'mixed' }}
            >
              <Terminal size={12} />
              System
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="flex flex-col h-full w-72 border-r border-theme transition-all duration-300 flex-shrink-0 bg-black/40">
        <div className="p-2 border-b border-theme bg-theme-tertiary/50 font-bold text-theme-secondary text-sm flex justify-between items-center">
          <div className="flex items-center gap-2">
            <button 
              onClick={() => setShowSystemConsole(false)}
              className="p-1 text-theme-muted hover:text-theme-primary hover:bg-theme-tertiary rounded transition-colors"
            >
              <ChevronLeft size={16} />
            </button>
            <Terminal size={16} className="text-green-400" />
            <span>System Console</span>
          </div>
          <span className="text-xs text-theme-muted">{systemMsgs.length}</span>
        </div>
        <div ref={listRef} className="flex-1 overflow-y-auto p-2 space-y-1 font-mono text-xs">
          {systemMsgs.length === 0 ? (
            <div className="text-theme-muted text-center py-4 italic">No system output</div>
          ) : (
            systemMsgs.map((msg) => (
              <div key={msg.id} className="p-1.5 rounded bg-theme-tertiary/30 border border-theme/50 hover:bg-theme-tertiary/50 transition-colors">
                <div className="flex items-center gap-2 text-[10px] text-theme-muted mb-0.5">
                  <span>{new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'})}</span>
                </div>
                <div className="text-theme-secondary break-all">
                  {(msg.content || '').slice(0, 200)}
                  {(msg.content || '').length > 200 && '...'}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    );
  };

  const MessageList = ({ msgs, title, isMain = false }: { msgs: any[], title: string, isMain?: boolean }) => {
    const listRef = useRef<HTMLDivElement>(null);
    const isCollapsed = collapsedColumns.has(title);
    const [shouldScroll, setShouldScroll] = useState(true);

    useEffect(() => {
      const el = listRef.current;
      if (!el) return;
      const handleScroll = () => {
        const { scrollTop, scrollHeight, clientHeight } = el;
        setShouldScroll(scrollHeight - scrollTop - clientHeight < 50);
      };
      el.addEventListener('scroll', handleScroll);
      return () => el.removeEventListener('scroll', handleScroll);
    }, []);

    useEffect(() => {
      if (!isCollapsed && shouldScroll && listRef.current) {
        listRef.current.scrollTop = listRef.current.scrollHeight;
      }
    }, [msgs, isCollapsed, shouldScroll]);

    if (isCollapsed) {
      return (
        <div className="flex flex-col h-full w-12 border-r border-theme bg-theme-secondary items-center py-2 transition-all duration-300 flex-shrink-0">
          <button 
            onClick={() => toggleColumn(title)}
            className="p-2 text-theme-muted hover:text-theme-primary hover:bg-theme-tertiary rounded mb-4"
          >
            <ChevronRight size={20} />
          </button>
          <div className="flex-1 w-full flex justify-center overflow-hidden">
            <div 
              className={`font-bold text-xs tracking-wider whitespace-nowrap ${getAgentColor(title.split(' ')[0])}`}
              style={{ writingMode: 'vertical-rl', textOrientation: 'mixed' }}
            >
              {title}
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className={`flex flex-col h-full border-r border-theme last:border-r-0 transition-all duration-300 flex-shrink-0 ${
        isMain ? 'min-w-[400px] flex-1' : 'min-w-[320px] max-w-[500px]'
      }`}>
        <div className="p-2 border-b border-theme bg-theme-secondary font-bold text-theme-secondary text-sm flex justify-between items-center sticky top-0 z-10">
          <div className="flex items-center gap-2">
            <button 
              onClick={() => toggleColumn(title)}
              className="p-1 text-theme-muted hover:text-theme-primary hover:bg-theme-tertiary rounded transition-colors"
            >
              <ChevronLeft size={16} />
            </button>
            <span className={getAgentColor(title.split(' ')[0])}>{title}</span>
          </div>
          {tokenStats?.by_agent?.[title] && (
            <span className="text-xs text-yellow-500/70 font-mono bg-yellow-900/20 px-2 py-0.5 rounded">
              {(tokenStats.by_agent[title].total || 0).toLocaleString()} t
            </span>
          )}
        </div>
        <div ref={listRef} className="flex-1 overflow-y-auto p-3 space-y-3 bg-theme-primary/30">
          {msgs.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-theme-muted text-sm italic">
              <span>No messages yet</span>
            </div>
          ) : (
            msgs.map((msg) => (
              <MessageBubble key={msg.id} msg={msg} />
            ))
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-theme-secondary border-r border-theme">
      {/* Header */}
      <div className="p-2 border-b border-theme flex justify-between items-center bg-theme-secondary">
        <div className="flex items-center gap-4">
          <h2 className="text-sm font-bold text-theme-muted px-2">
            {splitView ? 'Swarm Grid View' : 'Unified Chat'}
          </h2>
          {tokenStats?.total_tokens && (
            <span className="text-xs text-yellow-500 font-mono bg-yellow-900/20 px-2 py-1 rounded border border-yellow-900/30">
              Total: {tokenStats.total_tokens.toLocaleString()} toks
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {forceError && (
            <div className="flex items-center gap-1 text-xs text-red-400 mr-2">
              <AlertCircle size={14} />
              <span>{forceError}</span>
            </div>
          )}
          <button
            type="button"
            onClick={handleGo}
            disabled={goRunning}
            className={`px-2 py-1 text-xs rounded border transition-colors flex items-center gap-1 ${
              goRunning
                ? 'border-blue-500 text-blue-300 bg-blue-900/30 cursor-wait'
                : 'border-green-500 text-green-300 hover:bg-green-900/30'
            }`}
            title="Dispatch next task batch"
          >
            <Play size={14} />
            {goRunning ? 'Running...' : 'Go'}
          </button>
          <button
            type="button"
            onClick={handleForceStart}
            disabled={forceStarting}
            className={`px-2 py-1 text-xs rounded border transition-colors flex items-center gap-1 ${
              forceStarting
                ? 'border-blue-500 text-blue-300 bg-blue-900/30 cursor-wait'
                : 'border-purple-500 text-purple-300 hover:bg-purple-900/30'
            }`}
            title="Force restart swarm"
          >
            <Zap size={14} />
            {forceStarting ? 'Starting...' : 'Force Start'}
          </button>
          <button
            onClick={() => setSplitView(!splitView)}
            className="p-2 text-theme-muted hover:text-theme-primary hover:bg-theme-tertiary rounded transition-colors"
            title={splitView ? "Unified View" : "Split View"}
          >
            {splitView ? <LayoutList size={18} /> : <LayoutGrid size={18} />}
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-hidden relative">
        {splitView ? (
          <div className="absolute inset-0 flex overflow-x-auto">
            {/* System Console Column */}
            <SystemConsoleColumn />
            
            {/* Main Orchestrator Column */}
            <MessageList msgs={getOrchestratorMessages()} title="Orchestrator & User" isMain={true} />
            
            {/* Worker Agent Columns */}
            {agents.filter(a => !['Bossy McArchitect', 'Checky McManager'].includes(a.name)).map(agent => (
              <MessageList 
                key={agent.agent_id} 
                msgs={getAgentMessages(agent.name)} 
                title={agent.name} 
              />
            ))}
          </div>
        ) : (
          <div className="h-full overflow-y-auto p-4 space-y-4">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} msg={msg} />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>
      
      <form onSubmit={handleSubmit} className="p-3 bg-theme-secondary border-t border-theme">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onInput={(e) => setInput(e.currentTarget.value)}
            placeholder="Type a message or /command..."
            className="flex-1 bg-theme-tertiary text-theme-primary rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-theme-accent border border-theme"
          />
          <button 
            type="submit"
            className="bg-theme-accent hover:bg-theme-accent-hover text-white rounded-lg p-2 transition-colors"
          >
            <Send size={20} />
          </button>
        </div>
      </form>
    </div>
  );
}
