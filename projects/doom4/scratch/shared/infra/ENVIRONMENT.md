CI/CD Environment Variables and Secrets for the Doom-like project

1) General CI/CD (GitHub Actions)
- GITHUB_TOKEN: Provided by GitHub Actions for performing actions like deploying to pages. Do not override.
- NPM_TOKEN: Optional if private npm registries are used; add to GitHub Secrets if needed for npm login in CI.

2) Static Hosting / Deploy targets
- GITHUB Pages (gh-pages) deployment
  - No additional secrets required beyond GITHUB_TOKEN; permissions granted by GitHub Actions runner.
- AWS S3/CloudFront
  - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AWS_S3_BUCKET
- Netlify
  - NETLIFY_AUTH_TOKEN, NETLIFY_SITE_ID

3) Hosting provider-specific
- For AWS: configure with AWS CLI in Actions or use dedicated actions (e.g., aws-actions/configure-aws-credentials)
- For Netlify: use netlify-action

4) NPM and registry access
- NODE_AUTH_TOKEN or NPM_TOKEN as needed for private registries.

5) Local development environment (optional)
- NODE_VERSION (e.g., 18.x or 20.x) if you pin versions locally
- PROJECT_HOST (optional base URL for local testing)
