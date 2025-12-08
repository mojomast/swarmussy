import React from 'react';

// Lightweight skeleton placeholder for the Profile Panel in the app shell
const ProfilePanelPlaceholder = () => {
  return (
    <section aria-label="profile-panel-placeholder" style={styles.panel}>
      <h2 style={styles.title}>Doom Clone Profile (Skeleton)</h2>
      <div style={styles.row}>
        <div style={styles.avatar} aria-label="avatar placeholder" />
        <div style={styles.meta}>
          <div style={styles.line} />
          <div style={{ ...styles.line, width: '40%' }} />
        </div>
      </div>
      <div style={styles.grid}>
        <div style={styles.field}>
          <div style={styles.label}>Name</div>
          <div style={styles.skeleton} />
        </div>
        <div style={styles.field}>
          <div style={styles.label}>Avatar</div>
          <div style={styles.avatarGrid}>
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} style={styles.avatarCircle} />
            ))}
          </div>
        </div>
      </div>
      <div style={styles.actions}>
        <div style={styles.btn} />
        <div style={styles.btn} />
        <div style={styles.btn} />
      </div>
    </section>
  );
};

const styles = {
  panel: {
    border: '1px solid #ddd',
    padding: 16,
    borderRadius: 8,
    background: '#fff',
    maxWidth: 700,
  },
  title: { fontSize: 18, margin: 0, marginBottom: 12 },
  row: { display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 },
  avatar: { width: 40, height: 40, borderRadius: 9999, background: '#ddd' },
  meta: { flex: 1 },
  line: { height: 8, width: '60%', background: '#eee', borderRadius: 4, marginBottom: 6 },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 },
  field: { display: 'flex', flexDirection: 'column' },
  label: { fontSize: 12, color: '#666', marginBottom: 6 },
  skeleton: { height: 12, width: '100%', background: '#eee', borderRadius: 6 },
  avatarGrid: { display: 'flex', gap: 6, alignItems: 'center' },
  avatarCircle: { width: 26, height: 26, borderRadius: 999, background: '#ddd' },
  actions: { display: 'flex', gap: 8, marginTop: 12 },
  btn: { width: 60, height: 28, borderRadius: 6, background: '#eee' }
};

export default ProfilePanelPlaceholder;
