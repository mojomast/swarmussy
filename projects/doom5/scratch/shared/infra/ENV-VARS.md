Environment variables and secrets for CI stub and dev runtime

CI workflow (GitHub Actions):
- NODE_VERSION: 20
- CI_FLAGS: not required for this stub; kept for future gating
- NPM_TOKEN: if private registry is used; not required for public npm.

Dev runtime container (Dockerfile in scratch/shared/infra):
- No runtime secrets exposed by default. All dependencies resolved via package.json in scratch/shared.
- If you extend the dev server to fetch assets, use a .env file and load via dotenv (not included in this stub).

Security notes:
- Do not hardcode secrets. Use GitHub Secrets for CI as needed.
- Ensure build context does not leak private keys.
