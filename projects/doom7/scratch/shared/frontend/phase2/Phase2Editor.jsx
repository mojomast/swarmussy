import React, { useEffect, useState, useCallback } from 'react';

// Phase 2 Editor screen scaffold
// - Loads initial level data from /v2/editor/level
// - Allows editing a JSON config with a JSON-friendly editor (textarea)
// - Persists via POST /v2/editor/level
// - Keyboard accessibility and basic ARIA semantics

function Phase2Editor() {
  const [level, setLevel] = useState(null);
  const [configText, setConfigText] = useState("{}");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saveStatus, setSaveStatus] = useState(null);

  // Load initial level data
  useEffect(() => {
    let mounted = true;
    fetch('/v2/editor/level')
      .then(res => {
        if (!res.ok) throw new Error('Failed to load level');
        return res.json();
      })
      .then(data => {
        if (!mounted) return;
        const lvl = data?.level ?? data;
        setLevel(lvl);
        const cfg = (lvl && lvl.config) ? lvl.config : {};
        setConfigText(JSON.stringify(cfg, null, 2));
        setLoading(false);
      })
      .catch(() => {
        if (mounted) {
          setError('Unable to load level data');
          setLoading(false);
        }
      });
    return () => { mounted = false; };
  }, []);

  const saveLevel = useCallback(async () => {
    setError(null);
    setSaveStatus(null);
    let parsed;
    try {
      parsed = JSON.parse(configText);
    } catch (e) {
      setError('Invalid JSON');
      setSaveStatus('error');
      return;
    }
    const payload = {
      level: {
        ...(level || {}),
        config: parsed
      }
    };
    try {
      const res = await fetch('/v2/editor/level', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error('Save failed');
      const updated = await res.json();
      setLevel(updated?.level ?? level);
      setSaveStatus('ok');
    } catch (e) {
      setError('Failed to save level');
      setSaveStatus('error');
    }
  }, [configText, level]);

  // Keyboard shortcut: Ctrl/Cmd+S to save
  useEffect(() => {
    const onKey = (e) => {
      const isMac = navigator.platform.toLowerCase().includes('mac');
      if ((isMac && e.metaKey && e.key.toLowerCase() === 's') || (!isMac && e.ctrlKey && e.key.toLowerCase() === 's')) {
        e.preventDefault();
        saveLevel();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [saveLevel]);

  const reset = () => {
    const cfg = level?.config ?? {};
    setConfigText(JSON.stringify(cfg, null, 2));
  };

  const loadSample = () => {
    const sample = {
      gridSize: 16,
      entities: []
    };
    setConfigText(JSON.stringify(sample, null, 2));
  };

  return (
    <section aria-label="Phase 2 Editor" role="region" style={styles.section}>
      <h2 style={styles.h2}>Phase 2 Editor</h2>
      {loading && <p aria-live="polite">Loading level...</p>}
      {error && <div role="alert" aria-live="assertive" style={styles.error}>{error}</div>}
      {!loading && (
        <div style={styles.grid}>
          <div style={styles.left}>
            <label htmlFor="phase2-editor-json" style={styles.label}>Level JSON</label>
            <textarea
              id="phase2-editor-json"
              aria-label="Level JSON editor"
              value={configText}
              onChange={(e) => setConfigText(e.target.value)}
              style={styles.textarea}
              spellCheck={false}
            />
            <div style={styles.toolbar}>
              <button aria-label="Reset Example" onClick={reset} style={styles.btn}>Reset</button>
              <button aria-label="Load Sample" onClick={loadSample} style={styles.btn}>Load Sample</button>
              <button aria-label="Save Level" onClick={saveLevel} style={styles.btnPrimary}>Save</button>
              {saveStatus === 'ok' && <span aria-live="polite" style={styles.good}>Saved</span>}
              {saveStatus === 'error' && <span aria-live="polite" style={styles.error}>Error</span>}
            </div>
          </div>
          <aside style={styles.right}>
            <label style={styles.label}>Preview</label>
            <pre aria-label="Level JSON preview" style={styles.preview}>{configText}</pre>
          </aside>
        </div>
      )}
    </section>
  );
}

const styles = {
  section: { padding: '16px', border: '1px solid #e5e7eb', borderRadius: 8, background: '#fff' },
  h2: { fontSize: 20, margin: '0 0 12px' },
  grid: { display: 'flex', gap: 16, alignItems: 'flex-start' },
  left: { flex: 1, minWidth: 300 },
  right: { width: 360, maxWidth: '40%', minWidth: 260 },
  label: { display: 'block', fontSize: 12, color: '#6b7280', marginBottom: 6 },
  textarea: { width: '100%', height: 320, fontFamily: 'monospace', fontSize: 12, padding: 10, resize: 'vertical' },
  toolbar: { marginTop: 8, display: 'flex', gap: 8, alignItems: 'center' },
  btn: { padding: '6px 12px', borderRadius: 6, border: '1px solid #cbd5e1', background: '#f8fafc' },
  btnPrimary: { padding: '6px 12px', borderRadius: 6, border: '1px solid #1f83ff', background: '#1f77ff', color: '#fff' },
  good: { color: 'green', marginLeft: 8 },
  error: { color: 'red' },
  preview: { background: '#0b1020', color: '#e5e7eb', padding: 10, borderRadius: 6, height: 320, overflow: 'auto', whiteSpace: 'pre-wrap' }
};

export default Phase2Editor;
