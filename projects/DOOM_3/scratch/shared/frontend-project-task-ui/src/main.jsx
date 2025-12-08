import React from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import TaskList from './pages/TaskList.jsx'
import './index.css'

const router = createBrowserRouter([
  { path: '/', element: <TaskList projectId={1} /> },
])

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
)
