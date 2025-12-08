# API Documentation

## Overview
This backend provides a pluggable repository layer (in-memory first) with clean interfaces for data access.

## Authentication
- Per-project token-based authentication. Use the header `X-Project-Token` with your project token.
- Example: `X-Project-Token: alpha123`

## Endpoints
- POST /projects/{project_id}/tasks
  - Create a new task in a project
  - Body: JSON matching TaskCreate schema
- GET /projects/{project_id}/tasks
  - List tasks with optional status filter
- GET /projects/{project_id}/tasks/{task_id}
  - Retrieve a single task
- PATCH /projects/{project_id}/tasks/{task_id}
  - Update fields of a task
- DELETE /projects/{project_id}/tasks/{task_id}
  - Delete a task
