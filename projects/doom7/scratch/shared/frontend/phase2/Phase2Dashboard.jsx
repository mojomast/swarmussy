import React from 'react';

// Phase 2 Dashboard: small widget collection for runtime stats and status

function Phase2Dashboard() {
  // Minimal, mock data; real data from /v2/engine/render_stats could populate props/state in a real app
  const stats = {
    framesRendered: 1423,
    avgFps: 58.6,
    memoryMb: 512
  };

  return (
    <section aria-label="Phase 2 Dashboard" role="region" style={styles.section}>
      <h2 style={styles.h2}>Phase 2 Dashboard</h2>
      <div style={styles.grid}>
        <Widget title="Frames" value={stats.framesRendered} unit="fps" />
        <Widget title="Avg FPS" value={stats.avgFps} unit="fps" />
        <Widget title="Memory" value={stats.memoryMb} unit="MB" />
      </div>
    </section>
  );
}

function Widget({ title, value, unit }) {
  return (
    <div aria-label={title} style={styles.widget}>
      <div style={styles.widgetTitle}>{title}</div>
      <div style={styles.widgetValue}>{value} {unit}</div>
    </div>
  );
}

const styles = {
  section: { padding: '16px', border: '1px solid #e5e7eb', borderRadius: 8, background: '#fff', marginTop: 16 },
  h2: { fontSize: 20, margin: '0 0 12px' },
  grid: { display: 'flex', gap: 12 },
  widget: { padding: 12, borderRadius: 8, border: '1px solid #e2e8f0', minWidth: 120, textAlign: 'center', background: '#f8fafc' },
  widgetTitle: { fontSize: 12, color: '#6b7280' },
  widgetValue: { fontSize: 16, fontWeight: 600, marginTop: 6 }
};

export default Phase2Dashboard;
