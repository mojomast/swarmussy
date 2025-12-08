import React from 'react'
import { createBrowserRouter } from 'react-router-dom'
import App from './pages/App'

export const ROUTE_PATHS = ['/', '/editor', '/viewer']

const router = createBrowserRouter([
  { path: '/', element: <App /> },
  { path: '/editor', element: <App page="editor" /> },
  { path: '/viewer', element: <App page="viewer" /> },
])

export default router
