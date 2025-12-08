import React, { useEffect, useState } from 'react';

/**
 * Users UI Page
 * - Fetches user list from backend (/api/users)
 * - Displays users in a responsive grid
 * - Provides a form to create new users with client-side validation
 * - Uses Authorization header (Bearer testtoken) for backend compatibility
 */

const styles = {
  page: {
    fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI',
    color: '#1f2937',
    padding: '24px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: 700,
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
    gap: 16,
  },
  card: {
    border: '1px solid #e5e7eb',
    borderRadius: 12,
    padding: 16,
    background: '#fff',
    display: 'flex',
    gap: 12,
    alignItems: 'center',
    boxShadow: '0 1px 2px rgba(0,0,0,.04)',
  },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#3b82f6',
    color: '#fff',
    fontWeight: 700,
    fontSize: 14,
  },
  userInfo: {
    display: 'flex',
    flexDirection: 'column',
  },
  name: { fontWeight: 600, fontSize: 16, marginBottom: 4 },
  email: { fontSize: 12, color: '#6b7280' },
  formCard: {
    border: '1px solid #e5e7eb',
    borderRadius: 12,
    padding: 16,
    background: '#fff',
    marginTop: 24,
  },
  formRow: { display: 'flex', gap: 12, marginBottom: 12, flexWrap: 'wrap' },
  label: { display: 'block', fontSize: 12, color: '#374151', marginBottom: 6 },
  input: {
    padding: '10px 12px',
    borderRadius: 8,
    border: '1px solid #d1d5db',
    minWidth: 180,
    fontSize: 14,
  },
  select: { ... ({} as any) },
  error: { color: '#b91c1c', fontSize: 12, marginTop: 4 },
  button: {
    padding: '10px 16px',
    borderRadius: 8,
    border: '1px solid #1f6feb',
    background: '#1f6feb',
    color: '#fff',
    fontWeight: 600,
    cursor: 'pointer',
  },
  buttonSecondary: {
    padding: '10px 14px',
    borderRadius: 8,
    border: '1px solid #d1d5db',
    background: '#f3f4f6',
    color: '#111827',
    fontWeight: 600,
    cursor: 'pointer'
  },
  hint: { fontSize: 12, color: '#6b7280', marginTop: 6 },
  loading: { fontSize: 14, color: '#6b7280' },
  divider: { height: 1, background: '#e5e7eb', margin: '14px 0' },
};

function Avatar({ name }) {
  const initials = name?.trim().charAt(0) ? name.trim().charAt(0).toUpperCase() : '?';
  return <div style={styles.avatar}>{initials}</div>;
}

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // form state
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('member');
  const [formError, setFormError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/users', {
        headers: {
          'Authorization': 'Bearer testtoken',
        },
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Failed to load users: ${res.status} ${text}`);
      }
      const data = await res.json();
      setUsers(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const validateForm = () => {
    const errs = {};
    if (!name.trim()) errs.name = 'Name is required';
    if (!email.trim()) errs.email = 'Email is required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errs.email = 'Invalid email address';
    if (!role) errs.role = 'Role is required';
    return errs;
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setFormError(null);
    const errs = validateForm();
    if (Object.keys(errs).length > 0) {
      setFormError(Object.values(errs)[0]);
      return;
    }
    setSubmitting(true);
    try {
      const res = await fetch('/api/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer testtoken',
        },
        body: JSON.stringify({ name: name.trim(), email: email.trim(), role }),
      });
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`Create failed: ${res.status} ${errText}`);
      }
      // reset form on success
      setName('');
      setEmail('');
      setRole('member');
      // refresh list
      await fetchUsers();
    } catch (err) {
      setFormError(err?.message ?? 'Unknown error');
    } finally {
      setSubmitting(false);
    }
  };

  const userList = (
    <div style={styles.grid} aria-label="users list">
      {users.map((u) => (
        <div key={u.id ?? u.name + u.email} style={styles.card}>
          <div style={styles.avatar} aria-label="avatar">{(u.name?.[0] ?? 'U').toUpperCase()}</div>
          <div style={styles.userInfo}>
            <span style={styles.name}>{u.name ?? 'Unknown'}</span>
            <span style={styles.email}>{u.email ?? ''}</span>
            <span style={{ fontSize: 12, color: '#6b7280' }}>{u.role ?? 'user'}</span>
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <section style={styles.page} aria-labelledby="users-page-title">
      <div style={styles.header}>
        <h1 id="users-page-title" style={styles.title}>Users</h1>
        <div aria-live="polite" style={styles.hint}>
          {loading ? 'Loading users...' : ''}
        </div>
      </div>

      {error && (
        <div role="alert" style={{ ...styles.card, borderColor: '#f87171' }}>
          <span style={{ color: '#b91c1c', fontWeight: 600 }}>Error:</span>
          <span style={{ marginLeft: 6 }}>{error}</span>
        </div>
      )}

      {userList}

      <div style={styles.divider} />
      <section aria-labelledby="create-user-title" style={styles.formCard}>
        <h2 id="create-user-title" style={{ fontSize: 16, margin: 0, fontWeight: 700, marginBottom: 8 }}>Create user</h2>
        <form onSubmit={onSubmit} aria-label="Create user form">
          <div style={styles.formRow}>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <label style={styles.label} htmlFor="user-name">Name</label>
              <input
                id="user-name"
                style={styles.input}
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Jane Doe"
                required
              />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <label style={styles.label} htmlFor="user-email">Email</label>
              <input
                id="user-email"
                type="email"
                style={styles.input}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="jane@example.com"
                required
              />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <label style={styles.label} htmlFor="user-role">Role</label>
              <select
                id="user-role"
                style={{ ...styles.input, paddingRight: 8 }}
                value={role}
                onChange={(e) => setRole(e.target.value)}
              >
                <option value="admin">Admin</option>
                <option value="member">Member</option>
                <option value="guest">Guest</option>
              </select>
            </div>
          </div>
          {formError && (
            <div role="alert" style={styles.error} aria-live="polite">{formError}</div>
          )}
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <button type="submit" style={styles.button} disabled={submitting}>
              {submitting ? 'Creating...' : 'Create User'}
            </button>
            <button type="button" className="secondary" style={styles.buttonSecondary} onClick={() => {
              setName(''); setEmail(''); setRole('member'); setFormError(null);
            }}>
              Reset
            </button>
          </div>
        </form>
        <div style={styles.hint}>
          Client-side validation ensures name and email are valid before submitting. Backend will validate as well.
        </div>
      </section>
    </section>
  );
}
