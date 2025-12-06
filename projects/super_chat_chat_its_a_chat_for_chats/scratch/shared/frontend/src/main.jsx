import React from 'react';
import { createRoot } from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import AppShell from './ui/AppShell.jsx';
import GameCanvas from './ui/GameCanvas.jsx';
import './styles.css';

const router = createBrowserRouter([
  { path: '/', element: <AppShell><GameCanvas /></AppShell> },
  { path: '/game', element: <AppShell><GameCanvas /></AppShell> },
]);

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
);
