import { useState, useRef, useEffect } from 'preact/hooks';
import { Terminal, ChevronLeft, ChevronRight, Trash2, Download, Filter } from 'lucide-preact';

interface ConsoleMessage {
  id: string;
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'debug';
  source: string;
  message: string;
}

interface Props {
  messages: any[];
  collapsed?: boolean;
  onToggle?: () => void;
}

export function SystemConsole({ messages, collapsed = false, onToggle }: Props) {
  const [filter, setFilter] = useState<'all' | 'info' | 'warn' | 'error'>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const consoleRef = useRef<HTMLDivElement>(null);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);

  // Parse messages into console format
  const consoleMessages: ConsoleMessage[] = messages
    .filter(m => m.role === 'system' || m.sender_name === 'System')
    .map(m => {
      const content = m.content || '';
      let level: ConsoleMessage['level'] = 'info';
      let source = 'System';

      // Parse source from content like "Agent: action..."
      const sourceMatch = content.match(/^([^:]+):/);
      if (sourceMatch) {
        source = sourceMatch[1];
      }

      // Detect level from content
      if (content.toLowerCase().includes('error') || content.toLowerCase().includes('failed')) {
        level = 'error';
      } else if (content.toLowerCase().includes('warning') || content.toLowerCase().includes('warn')) {
        level = 'warn';
      } else if (content.toLowerCase().includes('debug')) {
        level = 'debug';
      }

      return {
        id: m.id || `${m.timestamp}-${Math.random()}`,
        timestamp: m.timestamp,
        level,
        source,
        message: content
      };
    });

  // Filter messages
  const filteredMessages = consoleMessages.filter(m => {
    if (filter !== 'all' && m.level !== filter) return false;
    if (searchTerm && !m.message.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  // Auto-scroll handling
  useEffect(() => {
    const el = consoleRef.current;
    if (!el) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = el;
      setShouldAutoScroll(scrollHeight - scrollTop - clientHeight < 50);
    };

    el.addEventListener('scroll', handleScroll);
    return () => el.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    if (shouldAutoScroll && consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [filteredMessages, shouldAutoScroll]);

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'error': return 'text-red-400';
      case 'warn': return 'text-yellow-400';
      case 'debug': return 'text-gray-500';
      default: return 'text-gray-300';
    }
  };

  const getLevelBadge = (level: string) => {
    switch (level) {
      case 'error': return 'bg-red-900/40 text-red-400 border-red-500/30';
      case 'warn': return 'bg-yellow-900/40 text-yellow-400 border-yellow-500/30';
      case 'debug': return 'bg-gray-800 text-gray-500 border-gray-600';
      default: return 'bg-blue-900/40 text-blue-400 border-blue-500/30';
    }
  };

  const handleExport = () => {
    const content = filteredMessages
      .map(m => `[${new Date(m.timestamp).toISOString()}] [${m.level.toUpperCase()}] ${m.source}: ${m.message}`)
      .join('\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `console-${new Date().toISOString().slice(0, 10)}.log`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Collapsed state
  if (collapsed) {
    return (
      <div className="flex flex-col h-full w-14 bg-theme-secondary border-r border-theme items-center py-2 transition-all duration-300">
        <button 
          onClick={onToggle}
          className="p-2 text-theme-muted hover:text-theme-primary hover:bg-theme-tertiary rounded transition-colors mb-4"
          title="Expand Console"
        >
          <ChevronRight size={20} />
        </button>
        <div className="flex-1 w-full flex justify-center overflow-hidden">
          <div 
            className="text-theme-muted font-bold text-xs tracking-wider whitespace-nowrap flex items-center gap-1" 
            style={{ writingMode: 'vertical-rl', textOrientation: 'mixed' }}
          >
            <Terminal size={12} />
            Console
          </div>
        </div>
        {/* Error count badge */}
        {consoleMessages.filter(m => m.level === 'error').length > 0 && (
          <div className="w-6 h-6 rounded-full bg-red-600 text-white text-xs flex items-center justify-center font-bold mb-2">
            {consoleMessages.filter(m => m.level === 'error').length}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full w-80 bg-theme-secondary border-r border-theme transition-all duration-300">
      {/* Header */}
      <div className="p-3 border-b border-theme bg-theme-tertiary/50">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <button 
              onClick={onToggle}
              className="p-1 text-theme-muted hover:text-theme-primary hover:bg-theme-tertiary rounded transition-colors"
              title="Collapse Console"
            >
              <ChevronLeft size={16} />
            </button>
            <Terminal size={16} className="text-green-400" />
            <span className="font-bold text-theme-primary text-sm">System Console</span>
          </div>
          <div className="flex items-center gap-1">
            <button 
              onClick={handleExport}
              className="p-1.5 text-theme-muted hover:text-theme-primary hover:bg-theme-tertiary rounded transition-colors"
              title="Export Logs"
            >
              <Download size={14} />
            </button>
          </div>
        </div>

        {/* Filter buttons */}
        <div className="flex items-center gap-1">
          {(['all', 'info', 'warn', 'error'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-2 py-0.5 text-xs rounded transition-colors ${
                filter === f 
                  ? 'bg-theme-accent text-white' 
                  : 'bg-theme-tertiary text-theme-muted hover:text-theme-primary'
              }`}
            >
              {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
              {f !== 'all' && (
                <span className="ml-1 opacity-70">
                  ({consoleMessages.filter(m => m.level === f).length})
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Console Output */}
      <div 
        ref={consoleRef}
        className="flex-1 overflow-y-auto bg-black/40 font-mono text-xs p-2 space-y-1"
      >
        {filteredMessages.length === 0 ? (
          <div className="text-theme-muted text-center py-4 italic">
            No console output yet
          </div>
        ) : (
          filteredMessages.map(msg => (
            <div key={msg.id} className="flex items-start gap-1 hover:bg-white/5 rounded px-1 py-0.5">
              <span className="text-gray-600 flex-shrink-0 w-14">
                {new Date(msg.timestamp).toLocaleTimeString([], { 
                  hour: '2-digit', 
                  minute: '2-digit',
                  second: '2-digit'
                })}
              </span>
              <span className={`px-1 rounded border text-[10px] flex-shrink-0 ${getLevelBadge(msg.level)}`}>
                {msg.level.slice(0, 3).toUpperCase()}
              </span>
              <span className={`flex-1 break-all ${getLevelColor(msg.level)}`}>
                {msg.message}
              </span>
            </div>
          ))
        )}
      </div>

      {/* Status bar */}
      <div className="p-2 border-t border-theme bg-theme-tertiary/30 flex items-center justify-between text-xs text-theme-muted">
        <span>{filteredMessages.length} messages</span>
        <div className="flex items-center gap-2">
          {consoleMessages.filter(m => m.level === 'error').length > 0 && (
            <span className="text-red-400">
              {consoleMessages.filter(m => m.level === 'error').length} errors
            </span>
          )}
          {consoleMessages.filter(m => m.level === 'warn').length > 0 && (
            <span className="text-yellow-400">
              {consoleMessages.filter(m => m.level === 'warn').length} warnings
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
