Docker Compose flow for local dev testing of Cleanup API.

This repo uses docker-compose to orchestrate a Postgres database and a Python FastAPI app.

Files:
- docker-compose.yml: top-level compose for cleanup
- app/docker-compose.yml: per-service compose for the API and DB
- .env.example: example env vars for local dev

Usage:
- docker-compose up
