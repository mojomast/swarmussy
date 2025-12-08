Dev CI basic scaffold for a Vite app with npm ci

Files:
- package.json: npm scripts including dev, build, and ci-build
- vite.config.ts: minimal Vite dev server config
- Dockerfile: dockerized dev server with npm ci optimization

Usage:
- npm install
- npm run dev
- npm run build
- npm run ci-build
- docker build -t dev-ci-basic .
