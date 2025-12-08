import React from 'react';

export type EditorUIProps = {
  onNewLevel?: () => void;
  onLoadLevel?: () => void;
  onSave?: () => void;
  children?: React.ReactNode;
};

/**
 * EditorUI
 * Lightweight chrome for the level editor. Provides a header with actions and a content container.
 */
const EditorUI: React.FC<EditorUIProps> = ({ onNewLevel, onLoadLevel, onSave, children }) => {
  return (
    <div className="editor-ui" aria-label="Editor UI">
      <header
        style={{ display: 'flex', gap: 8, alignItems: 'center', padding: '8px 12px', borderBottom: '1px solid #e2e8f0' }}
      >
        <button onClick={onNewLevel} aria-label="New level">New</button>
        <button onClick={onLoadLevel} aria-label="Load level">Load</button>
        <button onClick={onSave} aria-label="Save level">Save</button>
        <span style={{ marginLeft: 'auto', fontWeight: 600 }}>Level Editor</span>
      </header>
      <main style={{ padding: 12 }}>{children}</main>
    </div>
  );
};

export default EditorUI;
export type { EditorUIProps };
