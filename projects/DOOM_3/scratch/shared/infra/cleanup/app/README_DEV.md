Repo-backed Cleanup API: how to use
- Set REPO_API_URL to enable repository-backed API loading inside the Cleanup app container.
- When REPO_API_URL is set, startup script clones the API repo and runs its UVicorn server; otherwise falls back to local main.py/app.py if present.
