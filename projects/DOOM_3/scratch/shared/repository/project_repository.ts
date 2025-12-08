export type ProjectRecord = {
  id: string;
  name: string;
  token: string;
};

export interface ProjectRepository {
  createProject(name: string, token?: string): Promise<ProjectRecord>;
  getProject(id: string): Promise<ProjectRecord | undefined>;
  listProjects(): Promise<ProjectRecord[]>;
  verifyToken(projectId: string, token?: string): Promise<boolean>;
}

function nowIso(): string {
  return new Date().toISOString();
}

export class InMemoryProjectRepository implements ProjectRepository {
  private store: Record<string, ProjectRecord> = {};

  constructor(seed?: ProjectRecord[]) {
    if (seed && Array.isArray(seed)) {
      for (const p of seed) {
        this.store[p.id] = p;
      }
    }
  }

  async createProject(name: string, token?: string): Promise<ProjectRecord> {
    const id = (typeof crypto?.randomUUID === 'function') ? crypto.randomUUID() : `p_${Date.now()}_${Math.random().toString(36).slice(2,9)}`;
    const t = token || Math.random().toString(36).slice(2, 10);
    const rec: ProjectRecord = { id, name, token: t };
    this.store[id] = rec;
    return rec;
  }

  async getProject(id: string): Promise<ProjectRecord | undefined> {
    return this.store[id];
  }

  async listProjects(): Promise<ProjectRecord[]> {
    return Object.values(this.store);
  }

  async verifyToken(projectId: string, token?: string): Promise<boolean> {
    const p = this.store[projectId];
    if (!p) return false;
    return !!token && token === p.token;
  }
}

export function createDefaultProjectRepository(): ProjectRepository {
  return new InMemoryProjectRepository([
    { id: 'alpha', name: 'Alpha Project', token: 'alpha123' },
    { id: 'beta', name: 'Beta Project', token: 'betatoken' },
  ]);
}
