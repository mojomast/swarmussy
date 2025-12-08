Build/Play scaffolding for Dev tooling and builds

Overview
- Local dev tooling scaffold using Vite + TS, with npm scripts dev, build, test
- Minimal Dockerfile for local development and reproducible tool runs
- Simple README outlining how to build, run, and test locally or with Docker

What’s included
1) package.json scripts
- dev: vite
- build: vite build
- test: echo 'No tests configured' && exit 0

2) Minimal Vite configuration
- scratch/shared/vite.config.ts (basic dev server and build options)

3) Dockerfile for local dev tooling
- scratch/shared/Dockerfile (node:20-alpine, npm install, run dev)

4) Basic HTML/TS app scaffold
- scratch/shared/index.html
- scratch/shared/src/main.ts (entry wiring, simple canvas demo)
- scratch/shared/src/canvasEngine.ts (canvas helper)

5) README scaffolding
- scratch/shared/BUILD_PLAY.md contains how to run/build/play

Usage / How to run
- Local development (hosted by Vite)
  - npm install
  - npm run dev
  - Open http://localhost:5173

- Production build
  - npm run build
  - Serve dist with your favorite static server (e.g., npx serve dist)

- Docker (local dev tooling container)
  - docker build -t dev-tools-sandbox -f scratch/shared/Dockerfile .
  - docker run -p 5173:5173 dev-tools-sandbox

Environment variables
- This tooling scaffold requires no secrets for local dev.
- If you need to pass env-specific overrides, use a .env file and read via process.env in your TS/JS code. Do not commit secrets to repo.

Notes
- This is a minimal scaffolding intended for rapid iteration. Replace placeholders with real app code as needed.
