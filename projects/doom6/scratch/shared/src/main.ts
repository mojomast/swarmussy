import { initUI, setEngineStatusForUI } from './ui/index';
import { saveEditorState, loadEditorState } from './editor/persistence';
import { startTickLoop, stopTickLoop } from './engine/ticker';
import { LevelEditor } from './editor/levels/level_editor';
import { loadLevelIntoWorld } from './game/level_loader';
import { World } from './engine/core';

// Simple bootstrap: create a world, optionally load a level from URL param, then start loop
const root = document.getElementById('root');
let world = new World();
let tickActive = false;

function parseQueryParam(name: string): string | null {
  const params = new URLSearchParams(window.location.search);
  return params.get(name);
}

const loadLevelParam = parseQueryParam('loadLevel');
if (root) {
  initUI(root, {
    onPlay: () => {
      if (!tickActive) {
        startTickLoop();
        tickActive = true;
      }
      setEngineStatusForUI(true);
    },
    onStop: () => {
      if (tickActive) {
        stopTickLoop();
        tickActive = false;
      }
      setEngineStatusForUI(false);
    },
    onSave: async () => {
      await saveEditorState('current', { timestamp: Date.now() });
      console.log('Editor state saved (placeholder)');
    },
    onLoad: async () => {
      const data = await loadEditorState('current');
      console.log('Loaded editor state (placeholder):', data);
    },
    onEdit: () => {
      console.log('Edit mode toggled (placeholder)');
    }
  });

  // If a level filename is provided, load it into the world immediately
  if (loadLevelParam) {
    const levelJson = LevelEditor.loadLevel(loadLevelParam);
    if (levelJson) {
      loadLevelIntoWorld(world, levelJson);
      console.log('Loaded level into world on startup:', loadLevelParam);
    }
  }
}
