import React, { useEffect, useState } from 'react';

// Minimal Task UI to interact with per-project tasks at /projects/{project_id}/tasks
// Supports real API endpoints or a lightweight DEMO mode for local UI checks.

const DEMO_PROJECTS = [
  { id: 'p1', name: 'Repo A' },
  { id: 'p2', name: 'Repo B' }
];
const DEMO_TASKS = {
  p1: [
    { id: 't1', title: 'Cleanup readme', status: 'todo' },
    { id: 't2', title: 'Add license', status: 'in_progress' }
  ],
  p2: [
    { id: 't3', title: 'Configure CI', status: 'todo' }
  ]
};

function App() {
  const isDemoMode = typeof window !== 'undefined' && window.location.search.includes('demo');
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState('');
  const [tasks, setTasks] = useState([]);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [diagRunning, setDiagRunning] = useState(false);
  const [diagResults, setDiagResults] = useState([]);
  const [uiLogs, setUiLogs] = useState([]);
  // Load a list of projects from API (represents repository-backed projects)
  useEffect(() => {
    async function loadProjects() {
      if (isDemoMode) {
        setProjects(DEMO_PROJECTS);
        if (DEMO_PROJECTS.length > 0) {
          setSelectedProject(DEMO_PROJECTS[0].id);
        }
        return;
      }
      try {
        const res = await fetch('/projects');
        if (!res.ok) throw new Error('Failed to load projects');
        const data = await res.json();
        setProjects(data.projects || []);
        if (data.projects && data.projects.length > 0) {
          setSelectedProject(data.projects[0].id);
        }
      } catch (e) {
        setError(e.message);
      }
    }
    loadProjects();
  }, [isDemoMode]);

  // Load tasks for selected project
  useEffect(() => {
    if (!selectedProject) return;
    async function loadTasks() {
      setLoading(true);
      if (isDemoMode) {
        const ds = DEMO_TASKS[selectedProject] || [];
        setTasks(ds);
        setLoading(false);
        return;
      }
      try {
        const res = await fetch(`/projects/${selectedProject}/tasks`);
        if (!res.ok) throw new Error('Failed to load tasks');
        const data = await res.json();
        setTasks(data.tasks || []);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    }
    loadTasks();
  }, [selectedProject, isDemoMode]);

  async function createTask() {
    if (!newTaskTitle.trim()) return;
    setError(null);
    if (isDemoMode) {
      // mutate demo data
      const newTask = {
        id: 't' + Date.now(),
        title: newTaskTitle.trim(),
        status: 'todo'
      };
      if (!DEMO_TASKS[selectedProject]) DEMO_TASKS[selectedProject] = [];
      DEMO_TASKS[selectedProject] = [...DEMO_TASKS[selectedProject], newTask];
      setTasks((t) => [...t, newTask]);
      setNewTaskTitle('');
      setUiLogs((l) => [`Created task: ${newTask.title}`].concat(l));
      return;
    }
    try {
      const res = await fetch(`/projects/${selectedProject}/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTaskTitle.trim() })
      });
      if (!res.ok) throw new Error('Failed to create task');
      const data = await res.json();
      setTasks((t) => [...t, data.task].filter(Boolean));
      setNewTaskTitle('');
    } catch (e) {
      setError(e.message);
    }
  }

  async function updateTaskStatus(taskId, status) {
    if (isDemoMode) {
      // update in demo data
      const arr = DEMO_TASKS[selectedProject] || [];
      const next = arr.map((tt) => (tt.id === taskId ? { ...tt, status } : tt));
      DEMO_TASKS[selectedProject] = next;
      setTasks(next);
      return;
    }
    try {
      const res = await fetch(`/projects/${selectedProject}/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      });
      if (!res.ok) throw new Error('Failed to update task');
      // optimistic update
      setTasks((tasks) => tasks.map((t) => (t.id === taskId ? { ...t, status } : t)));
    } catch (e) {
      setError(e.message);
    }
  }

  async function runDiagnostics() {
    // Basic UI tests for API contracts
    setDiagRunning(true);
    setDiagResults([]);
    const results = [];
    function add(label, ok, detail) {
      results.push({ label, ok, detail: detail || '' });
    }
    try {
      // GET /projects
      try {
        const res = await fetch('/projects');
        if (!res.ok) {
          add('GET /projects', false, 'HTTP ' + res.status);
        } else {
          const data = await res.json();
          const count = Array.isArray(data.projects) ? data.projects.length : 0;
          add('GET /projects', true, `projects=${count}`);
          if (count > 0) {
            // Use first project id for next check
            const first = data.projects[0].id;
            if (first) {
              // GET /projects/{id}/tasks
              try {
                const res2 = await fetch(`/projects/${first}/tasks`);
                if (!res2.ok) {
                  add(`GET /projects/${first}/tasks`, false, 'HTTP ' + res2.status);
                } else {
                  const data2 = await res2.json();
                  const tcount = Array.isArray(data2.tasks) ? data2.tasks.length : 0;
                  add(`GET /projects/${first}/tasks`, true, `tasks=${tcount}`);
                }
              } catch (e) {
                add(`GET /projects/${first}/tasks`, false, e.message);
              }
            } else {
              add('GET /projects', true, 'no-project-id');
            }
          }
        }
      } catch (e) {
        add('GET /projects', false, e.message);
      }
    } finally {
      setDiagResults(results);
      setDiagRunning(false);
    }
  }

  // UI-friendly helper to know if we are in demo mode
  const demoLabel = isDemoMode ? ' DEMO MODE' : '';

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Repository-backed Tasks{demoLabel}</h1>
      {error && (
        <div style={{ color: 'red', marginBottom: 12 }}>{error}</div>
      )}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, alignItems: 'center', marginBottom: 16 }}>
        <label htmlFor="project-select">Project:</label>
        <select
          id="project-select"
          value={selectedProject}
          onChange={(e) => setSelectedProject(e.target.value)}
          aria-label="Select project"
        >
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        <button onClick={runDiagnostics} aria-label="Run API diagnostics" disabled={diagRunning}>
          {diagRunning ? 'Running...' : 'Run API checks'}
        </button>
      </div>
      <div style={{ border: '1px solid #ddd', padding: 12, borderRadius: 6, marginBottom: 16 }} aria-label="API diagnostics panel">
        <strong>API Diagnostics</strong>
        <div style={{ display: 'grid', gap: 8, marginTop: 8 }}>
          {diagResults.length === 0 ? (
            <div style={{ color: '#555' }}>No diagnostics run yet.</div>
          ) : (
            diagResults.map((r, idx) => (
              <div key={idx} style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>{r.label}</span>
                <span style={{ color: r.ok ? 'green' : 'red' }}>{r.ok ? 'OK' : 'FAIL'}</span>
                <span style={{ marginLeft: 12, color: '#666' }}>{r.detail}</span>
              </div>
            ))
          )}
        </div>
      </div>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 16 }}>
        <input
          type="text"
          value={newTaskTitle}
          onChange={(e) => setNewTaskTitle(e.target.value)}
          placeholder="New task title"
          aria-label="New task title"
          style={{ flex: 1, padding: 8, borderRadius: 4, border: '1px solid #ccc' }}
        />
        <button onClick={createTask} style={{ padding: '8px 12px' }}>
          Add Task
        </button>
      </div>
      {loading ? (
        <div>Loading tasks...</div>
      ) : (
        <ul role="list" aria-label="Task list" style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: 8 }}>
          {tasks.map((t) => (
            <li key={t.id} style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
              <span aria-label="status-dot" style={{ width: 16, height: 16, borderRadius: 4, background: '#888', display: 'inline-block' }} />
              <span style={{ flex: 1 }}>{t.title}</span>
              <select
                value={t.status}
                onChange={(e) => updateTaskStatus(t.id, e.target.value)}
                aria-label={`Status for ${t.title}`}
              >
                <option value="todo">todo</option>
                <option value="in_progress">in_progress</option>
                <option value="done">done</option>
              </select>
            </li>
          ))}
        </ul>
      )}
      <div style={{ marginTop: 24 }} aria-label="UI checks panel">
        <strong>UI Smoke Tests</strong>
        <ul style={{ listStyle: 'disc', paddingLeft: 20, marginTop: 8 }}>
          <li>Load projects (GET /projects) - {projects.length > 0 ? 'OK' : 'Not loaded'}</li>
          <li>List tasks for selected project - {tasks.length >= 0 ? 'OK' : 'Not loaded'}</li>
          <li>Create task (POST) - simulated in {isDemoMode ? 'demo' : 'real'} mode</li>
        </ul>
      </div>
    </div>
  );
}

export default App;
