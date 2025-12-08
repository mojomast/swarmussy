export type TaskStatus = 'pending' | 'in_progress' | 'done';

export type TaskRecord = {
  id: string;
  projectId: string;
  title: string;
  description?: string;
  status: TaskStatus;
  dueDate?: string;
  createdAt: string;
  updatedAt: string;
};

export interface TaskRepository {
  createTask(projectId: string, payload: { title: string; description?: string; status?: TaskStatus; dueDate?: string; }): Promise<TaskRecord>;
  getTask(projectId: string, id: string): Promise<TaskRecord | undefined>;
  listTasks(projectId: string): Promise<TaskRecord[]>;
  updateTask(projectId: string, id: string, payload: Partial<{ title: string; description: string; status: TaskStatus; dueDate: string }>): Promise<TaskRecord | undefined>;
  deleteTask(projectId: string, id: string): Promise<boolean>;
}

function nowIso(): string {
  return new Date().toISOString();
}

export class InMemoryTaskRepository implements TaskRepository {
  // projectId -> taskId -> TaskRecord
  private store: Record<string, Record<string, TaskRecord>> = {};

  private ensureProject(projectId: string) {
    if (!this.store[projectId]) {
      this.store[projectId] = {};
    }
  }

  async createTask(projectId: string, payload: { title: string; description?: string; status?: TaskStatus; dueDate?: string; }): Promise<TaskRecord> {
    this.ensureProject(projectId);
    const id = (typeof crypto?.randomUUID === 'function') ? crypto.randomUUID() : `t_${Date.now()}_${Math.random().toString(36).slice(2,9)}`;
    const now = nowIso();
    const task: TaskRecord = {
      id,
      projectId,
      title: payload.title,
      description: payload.description,
      status: payload.status ?? 'pending',
      dueDate: payload.dueDate,
      createdAt: now,
      updatedAt: now,
    };
    this.store[projectId][id] = task;
    return task;
  }

  async getTask(projectId: string, id: string): Promise<TaskRecord | undefined> {
    const proj = this.store[projectId];
    if (!proj) return undefined;
    return proj[id];
  }

  async listTasks(projectId: string): Promise<TaskRecord[]> {
    const proj = this.store[projectId] ?? {};
    return Object.values(proj);
  }

  async updateTask(projectId: string, id: string, payload: Partial<{ title: string; description: string; status: TaskStatus; dueDate: string }>): Promise<TaskRecord | undefined> {
    const proj = this.store[projectId];
    if (!proj) return undefined;
    const t = proj[id];
    if (!t) return undefined;
    if (payload.title !== undefined) t.title = payload.title;
    if (payload.description !== undefined) t.description = payload.description;
    if (payload.status !== undefined) t.status = payload.status;
    if (payload.dueDate !== undefined) t.dueDate = payload.dueDate;
    t.updatedAt = nowIso();
    return t;
  }

  async deleteTask(projectId: string, id: string): Promise<boolean> {
    const proj = this.store[projectId];
    if (!proj) return false;
    if (id in proj) {
      delete proj[id];
      return true;
    }
    return false;
  }
}

// Factory helper for tests or runtime
export function createDefaultTaskRepository(): TaskRepository {
  return new InMemoryTaskRepository();
}
