import React, { useEffect, useState } from 'react'
import TaskForm from '../components/TaskForm'
import SmokeTestPanel from '../components/SmokeTestPanel'
import { tasksEndpoint, updateTaskEndpoint } from '../utils/api'

function TaskList({ projectId }) {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    fetch(`${tasksEndpoint(projectId)}`)
      .then(res => res.json())
      .then(
        (data) => { setTasks(data); setLoading(false); },
        (err) => { setError(err); setLoading(false); }
      )
  }, [projectId])

  const handleCreated = (t) => {
    setTasks(prev => [t, ...prev])
  }

  const handleToggle = (task) => {
    const newStatus = task.status === 'completed' ? 'pending' : 'completed'
    fetch(`${updateTaskEndpoint(projectId, task.id)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    })
      .then(r => r.json())
      .then(updated => {
        setTasks(prev => prev.map(t => t.id === task.id ? updated : t))
      }).catch(() => {
        // best effort: ignore errors in UI for simplicity
      })
  }

  return (
    <div className="app">
      <div className="card">
        <h1>Project {projectId} Tasks</h1>
        <TaskForm projectId={projectId} onCreated={handleCreated} />
        <SmokeTestPanel projectId={projectId} />
        {loading && <div>Loading...</div>}
        {error && <div role="alert">Error loading tasks</div>}
        <ul>
          {tasks.map(t => (
            <li key={t.id} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ minWidth: 200 }}>{t.title}</span>
              <span style={{ color: '#7aa2ff' }}>{t.status}</span>
              <button onClick={() => handleToggle(t)} aria-label={`toggle-${t.id}`}>
                Toggle
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

export default TaskList
