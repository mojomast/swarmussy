import React from 'react';
import HealthPanel from './components/HealthPanel.jsx';
import ConfigPanel from './components/ConfigPanel.jsx';

export default function App(){
  return (
    <div className="app" style={{ padding: 16 }}>
      <h1>Health & Config</h1>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <HealthPanel />
        <ConfigPanel />
      </div>
    </div>
  );
}
