API Contract: Users

Data Models
- User
  - id: string
- name: string
- email: string
- createdAt: string (ISO 8601 timestamp)

Error Formats
- ErrorResponse
  - error: {
    - code: string
    - message: string
    - details?: any
  }

Endpoints
- GET /users
  - Description: Retrieve list of users
  - Response (200): { users: User[] }
  - Response (4xx/5xx): ErrorResponse

- POST /users
  - Description: Create a new user
  - Request Body (application/json): { name: string, email: string }
  - Response (201): { user: User }
  - Response (4xx/5xx): ErrorResponse

Notes
- All endpoints are designed as a minimal, contract-driven surface for the frontend.
- The frontend should handle loading and error states using the defined error formats.
