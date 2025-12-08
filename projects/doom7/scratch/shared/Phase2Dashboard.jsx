import React from 'react';

type Phase2DashboardProps = {
  summary: string;
  status?: string;
  onRun?: () => void;
};

export const Phase2Dashboard: React.FC<Phase2DashboardProps> = ({ summary, status = 'idle', onRun }) => {
  return (
    <section aria-label="Phase 2 Dashboard" style={{ padding: 16, border: '1px solid #e5e7eb', borderRadius: 8 }}>
      <h2 style={{ margin: 0, fontSize: 20 }}>Phase 2 Dashboard</h2>
      <p style={{ marginTop: 8 }}>{summary}</p>
      <p>Status: <strong>{status}</strong></p>
      <button onClick={onRun} aria-label="Run Phase 2" style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #ccc', background: '#fff' }}>Run</button>
    </section>
  );
};

export default Phase2Dashboard;
