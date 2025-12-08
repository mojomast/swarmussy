import React from 'react';

// Phase 1 UI Flow: simplified to reflect consolidated scope
// This component renders a lightweight Phase 1 navigation with keyboard-accessible controls

type Phase1Item = {
  id: string;
  label: string;
  ui_state: 'enabled' | 'disabled' | 'hidden';
};

type Phase1FlowProps = {
  items: Phase1Item[];
  onNavigate?: (id: string) => void;
};

export const Phase1Flow: React.FC<Phase1FlowProps> = ({ items, onNavigate }) => {
  // Keyboard navigation: arrow keys move focus, Enter to select
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>, itemId: string) => {
    if (e.key === 'Enter' || e.key === ' ') {
      onNavigate?.(itemId);
    }
  };

  return (
    <nav aria-label="Phase 1 navigation" role="navigation">
      <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', gap: 8 }}>
        {items.map((it) => (
          <li key={it.id}>
            {it.ui_state === 'hidden' ? null : (
              <button
                onClick={() => onNavigate?.(it.id)}
                onKeyDown={(e) => handleKeyDown(e, it.id)}
                disabled={it.ui_state === 'disabled'}
                aria-disabled={it.ui_state === 'disabled'}
                style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #ccc', background: '#fff' }}
              >
                {it.label}
              </button>
            )}
          </li>
        ))}
      </ul>
    </nav>
  );
};

export default Phase1Flow;
