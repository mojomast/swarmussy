import { useState, useEffect } from 'preact/hooks';
import { 
  X, 
  Sparkles, 
  Bot, 
  Zap, 
  MessageSquare,
  GitBranch,
  Layers,
  ArrowRight
} from 'lucide-preact';

interface Props {
  onClose: (dontShowAgain: boolean) => void;
}

const SPLASH_DISMISSED_KEY = 'swarm_splash_dismissed';

export function useSplashScreen() {
  const [showSplash, setShowSplash] = useState(false);

  useEffect(() => {
    const dismissed = localStorage.getItem(SPLASH_DISMISSED_KEY);
    if (!dismissed) {
      setShowSplash(true);
    }
  }, []);

  const openSplash = () => setShowSplash(true);
  const closeSplash = (dontShowAgain: boolean) => {
    if (dontShowAgain) {
      localStorage.setItem(SPLASH_DISMISSED_KEY, 'true');
    }
    setShowSplash(false);
  };

  return { showSplash, openSplash, closeSplash };
}

export function SplashScreen({ onClose }: Props) {
  const [dontShowAgain, setDontShowAgain] = useState(false);

  const handleClose = () => {
    onClose(dontShowAgain);
  };

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-[100] p-4 backdrop-blur-sm">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden">
        {/* Header with gradient */}
        <div className="bg-gradient-to-r from-purple-900/50 to-blue-900/50 p-6 border-b border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl flex items-center justify-center">
                <Bot className="text-white" size={28} />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">SwarmChat</h1>
                <p className="text-purple-300 text-sm">AI-Powered Multi-Agent Development</p>
              </div>
            </div>
            <button 
              onClick={handleClose}
              className="text-gray-400 hover:text-white p-2 rounded-lg hover:bg-gray-800/50 transition-colors"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* What is this */}
          <div>
            <h2 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
              <Sparkles className="text-purple-400" size={20} />
              What is SwarmChat?
            </h2>
            <p className="text-gray-300 text-sm leading-relaxed">
              SwarmChat is a multi-agent AI development system that uses specialized AI agents 
              working together to build your software projects. Think of it as having a team of 
              AI developers - an Architect, Backend Developer, Frontend Developer, QA Engineer, 
              DevOps, and Technical Writer - all collaborating on your project.
            </p>
          </div>

          {/* How it works */}
          <div>
            <h2 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
              <Zap className="text-yellow-400" size={20} />
              How It Works
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                <div className="flex items-center gap-2 mb-2">
                  <MessageSquare className="text-purple-400" size={18} />
                  <span className="font-medium text-white text-sm">1. Devussy Interview</span>
                </div>
                <p className="text-gray-400 text-xs">
                  Chat with our AI to define your project requirements and architecture.
                </p>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                <div className="flex items-center gap-2 mb-2">
                  <GitBranch className="text-blue-400" size={18} />
                  <span className="font-medium text-white text-sm">2. DevPlan Generation</span>
                </div>
                <p className="text-gray-400 text-xs">
                  AI generates a detailed development plan with phases and tasks.
                </p>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                <div className="flex items-center gap-2 mb-2">
                  <Layers className="text-green-400" size={18} />
                  <span className="font-medium text-white text-sm">3. Swarm Execution</span>
                </div>
                <p className="text-gray-400 text-xs">
                  Agents work in parallel to complete tasks and build your project.
                </p>
              </div>
            </div>
          </div>

          {/* Getting Started */}
          <div className="bg-blue-900/20 border border-blue-800/50 rounded-lg p-4">
            <h3 className="font-medium text-blue-300 mb-2">🚀 Getting Started</h3>
            <ol className="text-sm text-gray-300 space-y-1">
              <li className="flex items-start gap-2">
                <span className="text-blue-400 font-medium">1.</span>
                Create or select a project from the project selector
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-400 font-medium">2.</span>
                Click "Start Devussy Pipeline" to begin the interview process
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-400 font-medium">3.</span>
                Answer questions about your project - type /done when complete
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-400 font-medium">4.</span>
                Watch the swarm agents build your project in real-time!
              </li>
            </ol>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-700 bg-gray-900/50 flex items-center justify-between">
          <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={dontShowAgain}
              onChange={(e) => setDontShowAgain(e.currentTarget.checked)}
              className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-purple-500 focus:ring-purple-500 focus:ring-offset-gray-900"
            />
            Don't show this again
          </label>
          <button
            onClick={handleClose}
            className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white font-medium py-2 px-6 rounded-lg transition-all flex items-center gap-2"
          >
            Get Started
            <ArrowRight size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
