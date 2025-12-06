import React from 'react';

export default function AppShell({ children }) {
  return (
    <div className="app-shell">
      <header className="app-header">Game Sandbox</header>
      <main className="app-content">{children}</main>
    </div>
  );
}
