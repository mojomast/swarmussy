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
import { SplashScreen, useSplashScreen } from './components/SplashScreen';
import { ProjectDashboard } from './components/ProjectDashboard';
import { AgentSettingsPanel } from './components/AgentSettingsPanel';
import { AssistantChat } from './components/AssistantChat';
import { Terminal, Files, Settings, FolderOpen, Key, Sparkles, HelpCircle, MessageCircle } from 'lucide-preact';
import { selectProject, resumeDevussyPipeline, setDevussyMode, updateAgentConfig } from './lib/api';

type AppView = 'project-select' | 'main';

export function App() {
  const { messages, agents, tasks, status, tokenStats, project, connected, settings, refreshState } = useSwarm();
  const [view, setView] = useState<AppView>('project-select');
  const [activeTab, setActiveTab] = useState<'chat' | 'files'>('chat');
  const [showSettings, setShowSettings] = useState(false);
  const [showProviderSettings, setShowProviderSettings] = useState(false);
  const [showDevussyPipeline, setShowDevussyPipeline] = useState(false);
  const [currentProjectName, setCurrentProjectName] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<any>(null);
  const [showAgentSettings, setShowAgentSettings] = useState(false);
  const [showAssistantChat, setShowAssistantChat] = useState(false);
  const { showSplash, openSplash, closeSplash } = useSplashScreen();

  const handleAgentSettingsClick = (agent: any) => {
    setSelectedAgent(agent);
    setShowAgentSettings(true);
  };

  const handleAgentSettingsSave = async (agentId: string, config: any) => {
    await updateAgentConfig(agentId, config);
    await refreshState();
  };

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
    <div className="flex h-screen bg-theme-primary text-theme-secondary font-sans overflow-hidden">
      {/* Sidebar Navigation */}
      <div className="w-16 bg-theme-secondary border-r border-theme flex flex-col items-center py-4 gap-4">
        {/* Project Button */}
        <button 
          onClick={handleBackToProjects}
          className="p-3 text-theme-muted hover:text-theme-primary hover:bg-theme-tertiary rounded-xl transition-colors"
          title="Switch Project"
        >
          <FolderOpen size={24} />
        </button>
        
        <div className="w-8 h-px bg-theme-tertiary" />
        
        <button 
          onClick={() => setActiveTab('chat')}
          className={`p-3 rounded-xl transition-colors ${activeTab === 'chat' ? 'bg-theme-accent text-white' : 'text-theme-muted hover:text-theme-primary hover:bg-theme-tertiary'}`}
          title="Chat"
        >
          <Terminal size={24} />
        </button>
        <button 
          onClick={() => setActiveTab('files')}
          className={`p-3 rounded-xl transition-colors ${activeTab === 'files' ? 'bg-theme-accent text-white' : 'text-theme-muted hover:text-theme-primary hover:bg-theme-tertiary'}`}
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
          className="p-3 text-theme-muted hover:text-theme-primary hover:bg-theme-tertiary rounded-xl transition-colors"
          title="API Keys & Models"
        >
          <Key size={24} />
        </button>
        
        {/* General Settings */}
        <button 
          onClick={() => setShowSettings(true)}
          className="p-3 text-theme-muted hover:text-theme-primary hover:bg-theme-tertiary rounded-xl transition-colors"
          title="Settings"
        >
          <Settings size={24} />
        </button>
        
        {/* Assistant Chat Button */}
        <button 
          onClick={() => setShowAssistantChat(true)}
          className="p-3 text-emerald-400 hover:text-emerald-300 hover:bg-emerald-900/30 rounded-xl transition-colors"
          title="Project Assistant - Chat about your project"
        >
          <MessageCircle size={24} />
        </button>
        
        {/* Help Button */}
        <button 
          onClick={openSplash}
          className="p-3 text-theme-muted hover:text-theme-primary hover:bg-theme-tertiary rounded-xl transition-colors"
          title="Help & Getting Started"
        >
          <HelpCircle size={24} />
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
              <ChatPanel messages={messages} agents={agents} tokenStats={tokenStats} />
            </div>
            
            {/* Middle: Agents */}
            <div className="w-72 hidden lg:block">
              <AgentList 
                agents={agents} 
                tokenStats={tokenStats}
                onSelectAgent={(a) => console.log('Selected agent:', a)} 
                onSettingsClick={handleAgentSettingsClick}
              />
            </div>

            {/* Right: Dashboard & Tasks */}
            <div className="w-80 hidden xl:block border-l border-theme bg-theme-secondary flex flex-col">
              {/* Project Dashboard */}
              <div className="p-3 border-b border-theme">
                <ProjectDashboard 
                  projectName={currentProjectName}
                  status={status}
                  tasks={tasks}
                  agents={agents}
                  tokenStats={tokenStats}
                />
              </div>
              
              {/* Task Queue */}
              <div className="flex-1 overflow-hidden">
                <TaskBoard tasks={tasks} status={status} />
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

      {/* Splash Screen */}
      {showSplash && (
        <SplashScreen onClose={closeSplash} />
      )}

      {/* Agent Settings Modal */}
      {showAgentSettings && selectedAgent && (
        <AgentSettingsPanel
          agent={selectedAgent}
          onClose={() => {
            setShowAgentSettings(false);
            setSelectedAgent(null);
          }}
          onSave={handleAgentSettingsSave}
        />
      )}

      {/* Assistant Chat */}
      {showAssistantChat && (
        <AssistantChat
          projectName={currentProjectName}
          onClose={() => setShowAssistantChat(false)}
        />
      )}
    </div>
  );
}
