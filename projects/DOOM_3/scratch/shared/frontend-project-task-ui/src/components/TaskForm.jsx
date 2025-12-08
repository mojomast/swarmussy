import React, { useState } from 'react'
import { tasksEndpoint } from '../utils/api'

export default function TaskForm({ projectId, onCreated }) {
  const [title, setTitle] = useState('')
  const onSubmit = (e) => {
    e.preventDefault()
    fetch(`${tasksEndpoint(projectId)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title })
    }).then(r => r.json()).then((t) => {
      setTitle('')
      onCreated?.(t)
    })
  }
  return (
    <form onSubmit={onSubmit} style={{ display: 'flex', gap: 8, marginTop: 16 }}>
      <input value={title} onChange={e => setTitle(e.target.value)} placeholder="New task" />
      <button type="submit">Add</button>
    </form>
  )
}
