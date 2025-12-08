import React from 'react';

export type UIBridge = {
  onKeyDown?: (e: KeyboardEvent) => void;
  onMouse?: (e: MouseEvent) => void;
};

export const UIRoot = ({ children }: { children?: React.ReactNode }) => {
  return (
    <div style={{ height: '100%', width: '100%', display: 'flex', flexDirection: 'column' }}>
      {children}
    </div>
  );
};

export default UIRoot;
