import { describe, it, expect } from 'vitest'
import { createDefaultProjectRepository, ProjectRepository } from '../repository/project_repository'
import { createDefaultTaskRepository, TaskRepository, TaskRecord } from '../repository/task_repository'

describe('Repository layer: projects', () => {
  const projectRepo: ProjectRepository = createDefaultProjectRepository()

  it('lists initial seed projects', async () => {
    const list = await projectRepo.listProjects()
    expect(Array.isArray(list)).toBe(true)
    expect(list.length).toBeGreaterThanOrEqual(2)
  })

  it('verifies tokens for existing projects', async () => {
    const ok = await projectRepo.verifyToken('alpha', 'alpha123')
    expect(ok).toBe(true)
    const bad = await projectRepo.verifyToken('alpha', 'not-a-token')
    expect(bad).toBe(false)
  })

  it('creates a new project and lists it', async () => {
    const rec = await projectRepo.createProject('Gamma Project', 'gamma-token')
    expect(rec.id).toBeTruthy()
    const list = await projectRepo.listProjects()
    const found = list.find(p => p.id === rec.id)
    expect(found).toBeTruthy()
  })
})

describe('Repository layer: tasks (in-memory)', () => {
  const taskRepo: TaskRepository = createDefaultTaskRepository()

  it('creates, reads, updates, and deletes a task per project', async () => {
    // create in project alpha
    const t = await taskRepo.createTask('alpha', { title: 'Alpha Task', description: 'desc' })
    expect(t).toBeTruthy()
    expect(t.projectId).toBe('alpha')
    const got = await taskRepo.getTask('alpha', t.id)
    expect(got?.id).toBe(t.id)

    // list
    const listAlpha = await taskRepo.listTasks('alpha')
    expect(listAlpha.find(x => x.id === t.id)).toBeTruthy()

    // update
    const updated = await taskRepo.updateTask('alpha', t.id, { title: 'Alpha Task Updated', status: 'in_progress' })
    expect(updated?.title).toBe('Alpha Task Updated')
    expect(updated?.status).toBe('in_progress')

    // per-project isolation: create in beta
    const tBeta = await taskRepo.createTask('beta', { title: 'Beta Task' })
    const otherProj = await taskRepo.getTask('alpha', tBeta.id)
    expect(otherProj).toBeUndefined()

    // delete
    const del = await taskRepo.deleteTask('alpha', t.id)
    expect(del).toBe(true)
    const afterDel = await taskRepo.getTask('alpha', t.id)
    expect(afterDel).toBeUndefined()
  })
})
