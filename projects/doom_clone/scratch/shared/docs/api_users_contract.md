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
- GET /api/users
  - Description: Retrieve list of users
  - Query Params: page (default 1), limit (default 20)
  - Headers: Authorization: Bearer <token>
  - Response (200): { users: User[] }
  - Response (4xx/5xx): ErrorResponse

- GET /api/users/{user_id}
  - Description: Retrieve a user by ID
  - Headers: Authorization: Bearer <token>
  - Response (200): User
  - Response (404): ErrorResponse

- POST /api/users
  - Description: Create a new user
  - Headers: Authorization: Bearer <token>
  - Request Body (application/json): { name: string, email: string }
  - Response (201): { user: User }
  - Response (4xx/5xx): ErrorResponse

Notes
- Default pagination is page=1, limit=20 to align with tests.
- Bearer token must be provided in Authorization header.
