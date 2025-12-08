import React, { useEffect, useState } from 'react';
import { fetchHealth } from '../utils/api.js';

function HealthPanel(){
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchHealth()
      .then((data) => { setHealth(data); setLoading(false); })
      .catch((err) => { setError(err.message || 'Error fetching health'); setLoading(false); });
  }, []);

  if (loading) return <div>Loading health...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <section aria-label="health" style={{ border: '1px solid #ccc', padding: 12, borderRadius: 6 }}>
      <h2>Health</h2>
      <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(health, null, 2)}</pre>
    </section>
  );
}

export default HealthPanel;
