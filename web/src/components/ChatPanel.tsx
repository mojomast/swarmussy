import { useState, useRef, useEffect } from 'preact/hooks';
import { sendChat } from '../lib/api';
import { Send, User, Bot, AlertCircle } from 'lucide-preact';

export function ChatPanel({ messages, agents }: { messages: any[], agents: any[] }) {
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: any) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    const msg = input;
    setInput('');
    try {
      await sendChat(msg);
    } catch (err) {
      console.error(err);
      setInput(msg); // restore on error
    }
  };

  const getAgentColor = (name: string) => {
    // Simple hash for consistent colors if not in map
    return 'text-blue-400';
  };

  return (
    <div className="flex flex-col h-full bg-gray-900 border-r border-gray-800">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg: any) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' || msg.role === 'human' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-lg p-3 ${
              msg.role === 'user' || msg.role === 'human' 
                ? 'bg-blue-600 text-white' 
                : msg.role === 'system'
                ? 'bg-gray-800 text-gray-400 border border-gray-700 text-sm italic'
                : msg.role === 'tool'
                ? 'bg-black/30 text-gray-300 border border-gray-700 font-mono text-xs'
                : 'bg-gray-800 text-gray-200 border border-gray-700'
            }`}>
              <div className="flex items-center gap-2 mb-1">
                <span className={`text-xs font-bold ${
                  msg.role === 'assistant' ? getAgentColor(msg.sender_name) : 'text-gray-300'
                }`}>
                  {msg.sender_name}
                </span>
                <span className="text-xs text-gray-500">
                  {new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                </span>
              </div>
              <div className="whitespace-pre-wrap font-mono text-sm">
                {msg.content}
              </div>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      
      <form onSubmit={handleSubmit} className="p-4 bg-gray-900 border-t border-gray-800">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onInput={(e) => setInput(e.currentTarget.value)}
            placeholder="Type a message or /command..."
            className="flex-1 bg-gray-800 text-white rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 border border-gray-700"
          />
          <button 
            type="submit"
            className="bg-blue-600 hover:bg-blue-700 text-white rounded-md p-2 transition-colors"
          >
            <Send size={20} />
          </button>
        </div>
      </form>
    </div>
  );
}
