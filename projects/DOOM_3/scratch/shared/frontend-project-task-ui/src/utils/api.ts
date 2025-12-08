// Helpers to build API endpoints for per-project task contracts
export const tasksEndpoint = (projectId: string | number): string => {
  return `/projects/${projectId}/tasks`
}

export const updateTaskEndpoint = (projectId: string | number, taskId: string | number): string => {
  return `/projects/${projectId}/tasks/${taskId}`
}
