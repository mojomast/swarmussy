import { useState, useEffect } from 'preact/hooks';
import { updateSettings, setDevussyMode, fetchDevussyStatus } from '../lib/api';
import { X } from 'lucide-preact';

export function SettingsModal({ onClose, settings: initialSettings }: any) {
  const [localSettings, setLocalSettings] = useState(initialSettings || {});
  const [devussyStatus, setDevussyStatus] = useState<any>({});

  useEffect(() => {
    fetchDevussyStatus().then(setDevussyStatus);
  }, []);

  const handleSave = async () => {
    await updateSettings(localSettings);
    onClose();
  };

  const toggleDevussy = async () => {
    const newState = !devussyStatus.mode_enabled;
    await setDevussyMode(newState);
    setDevussyStatus({ ...devussyStatus, mode_enabled: newState });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-700 rounded-lg w-[500px] max-h-[80vh] flex flex-col shadow-2xl">
        <div className="p-4 border-b border-gray-800 flex justify-between items-center">
          <h2 className="text-lg font-bold text-white">Settings</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X size={20} />
          </button>
        </div>
        
        <div className="p-6 overflow-y-auto space-y-6">
          <div className="space-y-2">
            <label className="text-sm text-gray-400">Username</label>
            <input 
              type="text" 
              value={localSettings.username || ''}
              onInput={(e) => setLocalSettings({...localSettings, username: e.currentTarget.value})}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white"
            />
          </div>

          <div className="space-y-4 pt-4 border-t border-gray-800">
            <h3 className="text-white font-bold">Devussy Integration</h3>
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Devussy Mode</span>
              <button 
                onClick={toggleDevussy}
                className={`px-3 py-1 rounded ${
                  devussyStatus.mode_enabled ? 'bg-purple-600 text-white' : 'bg-gray-800 text-gray-400'
                }`}
              >
                {devussyStatus.mode_enabled ? 'Enabled' : 'Disabled'}
              </button>
            </div>
            {devussyStatus.available ? (
              <div className="text-xs text-green-400">Devussy core is available</div>
            ) : (
              <div className="text-xs text-red-400">Devussy core not found</div>
            )}
          </div>

          <div className="space-y-2 pt-4 border-t border-gray-800">
            <h3 className="text-white font-bold">Models</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-500">Architect Model</label>
                <input 
                  type="text" 
                  value={localSettings.architect_model || ''}
                  onInput={(e) => setLocalSettings({...localSettings, architect_model: e.currentTarget.value})}
                  className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-white"
                />
              </div>
              <div>
                <label className="text-xs text-gray-500">Swarm Model</label>
                <input 
                  type="text" 
                  value={localSettings.swarm_model || ''}
                  onInput={(e) => setLocalSettings({...localSettings, swarm_model: e.currentTarget.value})}
                  className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-white"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-gray-800 flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 text-gray-300 hover:text-white">Cancel</button>
          <button onClick={handleSave} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}
