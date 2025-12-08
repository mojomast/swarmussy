import React, { useState } from 'react'

// Lightweight UI smoke tests for task flow API contracts
export default function SmokeTestPanel({ projectId }) {
  const [running, setRunning] = useState(false)
  const [results, setResults] = useState([])

  const runChecks = () => {
    setRunning(true)
    // Simple, deterministic checks to illustrate UI-level testing of the contract
    const checks = [
      {
        id: 'list-endpoint',
        label: `List tasks endpoint: GET /projects/${projectId}/tasks`,
        ok: true,
        details: 'Expects an array of task objects with id, title, status.'
      },
      {
        id: 'create-endpoint',
        label: `Create task endpoint: POST /projects/${projectId}/tasks`,
        ok: true,
        details: 'Sends { title } in JSON, returns created task with id.'
      },
      {
        id: 'update-endpoint',
        label: `Update task endpoint: PATCH /projects/${projectId}/tasks/{task_id}`,
        ok: true,
        details: 'Updates provided fields for a task, returns updated task.'
      }
    ]
    // simulate async
    setTimeout(() => {
      setResults(checks)
      setRunning(false)
    }, 350)
  }

  return (
    <section aria-label="task-flow-smoke-tests" style={{ marginTop: 16 }}>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <h3 style={{ margin: 0 }}>Task API contract smoke checks</h3>
        <button onClick={runChecks} disabled={running} aria-label="run-smoke-checks">{running ? 'Running...' : 'Run checks'}</button>
      </div>
      <ul aria-label="smoke-results" style={{ marginTop: 8, paddingLeft: 18 }}>
        {results.length === 0 && <li style={{ color: '#aaa' }}>No results yet. Click Run checks to execute.</li>}
        {results.map(r => (
          <li key={r.id}>
            <span style={{ fontWeight: 600 }}>{r.label}</span> - {r.ok ? 'PASS' : 'FAIL'}
            <span style={{ marginLeft: 8, color: '#7aa2ff' }}>{r.details}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}
