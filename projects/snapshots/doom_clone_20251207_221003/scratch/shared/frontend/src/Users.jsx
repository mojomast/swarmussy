import React, { useEffect, useState, useCallback } from 'react';

/**
 * Users management panel
 * - Left: list of users (GET /users)
 * - Right: form to create a new user (POST /users)
 *
 * Features:
 * - Client-side validation for name, email, and role
 * - Loading states for fetching and submitting
 * - Inline error messages and accessible live region for status
 * - Responsive two-column layout with inlined styles for portability
 */

function initials(name) {
  if (!name) return '';
  const parts = name.trim().split(/\s+/);
  const first = parts[0] ? parts[0][0] : '';
  const second = parts[1] ? parts[1][0] : '';
  return (first + second).toUpperCase();
}

const Users = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [fetchError, setFetchError] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const [form, setForm] = useState({ name: '', email: '', role: '' });
  const [formErrors, setFormErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [formMessage, setFormMessage] = useState(null);
  const [formMessageType, setFormMessageType] = useState(''); // 'success' | 'error'

  // Fetch users
  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setFetchError(null);
    try {
      const res = await fetch('/users');
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.message || res.statusText);
      }
      const data = await res.json();
      // Normalize to array (some backends may return object with { users: [...] })
      if (Array.isArray(data)) {
        setUsers(data);
      } else if (Array.isArray(data?.users)) {
        setUsers(data.users);
      } else {
        setUsers([]);
      }
    } catch (err) {
      setFetchError(err.message || 'Failed to load users');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers, // eslint-disable-line]
      0]);

  // Validation
  const validate = () => {
    const errors = {};
    if (!form.name?.trim()) errors.name = 'Name is required';
    if (!form.email?.trim()) {
      errors.email = 'Email is required';
    } else {
      const email = form.email.trim();
      // Basic email format check
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        errors.email = 'Invalid email address';
      }
    }
    if (!form.role?.trim()) errors.role = 'Role is required';
    return errors;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
    // Clear the field error on change
    setFormErrors((errs) => ({ ...errs, [name]: undefined }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    setFormErrors(errs);
    if (Object.keys(errs).length > 0) return;

    setSubmitting(true);
    setFormMessage(null);
    try {
      const res = await fetch('/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.message || res.statusText);
      }
      const created = await res.json();
      // Prepend to list for instant feedback
      setUsers((u) => (Array.isArray(u) ? [created, ...u] : [created]));
      // Reset form
      setForm({ name: '', email: '', role: '' });
      setFormMessage('User created successfully');
      setFormMessageType('success');
    } catch (err) {
      setFormMessage(err.message || 'Failed to create user');
      setFormMessageType('error');
    } finally {
      setSubmitting(false);
    }
  };

  // Accessibility: live region for messages
  const liveRegionId = 'users-live-region';

  // Simple responsive styles included here for portability
  return (
    <div className="pf-users-panel" aria-label="Users management panel" style={{ padding: '16px' }}>
      <style>
        {`
        .pf-users-container {
          display: grid;
          grid-template-columns: 1fr 420px;
          gap: 24px;
          align-items: start;
        }
        @media (max-width: 900px) {
          .pf-users-container { grid-template-columns: 1fr; }
        }
        .card {
          background: #0b1020;
          border: 1px solid #1e2a6a;
          border-radius: 12px;
          padding: 16px;
          color: #e9eaf6;
          box-shadow: 0 8px 20px rgba(0,0,0,.15);
        }
        .header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 8px 0 12px 0;
        }
        .title {
          font-size: 1.25rem;
          font-weight: 700;
        }
        .loading { opacity: 0.9; }
        .users-list { list-style: none; padding: 0; margin: 0; }
        .user-item { display: flex; align-items: center; padding: 10px 6px; border-bottom: 1px solid rgba(255,255,255,.08); }
        .avatar { width: 40px; height: 40px; border-radius: 999px; display: inline-flex; align-items: center; justify-content: center; background: #2a326b; color: white; font-weight: 700; margin-right: 12px; flex: 0 0 auto; }
        .user-info { display: flex; flex-direction: column; }
        .user-name { font-weight: 600; margin-bottom: 2px; }
        .user-meta { font-size: 12px; color: #cbd5e1; }
        .form-row { display: grid; grid-template-columns: 1fr; gap: 8px; margin-bottom: 12px; }
        label { font-size: 13px; color: #cbd5e1; }
        input, select {
          width: 100%; padding: 10px 12px; border-radius: 8px; border: 1px solid #3b4b8a; background: #0f1730; color: #e6eafc;
        }
        input:focus, select:focus { outline: 2px solid #8ab4f8; outline-offset: 2px; }
        .error { color: #ffd0d0; font-size: 12px; margin-top: 4px; }
        .button-row { display: flex; gap: 8px; align-items: center; }
        button { padding: 10px 14px; border-radius: 8px; border: none; cursor: pointer; font-weight: 600; }
        .btn { background: #4f6feb; color: white; }
        .btn.secondary { background: #2a315a; color: #e9eaff; }
        .btn[disabled] { opacity: 0.6; cursor: not-allowed; }
        .live { margin-top: 8px; font-size: 13px; padding: 6px 8px; border-radius: 8px; }
        .live.success { background: rgba(0,128,0,.25); color: #b6ffbd; }
        .live.error { background: rgba(128,0,0,.25); color: #ffb3b3; }
        `}
      </style>
      <div className="pf-users-container">
        <section className="card" aria-label="Users list">
          <div className="header">
            <div className="title">Users</div>
            <div className="button-row" aria-label="Actions">
              <button className="btn secondary" type="button" onClick={() => setRefreshKey((k) => k + 1)} title="Refresh list">Refresh</button>
            </div>
          </div>
          {loading && <div className="loading" aria-live="polite">Loading users...</div>}
          {fetchError && (
            <div role="status" aria-live="polite" style={{ color: '#ffcccc', marginTop: 6 }}>
              {fetchError}
            </div>
          )}
          <ul className="users-list" aria-label="Users">
            {users.map((u) => {
              const name = u.name || '';
              const email = u.email || '';
              const role = u.role || '';
              return (
                <li key={u.id ?? name} className="user-item">
                  <span className="avatar" aria-label="User avatar">{initials(name) || 'U'}</span>
                  <div className="user-info">
                    <span className="user-name">{name}</span>
                    <span className="user-meta">{email}{role ? ` \u2022 ${role}` : ''}</span>
                  </div>
                </li>
              );
            })}
          </ul>
        </section>
        <section className="card" aria-label="Create new user form">
          <div className="header">
            <div className="title">Create User</div>
          </div>
          <form onSubmit={handleSubmit} noValidate>
            <div className="form-row">
              <label htmlFor="name">Name</label>
              <input
                id="name"
                name="name"
                type="text"
                value={form.name}
                onChange={handleChange}
                aria-invalid={!!formErrors.name}
                aria-describedby={formErrors.name ? 'name-error' : undefined}
              />
              {formErrors.name && <span id="name-error" className="error" role="alert">{formErrors.name}</span>}
            </div>
            <div className="form-row">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                name="email"
                type="email"
                value={form.email}
                onChange={handleChange}
                aria-invalid={!!formErrors.email}
                aria-describedby={formErrors.email ? 'email-error' : undefined}
              />
              {formErrors.email && <span id="email-error" className="error" role="alert">{formErrors.email}</span>}
            </div>
            <div className="form-row">
              <label htmlFor="role">Role</label>
              <select
                id="role"
                name="role"
                value={form.role}
                onChange={handleChange}
                aria-invalid={!!formErrors.role}
                aria-describedby={formErrors.role ? 'role-error' : undefined}
              >
                <option value="">Select a role</option>
                <option value="admin">Admin</option>
                <option value="manager">Manager</option>
                <option value="user">User</option>
              </select>
              {formErrors.role && <span id="role-error" className="error" role="alert">{formErrors.role}</span>}
            </div>
            <div className="button-row" aria-label="Form actions">
              <button className="btn" type="submit" disabled={submitting} aria-disabled={submitting}>
                {submitting ? 'Creating...' : 'Create User'}
              </button>
              <button className="btn secondary" type="button" onClick={() => setForm({ name: '', email: '', role: '' })} disabled={submitting}>
                Clear
              </button>
            </div>
            {formMessage && (
              <div id={liveRegionId} className={`live ${formMessageType}`} role="status" aria-live="polite">
                {formMessage}
              </div>
            )}
          </form>
        </section>
      </div>
    </div>
  );
};

export default Users;
