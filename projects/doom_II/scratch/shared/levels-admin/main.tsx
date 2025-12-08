import React from 'react';
import ReactDOM from 'react-dom/client';

// Simple wrapper; could be extended to render the list detail modal wiring using proper components
const App: React.FC = () => (
  <div style={{ padding: 16, color: 'white' }}>
    Levels Admin UI integrated into app
  </div>
);

const root = document.getElementById('root');
if (root) {
  // This would mount in a real SPA; we keep minimal here for task
  // @ts-ignore
  ReactDOM.createRoot(root).render(<App />);
}
