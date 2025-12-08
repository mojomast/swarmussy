import React from 'react';
import { getProfile, loadProfile } from './src/profile.js';

export default function Users() {
  const profile = loadProfile();
  return (
    <div>
      <h3>Users</h3>
      <pre>{JSON.stringify(profile, null, 2)}</pre>
    </div>
  );
}
