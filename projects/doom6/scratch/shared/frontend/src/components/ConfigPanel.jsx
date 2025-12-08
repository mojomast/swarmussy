import React, { useEffect, useState } from 'react';
import { fetchConfig } from '../utils/api.js';

function ConfigPanel(){
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchConfig()
      .then((data) => { setConfig(data); setLoading(false); })
      .catch((err) => { setError(err.message || 'Error fetching config'); setLoading(false); });
  }, []);

  if (loading) return <div>Loading config...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <section aria-label="config" style={{ border: '1px solid #ccc', padding: 12, borderRadius: 6 }}>
      <h2>Config</h2>
      <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(config, null, 2)}</pre>
    </section>
  );
}

export default ConfigPanel;
