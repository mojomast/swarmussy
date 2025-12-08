import React, { useEffect, useState } from 'react';

// Phase 2 Dashboard: runtime overview
// Consumes /v2/engine/render_stats SSE stream for live metrics

const Phase2Dashboard = () => {
  const [stats, setStats] = useState({});
  const [error, setError] = useState(null);

  useEffect(() => {
    // Setup SSE connection to /v2/events/stream
    const es = new EventSource('/v2/events/stream');
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        setStats(prev => ({ ...prev, ...data }));
      } catch (err) {
        // ignore parse errors
      }
    };
    es.onerror = () => {
      setError('Connection to live stream failed.');
    };
    return () => es.close();
  }, []);

  return (
    <section aria-label="Phase 2 Dashboard" role="region">
      <h2>Phase 2 Dashboard</h2>
      {error && <div role="alert" aria-live="assertive" style={{color:'red'}}>{error}</div>}
      <div aria-label="stats" role="group">
        <pre>{JSON.stringify(stats, null, 2)}</pre>
      </div>
    </section>
  );
};

export default Phase2Dashboard;
