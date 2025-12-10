import { CheckCircle2, Circle, Clock, AlertTriangle } from 'lucide-preact';

export function TaskBoard({ tasks }: { tasks: any[] }) {
  const getIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle2 className="text-green-500" size={18} />;
      case 'in_progress': return <Clock className="text-blue-500" size={18} />;
      case 'failed': return <AlertTriangle className="text-red-500" size={18} />;
      default: return <Circle className="text-gray-500" size={18} />;
    }
  };

  return (
    <div className="bg-gray-900 h-full flex flex-col">
      <div className="p-4 border-b border-gray-800 font-bold text-gray-200">
        Task Queue
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {tasks.length === 0 && (
          <div className="text-gray-500 text-center italic">No tasks active</div>
        )}
        {tasks.map(task => (
          <div key={task.id} className="bg-gray-800 rounded-lg p-3 border border-gray-700">
            <div className="flex items-start gap-3">
              <div className="mt-1">{getIcon(task.status)}</div>
              <div className="flex-1">
                <div className="text-sm text-gray-200 mb-1">{task.description}</div>
                <div className="flex justify-between items-center text-xs">
                  <span className={`px-2 py-0.5 rounded-full bg-gray-900 ${
                    task.status === 'in_progress' ? 'text-blue-400' : 'text-gray-400'
                  }`}>
                    {task.status}
                  </span>
                  {task.assigned_to && (
                    <span className="text-gray-500">
                      Assigned: {task.assigned_to.split('-')[0]}...
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
