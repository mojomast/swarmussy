import React from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import App from './pages/App'
import './styles.css'

const router = createBrowserRouter([
  { path: '/', element: <App /> },
  { path: '/editor', element: <App page=\"editor\" /> },
  { path: '/viewer', element: <App page=\"viewer\" /> },
])

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
)
