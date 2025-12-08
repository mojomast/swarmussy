import React, { useEffect, useState, useCallback } from 'react';

// Phase 2 Flow: navigation and editor screens
// This component wires to Phase 2 API surface at /v2 endpoints.
// Accessible navigation with ARIA roles and keyboard navigation.

const Phase2Flow = () => {
  const [level, setLevel] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [liveEvents, setLiveEvents] = useState([]);

  // Fetch initial level data and subscribe to events
  useEffect(() => {
    let mounted = true;

    // Load initial level data
    fetch('/v2/editor/level')
      .then(res => {
        if (!res.ok) throw new Error('Network response was not ok');
        return res.json();
      })
      .then(data => {
        if (mounted) {
          const lvl = data?.level ?? data ?? null;
          setLevel(lvl);
          setLoading(false);
        }
      })
      .catch(() => {
        if (mounted) {
          setError('Failed to load level data.');
          setLoading(false);
        }
      });

    // Optional Server-Sent Events for live updates
    if (typeof window !== 'undefined' && typeof window.EventSource === 'function') {
      try {
        const es = new window.EventSource('/v2/events/stream');
        es.onmessage = (ev) => {
          try {
            const data = JSON.parse(ev.data);
            setLiveEvents(prev => [data, ...prev].slice(0, 6));
          } catch (e) {
            // ignore parse errors
          }
        };
        es.onerror = () => es.close();
        // cleanup on unmount
        return () => {
          es.close();
          mounted = false;
        };
      } catch {
        // SSE not available
      }
    }

    return () => { mounted = false; };
  }, []);

  const saveLevel = async (payload) => {
    try {
      const res = await fetch('/v2/editor/level', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error('Save failed');
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
    <section role="region" aria-label="Phase 2 Flow">
      <h2>Phase 2 Flow</h2>
      {loading && <p role="status">Loading...</p>}
      {error && <div role="alert" aria-live="assertive" style={{color:'red'}}>{error}</div>}
      {!loading && !error && (
        <div>
          <p>Current Level: {level ? JSON.stringify(level) : 'None'}</p>
          <button aria-label="Save Level" onClick={() => saveLevel({ level })}>Save</button>
        </div>
      )}
      {liveEvents.length > 0 && (
        <div aria-label="Live Event Feed" style={{ marginTop: 12, padding: 12, border: '1px solid #e5e7eb', borderRadius: 6 }}>
          <strong>Live Events</strong>
          <ul>
            {liveEvents.map((ev, idx) => (
              <li key={idx}>{typeof ev === 'string' ? ev : JSON.stringify(ev)}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
};

export default Phase2Flow;
