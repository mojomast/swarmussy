import React from 'react';

// Phase 2 UI Flow: Phase 2 navigation reflecting new engine core
// This component renders a keyboard-accessible Phase 2 navigation

type Phase2Item = {
  id: string;
  label: string;
  ui_state: 'enabled' | 'disabled' | 'hidden';
};

type Phase2FlowProps = {
  items: Phase2Item[];
  onNavigate?: (id: string) => void;
};

export const Phase2Flow: React.FC<Phase2FlowProps> = ({ items, onNavigate }) => {
  // Keyboard navigation: Enter / Space to activate
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>, itemId: string) => {
    if (e.key === 'Enter' || e.key === ' ') {
      onNavigate?.(itemId);
    }
  };

  return (
    <nav aria-label="Phase 2 navigation" role="navigation">
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

export default Phase2Flow;
