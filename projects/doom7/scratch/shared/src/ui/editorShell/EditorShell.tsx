import React, { useEffect, useMemo, useState } from 'react';
import EditorController from './EditorController';
import type { Level, Entity, Asset } from './types';

// Minimal, framework-agnostic shell using simple React flags
export const EditorShell: React.FC = () => {
  const [controller] = useState(() => new EditorController());
  const [level, setLevel] = useState<Level | null>(controller.getLevel());
  const [panel, setPanel] = useState<string>(controller.getPanel());

  useEffect(() => {
    // Sync local with controller on mount
    setLevel(controller.getLevel());
    setPanel(controller.getPanel());
  }, []);

  const json = useMemo(() => level ? JSON.stringify(level, null, 2) : '', [level]);

  return (
    <div role="application" aria-label="In-engine Editor Shell" style={{ display: 'flex', height: '100%', width: '100%' }}>
      <aside style={{ width: 240, borderRight: '1px solid #ddd', padding: 8 }}>
        <nav>
          {(['Levels','Entities','Assets','Inspector'] as const).map((p) => (
            <button key={p} onClick={() => setPanel(p)} aria-label={`Go to ${p}`} style={{ display: 'block', width: '100%', padding: 8, margin: '6px 0' }}>{p}</button>
          ))}
        </nav>
      </aside>
      <main style={{ flex: 1, padding: 16 }}>
        <h2>Editor: {panel}</h2>
        <pre style={{ whiteSpace: 'pre-wrap' }}>{json}</pre>
      </main>
    </div>
  );
};
export default EditorShell;
