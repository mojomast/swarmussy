Cleanup local dev & CI/CD environment variables

Local (docker-compose)
- DB_HOST: db
- DB_PORT: 5432
- POSTGRES_USER: cleanup
- POSTGRES_PASSWORD: cleanup
- POSTGRES_DB: cleanup
- APP_HOST: 0.0.0.0
- APP_PORT: 8000

Notes:
- Do not commit real credentials; use a .env file or secret manager for CI.
- The Postgres service in docker-compose exposes 5432 and creates the cleanup DB with the provided user/password.

CI/CD Secrets (example mapping; set these in your CI secret store):
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- GITHUB_TOKEN (provided by GitHub Actions automatically)
- DB_PASSWORD (if used by external DB in CI)

Kubernetes secrets (production):
- cleanup-db-password
- cleanup-db-user
- cleanup-db-host
- cleanup-db-port

These should be managed securely via your cloud secret manager or CI secret store.
