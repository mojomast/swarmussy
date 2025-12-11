import { useState } from 'preact/hooks';
import { 
  CheckCircle2, Circle, Clock, AlertTriangle, ListTodo,
  ChevronDown, ChevronRight, Filter, User, Layers
} from 'lucide-preact';

interface Props {
  tasks: any[];
  status?: any;
}

export function TaskBoard({ tasks, status }: Props) {
  const [filter, setFilter] = useState<'all' | 'active' | 'completed'>('all');
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set());

  const toggleTask = (taskId: string) => {
    setExpandedTasks(prev => {
      const next = new Set(prev);
      if (next.has(taskId)) next.delete(taskId);
      else next.add(taskId);
      return next;
    });
  };

  const getStatusIcon = (taskStatus: string) => {
    switch (taskStatus) {
      case 'completed': return <CheckCircle2 className="text-green-500" size={14} />;
      case 'in_progress': return <Clock className="text-blue-500 animate-pulse" size={14} />;
      case 'blocked': return <AlertTriangle className="text-red-500" size={14} />;
      case 'dispatched': return <Clock className="text-yellow-500" size={14} />;
      default: return <Circle className="text-gray-500" size={14} />;
    }
  };

  const getStatusBadge = (taskStatus: string) => {
    switch (taskStatus) {
      case 'completed': return 'bg-green-900/40 text-green-400 border-green-500/30';
      case 'in_progress': return 'bg-blue-900/40 text-blue-400 border-blue-500/30';
      case 'blocked': return 'bg-red-900/40 text-red-400 border-red-500/30';
      case 'dispatched': return 'bg-yellow-900/40 text-yellow-400 border-yellow-500/30';
      default: return 'bg-gray-800 text-gray-400 border-gray-600';
    }
  };

  const getAgentColor = (agentName: string) => {
    const colors: Record<string, string> = {
      'backend_dev': 'text-blue-400',
      'frontend_dev': 'text-pink-400',
      'qa_engineer': 'text-green-400',
      'devops': 'text-yellow-400',
      'tech_writer': 'text-red-400',
      'Codey McBackend': 'text-blue-400',
      'Pixel McFrontend': 'text-pink-400',
      'Bugsy McTester': 'text-green-400',
      'Deployo McOps': 'text-yellow-400',
      'Docy McWriter': 'text-red-400'
    };
    return colors[agentName] || 'text-gray-400';
  };

  // Filter tasks
  const filteredTasks = tasks.filter(task => {
    if (filter === 'active') return ['in_progress', 'dispatched'].includes(task.status);
    if (filter === 'completed') return task.status === 'completed';
    return true;
  });

  // Group by phase
  const tasksByPhase = new Map<string, any[]>();
  filteredTasks.forEach(task => {
    const match = task.id?.match(/^(\d+)\./);
    const phase = match ? `Phase ${match[1]}` : 'Other';
    if (!tasksByPhase.has(phase)) tasksByPhase.set(phase, []);
    tasksByPhase.get(phase)!.push(task);
  });

  // Stats
  const totalTasks = tasks.length;
  const completedCount = tasks.filter(t => t.status === 'completed').length;
  const activeCount = tasks.filter(t => ['in_progress', 'dispatched'].includes(t.status)).length;

  return (
    <div className="bg-theme-secondary h-full flex flex-col">
      {/* Header */}
      <div className="p-3 border-b border-theme">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <ListTodo size={16} className="text-theme-accent" />
            <span className="font-bold text-theme-primary text-sm">Task Queue</span>
          </div>
          <span className="text-xs text-theme-muted">
            {completedCount}/{totalTasks}
          </span>
        </div>
        
        {/* Filter tabs */}
        <div className="flex gap-1">
          {(['all', 'active', 'completed'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-2 py-0.5 text-xs rounded transition-colors ${
                filter === f 
                  ? 'bg-theme-accent text-white' 
                  : 'bg-theme-tertiary text-theme-muted hover:text-theme-primary'
              }`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
              {f === 'active' && activeCount > 0 && (
                <span className="ml-1">({activeCount})</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Tasks List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-3">
        {filteredTasks.length === 0 ? (
          <div className="text-theme-muted text-center text-sm py-8 italic">
            {filter === 'all' ? 'No tasks in queue' : `No ${filter} tasks`}
          </div>
        ) : (
          Array.from(tasksByPhase.entries()).map(([phase, phaseTasks]) => (
            <div key={phase} className="space-y-1">
              {/* Phase header */}
              <div className="flex items-center gap-2 px-2 py-1 sticky top-0 bg-theme-secondary z-10">
                <Layers size={12} className="text-theme-muted" />
                <span className="text-xs font-bold text-theme-muted">{phase}</span>
                <span className="text-xs text-theme-muted">
                  ({phaseTasks.filter(t => t.status === 'completed').length}/{phaseTasks.length})
                </span>
              </div>

              {/* Phase tasks */}
              {phaseTasks.map(task => {
                const isExpanded = expandedTasks.has(task.id);
                return (
                  <div 
                    key={task.id}
                    className="bg-theme-tertiary/50 rounded-lg border border-theme overflow-hidden"
                  >
                    {/* Task header - always visible */}
                    <button
                      onClick={() => toggleTask(task.id)}
                      className="w-full p-2 flex items-start gap-2 hover:bg-theme-tertiary/70 transition-colors text-left"
                    >
                      <div className="mt-0.5 flex-shrink-0">
                        {getStatusIcon(task.status)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-mono text-theme-muted">{task.id}</span>
                          <span className={`px-1.5 py-0.5 text-[10px] rounded border ${getStatusBadge(task.status)}`}>
                            {task.status}
                          </span>
                        </div>
                        <div className="text-xs text-theme-primary line-clamp-1">
                          {task.title || task.description?.split('\n')[0] || 'Untitled Task'}
                        </div>
                      </div>
                      <div className="flex-shrink-0 text-theme-muted">
                        {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                      </div>
                    </button>

                    {/* Expanded details */}
                    {isExpanded && (
                      <div className="px-3 pb-2 pt-1 border-t border-theme/50 space-y-2">
                        {/* Description */}
                        {task.description && (
                          <div className="text-xs text-theme-secondary whitespace-pre-wrap bg-black/20 rounded p-2 max-h-32 overflow-y-auto">
                            {task.description}
                          </div>
                        )}
                        
                        {/* Meta info */}
                        <div className="flex flex-wrap items-center gap-2 text-xs">
                          {task.assigned_to && (
                            <div className="flex items-center gap-1">
                              <User size={10} />
                              <span className={getAgentColor(task.assigned_to)}>
                                {task.assigned_to}
                              </span>
                            </div>
                          )}
                          {task.priority && (
                            <span className={`px-1.5 py-0.5 rounded ${
                              task.priority === 'high' ? 'bg-red-900/30 text-red-400' :
                              task.priority === 'medium' ? 'bg-yellow-900/30 text-yellow-400' :
                              'bg-gray-800 text-gray-400'
                            }`}>
                              {task.priority}
                            </span>
                          )}
                          {task.complexity && (
                            <span className="text-theme-muted">
                              {task.complexity}
                            </span>
                          )}
                        </div>

                        {/* Dependencies */}
                        {task.depends_on && task.depends_on.length > 0 && (
                          <div className="text-xs text-theme-muted">
                            Depends: {task.depends_on.join(', ')}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ))
        )}
      </div>

      {/* Footer stats */}
      <div className="p-2 border-t border-theme bg-theme-tertiary/30 flex items-center justify-between text-xs text-theme-muted">
        <span>{filteredTasks.length} tasks shown</span>
        <div className="flex items-center gap-3">
          <span className="text-blue-400">{activeCount} active</span>
          <span className="text-green-400">{completedCount} done</span>
        </div>
      </div>
    </div>
  );
}
