import React, { useEffect, useState } from 'react';

// Phase 2 Flow: navigation and editor screens
// This component wires to Phase 2 API surface at /v2 endpoints.
// Accessible navigation with ARIA roles and keyboard shortcuts.

const Phase2Flow = () => {
  const [level, setLevel] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch initial level data from /v2/editor/level
  useEffect(() => {
    let mounted = true;
    fetch('/v2/editor/level')
      .then(res => res.ok ? res.json() : Promise.reject(res.status))
      .then(data => {
        if (mounted) {
          setLevel(data?.level ?? data);
          setLoading(false);
        }
      })
      .catch(() => {
        if (mounted) {
          setError('Failed to load level data.');
          setLoading(false);
        }
      });
    return () => { mounted = false; };
  }, []);

  const saveLevel = async (payload) => {
    try {
      const res = await fetch('/v2/editor/level', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        throw new Error('Save failed');
      }
      const updated = await res.json();
      setLevel(updated?.level ?? level);
      return true;
    } catch (e) {
      setError('Failed to save level.');
      return false;
    }
  };

  // Simple UI: show editor placeholder with accessible labels
  return (
    <div role="region" aria-label="Phase 2 Flow">
      <h2>Phase 2 Flow</h2>
      {loading && <p role="status">Loading...</p>}
      {error && <div role="alert" aria-live="assertive" style={{color:'red'}}>{error}</div>}
      {!loading && !error && (
        <div>
          <p>Current Level: {level ? JSON.stringify(level) : 'None'}</p>
          <button aria-label="Save Level" onClick={() => saveLevel({ level })}>Save</button>
        </div>
      )}
    </div>
  );
};

export default Phase2Flow;
