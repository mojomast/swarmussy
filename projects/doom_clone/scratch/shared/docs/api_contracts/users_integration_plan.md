API Integration Plan: Users

Goal: Wire frontend to perform GET /users and POST /users with basic loading, error handling, and form validation in a production-ready UI scaffold.

Plan
- Data flow
  - Fetch users on component mount via GET /users. Expect { users: User[] }.
  - Display loading indicator while fetching. Show error on failure using Error response shape.
  - Provide form to create a new user with fields: name, email. Validate locally (non-empty, valid email format).
  - On submit, POST /users with { name, email }. Expect { user: User } on success. Append to list without re-fetching.
- API contracts alignment
  - Use shared/docs/api_contracts/users_api_contract.md as single source of truth.
- UI states
  - Loading spinner or text while fetching or posting.
  - Inline validation messages for fields (e.g., required, invalid email).
  - Error toast/row if server returns error, e.g., duplicates, invalid input (4xx/5xx).
- Error handling
  - Map non-2xx responses to Error object with message including status code.
- Accessibility
  - Use aria-live regions for errors, meaningful labels for inputs, and semantic headings.

Status: Draft for integration tests and CI validation.
