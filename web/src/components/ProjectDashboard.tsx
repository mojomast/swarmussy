import { useState } from 'preact/hooks';
import { 
  BarChart3, CheckCircle2, Clock, AlertTriangle, Target, 
  TrendingUp, Layers, Activity, ChevronDown, ChevronRight,
  Zap, FileText, Users
} from 'lucide-preact';

interface PhaseInfo {
  id: string;
  name: string;
  status: 'pending' | 'in_progress' | 'completed';
  tasks_total: number;
  tasks_completed: number;
}

interface Props {
  projectName: string;
  status: any;
  tasks: any[];
  agents: any[];
  tokenStats: any;
}

export function ProjectDashboard({ projectName, status, tasks, agents, tokenStats }: Props) {
  const [expanded, setExpanded] = useState(true);

  // Calculate stats from tasks
  const totalTasks = tasks.length;
  const completedTasks = tasks.filter(t => t.status === 'completed').length;
  const inProgressTasks = tasks.filter(t => t.status === 'in_progress').length;
  const blockedTasks = tasks.filter(t => t.status === 'blocked').length;
  const pendingTasks = tasks.filter(t => t.status === 'pending').length;

  // Calculate phase info from tasks (tasks have format like "1.1", "1.2", "2.1")
  const phases: PhaseInfo[] = [];
  const phaseMap = new Map<string, { total: number; completed: number; inProgress: number }>();
  
  tasks.forEach(task => {
    const match = task.id?.match(/^(\d+)\./);
    if (match) {
      const phaseId = match[1];
      if (!phaseMap.has(phaseId)) {
        phaseMap.set(phaseId, { total: 0, completed: 0, inProgress: 0 });
      }
      const phase = phaseMap.get(phaseId)!;
      phase.total++;
      if (task.status === 'completed') phase.completed++;
      if (task.status === 'in_progress') phase.inProgress++;
    }
  });

  phaseMap.forEach((data, id) => {
    phases.push({
      id,
      name: `Phase ${id}`,
      status: data.completed === data.total ? 'completed' : data.inProgress > 0 ? 'in_progress' : 'pending',
      tasks_total: data.total,
      tasks_completed: data.completed
    });
  });

  // Sort phases by ID
  phases.sort((a, b) => parseInt(a.id) - parseInt(b.id));

  const overallProgress = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;
  const activeAgents = agents.filter(a => a.status === 'working').length;

  // Get blockers (blocked tasks with reasons)
  const blockers = tasks.filter(t => t.status === 'blocked').map(t => ({
    task: t.id || t.description?.slice(0, 30),
    reason: t.blocked_reason || 'Dependency not met'
  }));

  return (
    <div className="bg-theme-secondary border border-theme rounded-lg overflow-hidden">
      {/* Header */}
      <button 
        onClick={() => setExpanded(!expanded)}
        className="w-full p-4 flex items-center justify-between hover:bg-theme-tertiary transition-colors"
      >
        <div className="flex items-center gap-3">
          <BarChart3 className="text-theme-accent" size={20} />
          <span className="font-bold text-theme-primary">Project Dashboard</span>
          {projectName && (
            <span className="text-xs bg-theme-accent/20 text-theme-accent px-2 py-0.5 rounded">
              {projectName}
            </span>
          )}
        </div>
        {expanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
      </button>

      {expanded && (
        <div className="p-4 pt-0 space-y-4">
          {/* Progress Overview */}
          <div className="grid grid-cols-2 gap-3">
            {/* Overall Progress */}
            <div className="bg-theme-tertiary rounded-lg p-3 border border-theme">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-theme-muted">Overall Progress</span>
                <TrendingUp size={14} className="text-green-400" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-theme-primary">{overallProgress}%</span>
                <span className="text-xs text-theme-muted">{completedTasks}/{totalTasks}</span>
              </div>
              <div className="mt-2 h-2 bg-gray-800 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-green-500 to-emerald-400 transition-all duration-500"
                  style={{ width: `${overallProgress}%` }}
                />
              </div>
            </div>

            {/* Token Usage */}
            <div className="bg-theme-tertiary rounded-lg p-3 border border-theme">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-theme-muted">Token Usage</span>
                <Zap size={14} className="text-yellow-400" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-yellow-400">
                  {((tokenStats?.total_tokens || 0) / 1000).toFixed(1)}k
                </span>
              </div>
              <div className="mt-1 text-xs text-theme-muted">
                Round {status?.round_number || 0}
              </div>
            </div>
          </div>

          {/* Quick Stats Row */}
          <div className="grid grid-cols-4 gap-2">
            <div className="bg-theme-tertiary/50 rounded p-2 text-center border border-theme">
              <div className="text-lg font-bold text-blue-400">{inProgressTasks}</div>
              <div className="text-xs text-theme-muted flex items-center justify-center gap-1">
                <Clock size={10} /> Active
              </div>
            </div>
            <div className="bg-theme-tertiary/50 rounded p-2 text-center border border-theme">
              <div className="text-lg font-bold text-gray-400">{pendingTasks}</div>
              <div className="text-xs text-theme-muted flex items-center justify-center gap-1">
                <Target size={10} /> Pending
              </div>
            </div>
            <div className="bg-theme-tertiary/50 rounded p-2 text-center border border-theme">
              <div className="text-lg font-bold text-green-400">{completedTasks}</div>
              <div className="text-xs text-theme-muted flex items-center justify-center gap-1">
                <CheckCircle2 size={10} /> Done
              </div>
            </div>
            <div className="bg-theme-tertiary/50 rounded p-2 text-center border border-theme">
              <div className="text-lg font-bold text-red-400">{blockedTasks}</div>
              <div className="text-xs text-theme-muted flex items-center justify-center gap-1">
                <AlertTriangle size={10} /> Blocked
              </div>
            </div>
          </div>

          {/* Phase Progress */}
          {phases.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs text-theme-muted">
                <Layers size={12} />
                <span>Phase Progress</span>
              </div>
              <div className="space-y-1">
                {phases.map(phase => (
                  <div key={phase.id} className="flex items-center gap-2">
                    <div className="w-16 text-xs text-theme-muted truncate">{phase.name}</div>
                    <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                      <div 
                        className={`h-full transition-all duration-300 ${
                          phase.status === 'completed' ? 'bg-green-500' :
                          phase.status === 'in_progress' ? 'bg-blue-500' : 'bg-gray-600'
                        }`}
                        style={{ width: `${phase.tasks_total > 0 ? (phase.tasks_completed / phase.tasks_total) * 100 : 0}%` }}
                      />
                    </div>
                    <div className="w-12 text-xs text-theme-muted text-right">
                      {phase.tasks_completed}/{phase.tasks_total}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Active Agents */}
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-theme-muted">
              <Users size={12} />
              <span>Active Agents</span>
            </div>
            <div className="flex items-center gap-1">
              <Activity size={12} className="text-green-400" />
              <span className="text-green-400 font-bold">{activeAgents}</span>
              <span className="text-theme-muted">/ {agents.length}</span>
            </div>
          </div>

          {/* Blockers */}
          {blockers.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs text-red-400">
                <AlertTriangle size={12} />
                <span>Blockers ({blockers.length})</span>
              </div>
              <div className="space-y-1 max-h-24 overflow-y-auto">
                {blockers.map((blocker, i) => (
                  <div key={i} className="text-xs bg-red-900/20 border border-red-900/30 rounded px-2 py-1">
                    <span className="text-red-400">{blocker.task}:</span>
                    <span className="text-theme-muted ml-1">{blocker.reason}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Mode Badge */}
          <div className="flex items-center justify-between pt-2 border-t border-theme">
            <div className="flex items-center gap-2">
              <FileText size={12} className="text-theme-muted" />
              <span className="text-xs text-theme-muted">Mode:</span>
              <span className={`text-xs font-bold ${status?.devussy_mode ? 'text-purple-400' : 'text-gray-400'}`}>
                {status?.devussy_mode ? 'Devussy Pipeline' : 'Standard Swarm'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
