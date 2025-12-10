import { Bot, Activity, BrainCircuit } from 'lucide-preact';

export function AgentList({ agents, onSelect }: { agents: any[], onSelect: (agent: any) => void }) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'working': return 'text-green-400';
      case 'idle': return 'text-gray-400';
      case 'error': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className="bg-gray-900 h-full border-r border-gray-800 flex flex-col">
      <div className="p-4 border-b border-gray-800 font-bold text-gray-200 flex items-center gap-2">
        <Bot size={20} />
        <span>Swarm Agents</span>
      </div>
      <div className="flex-1 overflow-y-auto">
        {agents.map(agent => (
          <div 
            key={agent.agent_id}
            onClick={() => onSelect(agent)}
            className="p-4 border-b border-gray-800 hover:bg-gray-800 cursor-pointer transition-colors"
          >
            <div className="flex justify-between items-start mb-1">
              <span className="font-bold text-gray-200">{agent.name}</span>
              <Activity size={16} className={getStatusColor(agent.status)} />
            </div>
            <div className="text-xs text-gray-500 font-mono mb-2">{agent.model}</div>
            {agent.current_task_description && (
              <div className="text-xs text-yellow-500 bg-yellow-900/20 p-2 rounded border border-yellow-900/50">
                <BrainCircuit size={12} className="inline mr-1" />
                {agent.current_task_description.slice(0, 60)}...
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
