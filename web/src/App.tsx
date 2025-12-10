import { useState, useEffect } from 'preact/hooks';
import { useSwarm } from './hooks/useSwarm';
import { ChatPanel } from './components/ChatPanel';
import { AgentList } from './components/AgentList';
import { TaskBoard } from './components/TaskBoard';
import { FileBrowser } from './components/FileBrowser';
import { SettingsModal } from './components/SettingsModal';
import { ProjectSelector } from './components/ProjectSelector';
import { DevussyPipelineModal } from './components/DevussyPipelineModal';
import { ProviderSettings } from './components/ProviderSettings';
import { Terminal, Files, Settings, FolderOpen, Key, Sparkles } from 'lucide-preact';
import { selectProject, resumeDevussyPipeline, setDevussyMode } from './lib/api';

type AppView = 'project-select' | 'main';

export function App() {
  const { messages, agents, tasks, status, project, connected, settings, refreshState } = useSwarm();
  const [view, setView] = useState<AppView>('project-select');
  const [activeTab, setActiveTab] = useState<'chat' | 'files'>('chat');
  const [showSettings, setShowSettings] = useState(false);
  const [showProviderSettings, setShowProviderSettings] = useState(false);
  const [showDevussyPipeline, setShowDevussyPipeline] = useState(false);
  const [currentProjectName, setCurrentProjectName] = useState('');

  // Check if we should show project selector or main view
  useEffect(() => {
    if (project?.name) {
      setCurrentProjectName(project.name);
      // If project has devplan, go straight to main view
      if (project.has_master_plan || project.has_devplan) {
        setView('main');
      }
    }
  }, [project]);

  const handleProjectSelected = async (projectName: string, startDevussy: boolean) => {
    setCurrentProjectName(projectName);
    
    if (startDevussy) {
      // Show devussy pipeline modal
      setShowDevussyPipeline(true);
    } else {
      // Go directly to main view
      setView('main');
      await refreshState();
    }
  };

  const handleResumeDevussy = async (resumeInfo: any) => {
    try {
      await resumeDevussyPipeline(resumeInfo);
      await setDevussyMode(true);
      setView('main');
      await refreshState();
    } catch (e) {
      console.error('Failed to resume pipeline', e);
    }
  };

  const handleDevussyComplete = async () => {
    setShowDevussyPipeline(false);
    await setDevussyMode(true);
    setView('main');
    await refreshState();
  };

  const handleBackToProjects = () => {
    setView('project-select');
  };

  // Project Selection View
  if (view === 'project-select') {
    return (
      <>
        <ProjectSelector
          onProjectSelected={handleProjectSelected}
          onResumeDevussy={handleResumeDevussy}
        />
        {showDevussyPipeline && (
          <DevussyPipelineModal
            projectName={currentProjectName}
            onClose={() => {
              setShowDevussyPipeline(false);
              setView('main');
            }}
            onComplete={handleDevussyComplete}
          />
        )}
      </>
    );
  }

  // Main Application View
  return (
    <div className="flex h-screen bg-gray-950 text-white font-sans overflow-hidden">
      {/* Sidebar Navigation */}
      <div className="w-16 bg-gray-900 border-r border-gray-800 flex flex-col items-center py-4 gap-4">
        {/* Project Button */}
        <button 
          onClick={handleBackToProjects}
          className="p-3 text-gray-400 hover:text-white hover:bg-gray-800 rounded-xl transition-colors"
          title="Switch Project"
        >
          <FolderOpen size={24} />
        </button>
        
        <div className="w-8 h-px bg-gray-700" />
        
        <button 
          onClick={() => setActiveTab('chat')}
          className={`p-3 rounded-xl transition-colors ${activeTab === 'chat' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'}`}
          title="Chat"
        >
          <Terminal size={24} />
        </button>
        <button 
          onClick={() => setActiveTab('files')}
          className={`p-3 rounded-xl transition-colors ${activeTab === 'files' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'}`}
          title="Files"
        >
          <Files size={24} />
        </button>
        
        <div className="flex-1" />
        
        {/* Devussy Pipeline Button */}
        <button 
          onClick={() => setShowDevussyPipeline(true)}
          className="p-3 text-purple-400 hover:text-purple-300 hover:bg-purple-900/30 rounded-xl transition-colors"
          title="Devussy Pipeline"
        >
          <Sparkles size={24} />
        </button>
        
        {/* Provider Settings */}
        <button 
          onClick={() => setShowProviderSettings(true)}
          className="p-3 text-gray-400 hover:text-white hover:bg-gray-800 rounded-xl transition-colors"
          title="API Keys & Models"
        >
          <Key size={24} />
        </button>
        
        {/* General Settings */}
        <button 
          onClick={() => setShowSettings(true)}
          className="p-3 text-gray-400 hover:text-white hover:bg-gray-800 rounded-xl transition-colors"
          title="Settings"
        >
          <Settings size={24} />
        </button>
        
        {/* Connection Status */}
        <div 
          className={`w-3 h-3 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} 
          title={connected ? "Connected" : "Disconnected"} 
        />
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {activeTab === 'chat' ? (
          <>
            {/* Left: Chat */}
            <div className="flex-1 min-w-0">
              <ChatPanel messages={messages} agents={agents} />
            </div>
            
            {/* Middle: Agents */}
            <div className="w-64 hidden lg:block">
              <AgentList agents={agents} onSelect={(a) => console.log(a)} />
            </div>

            {/* Right: Tasks & Status */}
            <div className="w-72 hidden xl:block border-l border-gray-800 bg-gray-900 flex flex-col">
              <div className="p-4 border-b border-gray-800">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-bold text-gray-200">Project Status</h3>
                  {currentProjectName && (
                    <span className="text-xs bg-blue-900/40 text-blue-300 px-2 py-1 rounded">
                      {currentProjectName}
                    </span>
                  )}
                </div>
                <div className="text-xs text-gray-400 space-y-1">
                  <div className="flex justify-between">
                    <span>Round:</span> <span className="text-white">{status.round_number || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Tokens:</span> <span className="text-yellow-500">{status.total_tokens?.toLocaleString() || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Mode:</span> <span className={status.devussy_mode ? 'text-purple-400' : 'text-gray-400'}>
                      {status.devussy_mode ? 'Devussy' : 'Standard'}
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex-1 overflow-hidden">
                <TaskBoard tasks={tasks} />
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1">
            <FileBrowser />
          </div>
        )}
      </div>

      {/* Modals */}
      {showSettings && (
        <SettingsModal 
          onClose={() => {
            setShowSettings(false);
            refreshState();
          }} 
          settings={settings} 
        />
      )}

      {showProviderSettings && (
        <ProviderSettings
          onClose={() => {
            setShowProviderSettings(false);
            refreshState();
          }}
        />
      )}

      {showDevussyPipeline && (
        <DevussyPipelineModal
          projectName={currentProjectName}
          onClose={() => setShowDevussyPipeline(false)}
          onComplete={handleDevussyComplete}
        />
      )}
    </div>
  );
}
