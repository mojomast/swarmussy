import { useState, useEffect } from 'preact/hooks';
import { fetchProjects, createProject, selectProject, deleteProject, fetchDevussyArtifacts } from '../lib/api';
import { FolderPlus, FolderOpen, Trash2, Play, RotateCcw, Sparkles, AlertCircle, Check, Loader2 } from 'lucide-preact';

interface Project {
  name: string;
  is_current: boolean;
  created_at?: string;
  has_devplan?: boolean;
}

interface DevussyRun {
  name: string;
  path: string;
  artifacts: string[];
  stages_complete: string[];
  phase_count?: number;
}

interface Props {
  onProjectSelected: (projectName: string, startDevussy: boolean) => void;
  onResumeDevussy: (resumeInfo: any) => void;
}

export function ProjectSelector({ onProjectSelected, onResumeDevussy }: Props) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');
  const [error, setError] = useState('');
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [artifacts, setArtifacts] = useState<{ runs: DevussyRun[], checkpoints: any[] }>({ runs: [], checkpoints: [] });
  const [showResumeOptions, setShowResumeOptions] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const data = await fetchProjects();
      setProjects(data.projects || []);
      
      // Find current project
      const current = data.projects?.find((p: Project) => p.is_current);
      if (current) {
        setSelectedProject(current.name);
        loadArtifacts();
      }
    } catch (e) {
      setError('Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const loadArtifacts = async () => {
    try {
      const data = await fetchDevussyArtifacts();
      setArtifacts(data);
    } catch (e) {
      console.error('Failed to load artifacts', e);
    }
  };

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) {
      setError('Project name is required');
      return;
    }

    try {
      setCreating(true);
      setError('');
      await createProject(newProjectName.trim(), newProjectDesc.trim());
      await selectProject(newProjectName.trim());
      setNewProjectName('');
      setNewProjectDesc('');
      // New project - start devussy interview
      onProjectSelected(newProjectName.trim(), true);
    } catch (e: any) {
      setError(e.message || 'Failed to create project');
    } finally {
      setCreating(false);
    }
  };

  const handleSelectProject = async (name: string) => {
    try {
      setSelectedProject(name);
      await selectProject(name);
      await loadArtifacts();
    } catch (e) {
      setError('Failed to select project');
    }
  };

  const handleDeleteProject = async (name: string) => {
    if (!confirm(`Delete project "${name}"? This cannot be undone.`)) return;
    
    try {
      setDeleting(name);
      await deleteProject(name);
      await loadProjects();
      if (selectedProject === name) {
        setSelectedProject(null);
      }
    } catch (e) {
      setError('Failed to delete project');
    } finally {
      setDeleting(null);
    }
  };

  const handleOpenProject = () => {
    if (!selectedProject) return;
    // Open existing project without starting devussy
    onProjectSelected(selectedProject, false);
  };

  const handleStartDevussy = () => {
    if (!selectedProject) return;
    onProjectSelected(selectedProject, true);
  };

  const handleResumeFromRun = (run: DevussyRun, stage: string) => {
    onResumeDevussy({
      type: 'run',
      run_path: run.path,
      resume_after: stage
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Loading projects...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-4xl mx-auto p-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            🐝 SwarmUssY
          </h1>
          <p className="text-gray-400">Multi-Agent AI Development Platform</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-900/30 border border-red-700 rounded-lg flex items-center gap-2 text-red-300">
            <AlertCircle size={20} />
            <span>{error}</span>
            <button onClick={() => setError('')} className="ml-auto text-red-400 hover:text-red-300">×</button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Create New Project */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <FolderPlus className="text-green-400" size={24} />
              New Project
            </h2>
            <p className="text-gray-400 text-sm mb-4">
              Create a new project and start the Devussy interview to define your project requirements.
            </p>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Project Name</label>
                <input
                  type="text"
                  value={newProjectName}
                  onInput={(e) => setNewProjectName(e.currentTarget.value)}
                  placeholder="my-awesome-project"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Description (optional)</label>
                <input
                  type="text"
                  value={newProjectDesc}
                  onInput={(e) => setNewProjectDesc(e.currentTarget.value)}
                  placeholder="A brief description..."
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <button
                onClick={handleCreateProject}
                disabled={creating || !newProjectName.trim()}
                className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-3 px-4 rounded-lg transition-all flex items-center justify-center gap-2"
              >
                {creating ? (
                  <>
                    <Loader2 className="animate-spin" size={20} />
                    Creating...
                  </>
                ) : (
                  <>
                    <Sparkles size={20} />
                    Create & Start Devussy Interview
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Existing Projects */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <FolderOpen className="text-blue-400" size={24} />
              Existing Projects
            </h2>
            
            {projects.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No projects yet. Create one to get started!</p>
            ) : (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {projects.map((project) => (
                  <div
                    key={project.name}
                    onClick={() => handleSelectProject(project.name)}
                    className={`p-3 rounded-lg cursor-pointer transition-all flex items-center justify-between group ${
                      selectedProject === project.name
                        ? 'bg-blue-900/40 border border-blue-700'
                        : 'bg-gray-800 border border-gray-700 hover:border-gray-600'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      {selectedProject === project.name && (
                        <Check size={16} className="text-blue-400" />
                      )}
                      <span className="font-medium">{project.name}</span>
                      {project.is_current && (
                        <span className="text-xs bg-blue-600 px-2 py-0.5 rounded">current</span>
                      )}
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteProject(project.name);
                      }}
                      disabled={deleting === project.name}
                      className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300 p-1 transition-opacity"
                    >
                      {deleting === project.name ? (
                        <Loader2 className="animate-spin" size={16} />
                      ) : (
                        <Trash2 size={16} />
                      )}
                    </button>
                  </div>
                ))}
              </div>
            )}

            {selectedProject && (
              <div className="mt-4 pt-4 border-t border-gray-700 space-y-2">
                <button
                  onClick={handleOpenProject}
                  className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  <Play size={18} />
                  Open Project
                </button>
                <button
                  onClick={handleStartDevussy}
                  className="w-full bg-purple-600 hover:bg-purple-500 text-white font-bold py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  <Sparkles size={18} />
                  Start New Devussy Pipeline
                </button>
                {artifacts.runs.length > 0 && (
                  <button
                    onClick={() => setShowResumeOptions(!showResumeOptions)}
                    className="w-full bg-gray-700 hover:bg-gray-600 text-white py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
                  >
                    <RotateCcw size={18} />
                    Resume from Checkpoint ({artifacts.runs.length} runs)
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Resume Options */}
        {showResumeOptions && artifacts.runs.length > 0 && (
          <div className="mt-8 bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
              <RotateCcw className="text-yellow-400" size={20} />
              Resume from Previous Run
            </h3>
            <div className="space-y-4">
              {artifacts.runs.slice(0, 5).map((run) => (
                <div key={run.path} className="bg-gray-800 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-blue-300">{run.name}</span>
                    <span className="text-xs text-gray-500">{run.artifacts.length} artifacts</span>
                  </div>
                  <div className="text-xs text-gray-400 mb-3">
                    Stages: {run.stages_complete.join(' → ')}
                    {run.phase_count && ` (${run.phase_count} phases)`}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {run.stages_complete.map((stage) => (
                      <button
                        key={stage}
                        onClick={() => handleResumeFromRun(run, stage)}
                        className="text-xs bg-yellow-900/40 hover:bg-yellow-800/60 text-yellow-300 px-3 py-1 rounded transition-colors"
                      >
                        Resume after {stage}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-12 text-center text-gray-500 text-sm">
          <p>Press <kbd className="bg-gray-800 px-2 py-1 rounded">⚙️ Settings</kbd> in the main app to configure models and API keys</p>
        </div>
      </div>
    </div>
  );
}
