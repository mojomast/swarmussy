# API Contract - User Profiles

This document defines the contract for the backend /users API endpoints used by the frontend profile features.

## Endpoints
- GET /users
  - Returns a list of user summaries
- POST /users
  - Creates a new user profile
  - Body: { name: string, avatar?: string, level?: number, health?: number, score?: number, inventory?: array }
- GET /users/{id}
  - Returns a user profile by id
- PUT /users/{id}
  - Updates a user profile
  - Body: partial UserProfile
- DELETE /users/{id}
  - Deletes a user profile

## Schemas
- UserProfile
  - id: string
  - name: string
  - avatar?: string
  - level?: number
  - health?: number
  - score?: number
  - inventory?: array
- Summary
  - id: string
  - name: string
  - avatar?: string

