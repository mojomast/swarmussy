import React, { useEffect, useMemo, useState } from 'react';
import { getProfile, saveProfile, loadProfile, deleteProfile } from './profile.js';

// Simple avatar emoji picker options
const AVATARS = ['\ud83d\ude0e', '\ud83e\uddd9\u200d\u2642\ufe0f', '\ud83e\udddf\u200d\u2642\ufe0f', '\ud83e\udddb\u200d\u2642\ufe0f', '\ud83d\udc7d', '\ud83d\udc32', '\ud83d\udc3a', '\ud83d\udc35', '\ud83e\uddd9\u200d\u2640\ufe0f', '\ud83e\udd8a'];

function AvatarPicker({ value, onChange }) {
  return (
    <div role="group" aria-label="Avatar selector" className="avatar-picker" >
      {AVATARS.map((a) => (
        <button
          key={a}
          type="button"
          aria-pressed={value === a}
          className={`avatar-btn ${value === a ? 'selected' : ''}`}
          onClick={() => onChange(a)}
          title={a}
        >
          <span aria-label={`avatar ${a}`} role="img">{a}</span>
        </button>
      ))}
    </div>
  );
}

export default function ProfilePanel({ onBootstrapped }) {
  const [name, setName] = useState('');
  const [avatar, setAvatar] = useState('\ud83d\ude0e');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [currentProfile, setCurrentProfile] = useState(null);
  const AUTO_LOAD_KEY = 'doomClone.autoLoad';
  const [autoLoad, setAutoLoad] = useState(() => {
    const v = localStorage.getItem(AUTO_LOAD_KEY);
    return v === null ? true : v === 'true';
  });

  // Load profile on mount if available
  useEffect(() => {
    let mounted = true;
    async function bootstrap() {
      // Load current profile for summary
      try {
        const prof = await loadProfile();
        if (mounted && prof) {
          setName(prof.name || '');
          setAvatar(prof.avatar || '\ud83d\ude0e');
          setCurrentProfile(prof);
          if (typeof onBootstrapped === 'function') {
            onBootstrapped(prof);
          }
        }
      } catch (_) {
        // ignore bootstrap errors
      }
    }
    bootstrap();
    return () => {
      mounted = false;
    };
  }, [onBootstrapped]);

  // Persist auto-load setting
  useEffect(() => {
    localStorage.setItem(AUTO_LOAD_KEY, String(autoLoad));
  }, [autoLoad]);

  // Validation: name required, avatar is chosen from list but default provided
  const canSave = useMemo(() => {
    return typeof name === 'string' && name.trim().length > 0;
  }, [name]);

  async function handleSave(e) {
    e?.preventDefault();
    setError('');
    if (!canSave) {
      setError('Please enter a name for your profile.');
      return;
    }
    setLoading(true);
    try {
      const saved = await saveProfile({ name: name.trim(), avatar });
      setMessage('Profile saved.');
      setCurrentProfile(saved);
      // Clear message after a moment
      setTimeout(() => setMessage(''), 1500);
    } catch (err) {
      setError('Failed to save profile.');
    } finally {
      setLoading(false);
    }
  }

  async function handleLoad() {
    setError('');
    setMessage('');
    setLoading(true);
    try {
      const prof = await loadProfile();
      if (prof) {
        setName(prof.name || '');
        setAvatar(prof.avatar || '\ud83d\ude0e');
        setCurrentProfile(prof);
        setMessage('Profile loaded.');
      } else {
        setError('No profile found.');
      }
    } catch {
      setError('Failed to load profile.');
    } finally {
      setLoading(false);
      setTimeout(() => setMessage(''), 1500);
    }
  }

  async function handleDelete() {
    setError('');
    setMessage('');
    setLoading(true);
    try {
      await deleteProfile();
      setName('');
      setAvatar('\ud83d\ude0e');
      setCurrentProfile(null);
      setMessage('Profile deleted.');
    } catch {
      setError('Failed to delete profile.');
    } finally {
      setLoading(false);
      setTimeout(() => setMessage(''), 1500);
    }
  }

  return (
    <section aria-labelledby="profile-title" className="profile-panel" style={styles.panel}>
      <h2 id="profile-title" style={styles.title}> Doom Clone Profile </h2>
      <div style={styles.summary} aria-label="Current profile summary">
        <span style={styles.summaryLabel}>Current profile:</span>
        {currentProfile ? (
          <span style={styles.summaryContent}>
            <span className="avatar" style={styles.smallAvatar} aria-label="current avatar">{currentProfile.avatar || '\ud83d\ude0e'}</span>
            <span style={styles.summaryName}>{currentProfile.name || ''}</span>
          </span>
        ) : (
          <span style={styles.summaryContent}>None</span>
        )}
      </div>
      <div style={styles.autoRow}>
        <label htmlFor="autoLoad" style={styles.label}>Auto-load on startup</label>
        <input
          id="autoLoad"
          type="checkbox"
          checked={autoLoad}
          onChange={(e) => setAutoLoad(e.target.checked)}
          aria-label="Auto-load on startup"
        />
      </div>
      <form onSubmit={handleSave} aria-label="Profile form" style={styles.form}>
        <div style={styles.field}>
          <label htmlFor="name" style={styles.label}>Name</label>
          <input
            id="name"
            name="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter your name"
            aria-invalid={!!error}
            aria-describedby={error ? 'profile-error' : undefined}
            style={styles.input}
          />
        </div>
        <div style={styles.field}>
          <span style={styles.label}>Avatar</span>
          <AvatarPicker value={avatar} onChange={setAvatar} />
        </div>
        <div style={styles.actions}>
          <button type="submit" disabled={loading} aria-label="Save profile" style={styles.buttonPrimary}>
            {loading ? 'Saving...' : 'Save Profile'}
          </button>
          <button type="button" onClick={handleLoad} disabled={loading} aria-label="Load profile" style={styles.buttonSecondary}>
            Load
          </button>
          <button type="button" onClick={handleDelete} disabled={loading} aria-label="Delete profile" style={styles.dangerButton}>
            Delete
          </button>
        </div>
        {error && (
          <div id="profile-error" role="alert" aria-live="polite" style={styles.error}>{error}</div>
        )}
        {message && (
          <div role="status" aria-live="polite" style={styles.success}>{message}</div>
        )}
      </form>
    </section>
  );
}

const styles = {
  panel: {
    border: '1px solid #ddd',
    borderRadius: 8,
    padding: 20,
    background: '#fff',
    maxWidth: 700,
  },
  title: {
    margin: 0,
    marginBottom: 12,
    fontSize: 18,
  },
  summary: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '6px 0 12px 0',
  },
  summaryLabel: { fontWeight: 700 },
  summaryContent: { display: 'inline-flex', alignItems: 'center', gap: 8 },
  smallAvatar: { width: 20, height: 20, borderRadius: 9999, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', background: '#2a326b', color: 'white', fontSize: 12 },
  summaryName: { fontWeight: 600, fontSize: 14 },
  autoRow: { display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 },
  form: {
    display: 'grid',
    gridTemplateColumns: '1fr',
    gap: 12,
  },
  field: {
    display: 'flex',
    flexDirection: 'column',
  },
  label: {
    fontWeight: 600,
    marginBottom: 6,
  },
  input: {
    padding: '8px 12px',
    fontSize: 16,
    borderRadius: 6,
    border: '1px solid #ccc',
  },
  avatarPicker: {},
  actions: {
    display: 'flex',
    gap: 10,
    alignItems: 'center',
  },
  buttonPrimary: {
    padding: '10px 14px',
    background: '#4a90e2',
    color: '#fff',
    border: 'none',
    borderRadius: 6,
    cursor: 'pointer',
  },
  buttonSecondary: {
    padding: '10px 12px',
    background: '#eee',
    border: '1px solid #ccc',
    borderRadius: 6,
    cursor: 'pointer',
  },
  dangerButton: {
    padding: '10px 12px',
    background: '#f44336',
    color: '#fff',
    border: 'none',
    borderRadius: 6,
    cursor: 'pointer',
  },
  error: {
    color: '#c00',
  },
  success: {
    color: '#2e7d32',
  },
};

export { ProfilePanel as default };
