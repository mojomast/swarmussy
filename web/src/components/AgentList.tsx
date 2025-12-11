import { useState } from 'preact/hooks';
import { 
  Bot, Activity, BrainCircuit, ChevronDown, ChevronRight, 
  Settings, Zap, Target, Clock, Hash
} from 'lucide-preact';

interface Props {
  agents: any[];
  tokenStats?: any;
  onSelectAgent: (agent: any) => void;
  onSettingsClick: (agent: any) => void;
}

export function AgentList({ agents, tokenStats, onSelectAgent, onSettingsClick }: Props) {
  const [allAgentsExpanded, setAllAgentsExpanded] = useState(false);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'working': return 'text-green-400';
      case 'idle': return 'text-gray-400';
      case 'error': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getAgentColor = (name: string) => {
    const colors: Record<string, string> = {
      'Bossy McArchitect': 'border-purple-500/50 bg-purple-900/10',
      'Codey McBackend': 'border-blue-500/50 bg-blue-900/10',
      'Pixel McFrontend': 'border-pink-500/50 bg-pink-900/10',
      'Bugsy McTester': 'border-green-500/50 bg-green-900/10',
      'Deployo McOps': 'border-yellow-500/50 bg-yellow-900/10',
      'Checky McManager': 'border-cyan-500/50 bg-cyan-900/10',
      'Docy McWriter': 'border-red-500/50 bg-red-900/10'
    };
    return colors[name] || 'border-gray-500/50 bg-gray-900/10';
  };

  const getAgentTextColor = (name: string) => {
    const colors: Record<string, string> = {
      'Bossy McArchitect': 'text-purple-400',
      'Codey McBackend': 'text-blue-400',
      'Pixel McFrontend': 'text-pink-400',
      'Bugsy McTester': 'text-green-400',
      'Deployo McOps': 'text-yellow-400',
      'Checky McManager': 'text-cyan-400',
      'Docy McWriter': 'text-red-400'
    };
    return colors[name] || 'text-gray-400';
  };

  // Active agents = those with a task or working status
  const activeAgents = agents.filter(a => 
    a.status === 'working' || a.current_task_description || a.current_task_id
  );
  const inactiveAgents = agents.filter(a => 
    a.status !== 'working' && !a.current_task_description && !a.current_task_id
  );

  const getAgentTokens = (agentName: string) => {
    return tokenStats?.by_agent?.[agentName]?.total || 0;
  };

  const ActiveAgentCard = ({ agent }: { agent: any }) => (
    <div 
      className={`p-3 rounded-lg border ${getAgentColor(agent.name)} hover:bg-theme-tertiary/50 cursor-pointer transition-all`}
      onClick={() => onSelectAgent(agent)}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${
            agent.status === 'working' ? 'bg-green-400 animate-pulse' : 'bg-gray-500'
          }`} />
          <span className={`font-bold text-sm ${getAgentTextColor(agent.name)}`}>
            {agent.name}
          </span>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onSettingsClick(agent);
          }}
          className="p-1 hover:bg-theme-tertiary rounded transition-colors text-theme-muted hover:text-theme-primary"
          title="Agent Settings"
        >
          <Settings size={14} />
        </button>
      </div>

      {/* Current objective */}
      {agent.current_task_description && (
        <div className="mb-2">
          <div className="flex items-center gap-1 text-xs text-theme-muted mb-1">
            <Target size={10} />
            <span>Current Objective</span>
          </div>
          <div className="text-xs text-yellow-400 bg-yellow-900/20 p-2 rounded border border-yellow-900/30 line-clamp-2">
            {agent.current_task_description}
          </div>
        </div>
      )}

      {/* Next objective if available */}
      {agent.next_task_description && (
        <div className="mb-2">
          <div className="flex items-center gap-1 text-xs text-theme-muted mb-1">
            <Clock size={10} />
            <span>Next Up</span>
          </div>
          <div className="text-xs text-gray-400 bg-gray-800/50 p-2 rounded border border-gray-700 line-clamp-1">
            {agent.next_task_description}
          </div>
        </div>
      )}

      {/* Stats row */}
      <div className="flex items-center justify-between text-xs text-theme-muted mt-2 pt-2 border-t border-theme">
        <div className="flex items-center gap-1">
          <Zap size={10} className="text-yellow-400" />
          <span className="text-yellow-400">{getAgentTokens(agent.name).toLocaleString()}</span>
          <span>tokens</span>
        </div>
        <div className="flex items-center gap-1">
          <Hash size={10} />
          <span>{agent.tool_call_count || 0} calls</span>
        </div>
        <div className="text-gray-500 font-mono text-[10px]">
          {(agent.model || '').split('/').pop()?.slice(0, 12)}
        </div>
      </div>
    </div>
  );

  const InactiveAgentRow = ({ agent }: { agent: any }) => (
    <div 
      className="flex items-center justify-between p-2 hover:bg-theme-tertiary/30 rounded cursor-pointer transition-colors"
      onClick={() => onSelectAgent(agent)}
    >
      <div className="flex items-center gap-2">
        <div className={`w-1.5 h-1.5 rounded-full ${getStatusColor(agent.status).replace('text-', 'bg-')}`} />
        <span className={`text-sm ${getAgentTextColor(agent.name)}`}>{agent.name}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs text-theme-muted">
          {getAgentTokens(agent.name).toLocaleString()} t
        </span>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onSettingsClick(agent);
          }}
          className="p-1 hover:bg-theme-tertiary rounded transition-colors text-theme-muted hover:text-theme-primary"
          title="Agent Settings"
        >
          <Settings size={12} />
        </button>
      </div>
    </div>
  );

  return (
    <div className="bg-theme-secondary h-full border-r border-theme flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-theme font-bold text-theme-primary flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot size={20} className="text-theme-accent" />
          <span>Swarm Agents</span>
        </div>
        <div className="flex items-center gap-1 text-xs">
          <Activity size={12} className="text-green-400" />
          <span className="text-green-400">{activeAgents.length}</span>
          <span className="text-theme-muted">active</span>
        </div>
      </div>

      {/* Active Agents Section */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {activeAgents.length === 0 ? (
          <div className="text-center text-theme-muted text-sm py-4 italic">
            No agents currently working
          </div>
        ) : (
          activeAgents.map(agent => (
            <ActiveAgentCard key={agent.agent_id} agent={agent} />
          ))
        )}
      </div>

      {/* All Agents Collapsible Section */}
      <div className="border-t border-theme">
        <button
          onClick={() => setAllAgentsExpanded(!allAgentsExpanded)}
          className="w-full p-3 flex items-center justify-between hover:bg-theme-tertiary/30 transition-colors"
        >
          <div className="flex items-center gap-2 text-sm text-theme-muted">
            {allAgentsExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            <span>All Agents ({agents.length})</span>
          </div>
          <span className="text-xs text-theme-muted">
            {inactiveAgents.length} idle
          </span>
        </button>
        
        {allAgentsExpanded && (
          <div className="px-3 pb-3 space-y-1 max-h-60 overflow-y-auto">
            {agents.map(agent => (
              <InactiveAgentRow key={agent.agent_id} agent={agent} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
