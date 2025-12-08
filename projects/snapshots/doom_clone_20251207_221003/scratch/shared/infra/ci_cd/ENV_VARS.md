CI/CD environment variables and secrets

- DOCKERHUB_USERNAME and DOCKERHUB_PASSWORD: For optional publishing of built Docker images (if added to pipeline).
- AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION: If you enable packaging into S3 or deploying to AWS.
- GITHUB_TOKEN: Auto-injected by GitHub Actions for API access; required for certain actions (if you rely on API calls).
- RUSTFLAGS: Optional flags for cross-compilation or linting; not required by default.
- TARGET: Cross-compilation target (e.g., x86_64-unknown-linux-gnu); supplied by matrix in CI.

Notes:
- Never hardcode credentials. Use GitHub Secrets / CI secret stores. The pipeline should inject them as environment variables during run.
