# Code & System Coherence Review

Scope: `scratch/shared` (backend, frontend, infra, tests, and planning docs).
Date: 2025-12-06

---

## High-level Impression

- **Overall**: The planning docs, infra, and scaffolds are surprisingly rich for an MVP. However, there are **multiple contract mismatches** between docs, backend, frontend, and tests. The project reads like several good, but partially independent, experiments that haven’t been fully reconciled.
- **Architectural intent** (React + Vite frontend, Express + SQLite backend, Docker + CI, Jest + Playwright) is clear and consistently described in docs, but the **actual wiring between layers is incomplete/inconsistent**.

---

## Planning & Documentation vs Implementation

### Strengths
- **Master plan / devplan / infra_status / e2e_plan** are coherent with each other:
  - Clear target stack: React + Canvas, Express + SQLite, Docker, CI, Jest/Playwright.
  - Milestones and timelines line up across `master_plan.md` and `timeline.md`.
  - `infra_status.md` accurately lists most real files and describes the desired MVP (Docker Compose, backend API skeleton, frontend SPA, CI).
  - `e2e_plan.md` is detailed and realistic, clearly articulating game lifecycle endpoints and E2E flows.
- Docs make it easy to understand **where the project is headed**.

### Incoherences / Gaps
- **Game API described but not implemented**:
  - Docs and E2E plan reference `/api/game/start`, `/api/game/status`, `/api/game/end`, but there is **no corresponding implementation** in the backend.
- **User API contract divergence**:
  - `e2e_plan.md` and Playwright tests (`api_health.spec.ts`, `users_api.spec.ts`) assume **`/api/users`** returning a bare array.
  - Actual running backend (`backend/server.js`) exposes **`/users`** and returns `{ users: [...] }`.
  - A more complete user API lives in `src/users.js` (modular router, validation, better errors) but is **not wired into the real backend server** and uses `/users`, not `/api/users`.
- **Docs vs current UI**:
  - Docs/e2e talk about a Start/Status/End game flow and wiring the frontend to backend, but `GameCanvas.jsx` is still a **pure visual placeholder** with no API calls or lifecycle behaviour.

Net: The written plans are coherent with each other, but **they describe a system that’s a couple of steps ahead of what’s actually wired up**.

---

## Backend: Express + SQLite

### What’s working/coherent
- **`src/users.js`** is a well-structured, modular users API skeleton:
  - Separate `initDb`, `createUsersRouter`, `validateUser`, `seedDemoUsers`.
  - Clear schema and inline explanation of exported functions.
  - Proper validation of `name` and `email`, with reasonable error handling and status codes.
  - Jest + Supertest tests in `test/users.test.js` are aligned with this module (they mount the router on `/` and expect JSON arrays and 201/400/409 statuses).
- **`backend/server.js`**:
  - Initializes SQLite DB and creates a `users` table if needed.
  - Seeds demo data.
  - Exposes `/health`, `/users`, `/users/:id`, and `POST /users`.
  - Uses morgan and JSON body parsing.

### Coherence Issues
- **Two separate user APIs with different contracts**:
  - `backend/server.js` defines `GET /users` that returns `{ users: rows }`.
  - `src/users.js`’s router defines `GET /users` returning a **bare array**.
  - E2E tests (`api_health.spec.ts`, `users_api.spec.ts`) expect `/api/users` and a bare array.
  - Result: **three different implied contracts** for “user list”: `/users` object, `/users` array, `/api/users` array.
- **`src/users.js` not used by `backend/server.js`**:
  - Given that `users.test.js` and docs clearly centre on `src/users.js`, the “real” Express app in `backend/server.js` should almost certainly mount that router (e.g., under `/api`). Right now they are **two parallel worlds**.
- **Status of Jest tests and dependencies is unclear**:
  - `test/users.test.js` uses Jest APIs, but there is **no obvious Jest dependency or npm script** in `scratch/shared` itself. CI only runs backend’s `npm test`, which does not run these Jest tests.
  - This makes it easy to accidentally break the “nice” user API module without noticing.

### `backend/test/run_tests.js`
- Runs `node -e "require('./server.js')"` as a smoke test, relying on working dir semantics.
- This doesn’t assert any API behaviour, so it’s **coherent with “smoke only” intent**, but **not coherent with the richer test story in docs and `users.test.js`**.

---

## Frontend: React + Vite

### What’s working/coherent
- Minimal but clear scaffold:
  - `main.jsx` sets up `createBrowserRouter` with `/` and `/game`, both wrapping `GameCanvas` in `AppShell`.
  - `AppShell.jsx` provides a simple layout shell.
  - `GameCanvas.jsx` implements a canvas ref and a simple animation loop; state is tracked with `status` via `useState` (though not yet wired into UI or backend).
- The **overall structure** (AppShell + GameCanvas + routing) matches the high-level plan.

### Coherence Issues vs tests and docs
- **Missing DOM structure that tests rely on**:
  - Playwright tests expect:
    - A link `a[href="/game"]` on the home page.
    - A canvas with `id="game-canvas"`.
    - Buttons `#start-game` and `#end-game`.
    - A `#game-status` element that becomes visible/updates.
  - Actual `GameCanvas.jsx` and `AppShell.jsx`:
    - No anchor for `/game`.
    - `<canvas>` has no `id`.
    - Only a single `<button>` with no id, and it only updates local `status` state (which is **not rendered** in the DOM; the status div is hardcoded `Status: idle`).
    - No end-game button.
  - Result: **all game-related E2E frontend tests will fail immediately** against this UI.
- **No real backend wiring yet, despite docs claiming it**:
  - `infra_status.md` and `frontend/README.md` both talk about the app being wired to the backend via `VITE_BACKEND_URL`.
  - Current React code never reads `import.meta.env.VITE_BACKEND_URL` and makes **no network calls**.
  - There is no abstraction for an `apiClient` or game/user service.
- **Router vs E2E expectations**:
  - `main.jsx` defines `/` and `/game`, but:
    - The home route already renders the game; E2E tests expect `/` to be a landing page with a link to `/game`.
    - There’s no navigation or layout difference between `/` and `/game` beyond URL.

### Package/dependency coherence
- `frontend/package.json` lists only `react` and `react-dom`, but `main.jsx` uses `react-router-dom`:
  - **Missing direct dependency** on `react-router-dom` is a coherence and reliability problem.
- `tsconfig.json` exists, but sources are plain JS/JSX; that’s OK but slightly confusing without TypeScript usage or explanation.

---

## E2E Tests vs Reality

### What tests assume
- **API**:
  - `api_health.spec.ts` and `users_api.spec.ts` assume `GET /api/users` exists and returns an **array**.
- **Frontend**:
  - `frontend_smoke.spec.ts`, `game_start.spec.ts`, and `game_end.spec.ts` assume:
    - Base URL serves HTML (likely frontend) at `/`.
    - A link to `/game` exists.
    - DOM IDs as described above (`#game-canvas`, `#start-game`, `#end-game`, `#game-status`).
    - Status text transitions to `starting` / `running` / `completed`.

### What actually exists
- Backend has `/users` (no `/api` prefix) and returns `{ users: [...] }`.
- Frontend is not mounted behind the backend; Docker Compose runs them on **different ports**.
- Frontend UI lacks all the IDs and dynamic status behaviour.

### Config-level mismatch
- `playwright.config.js` uses:
  - `baseURL: process.env.BASE_URL || 'http://localhost:3000'`.
- In `docker-compose.yml`:
  - Backend listens on **3000**.
  - Frontend (Vite/Nginx) is mapped to **5173**.
- The E2E suite wants to hit **both frontend and API**, but with `baseURL` defaulting to `http://localhost:3000` it will:
  - Send frontend navigation (`page.goto('/')`) to the backend, which doesn’t serve HTML.
  - Send API calls to the backend at `/api/users` which doesn’t exist.

Net: The E2E tests are **well-specified for the intended future system**, but **not aligned with the current deployment topology or API surface**.

---

## Infra: Docker, Docker Compose, CI

### Docker & Compose
- **Backend Dockerfile** is simple and coherent for a Node API container.
- **Frontend Dockerfile** builds with Vite and then serves via Nginx:
  - This is reasonable for production, but there is a port mismatch:
    - Nginx defaults to port **80**, but the Dockerfile exposes **5173** and `docker-compose.yml` maps `5173:5173`.
    - Unless the Nginx config is changed, traffic on 5173 will not reach the Nginx listener on 80.
- **VITE_BACKEND_URL semantics**:
  - `docker-compose.yml` passes `VITE_BACKEND_URL=http://backend:3000` to the **runtime container**.
  - Vite needs `VITE_*` env vars at **build time** to bake them into the bundle.
  - In the current multi-stage Dockerfile, env from runtime stage will not affect the `npm run build` stage unless wired via build args. So the env plumbing described in `infra_status.md` is **not yet faithfully implemented**.

### CI (`.github/workflows/ci.yml`)
- Backend CI is mostly coherent:
  - Checks out code, sets up Node 18, runs `npm install` and `npm test` in `scratch/shared/backend`.
- Frontend CI is **stubbed and structurally odd**:
  - There’s a `- name: Setup frontend` step that mixes `uses: actions/setup-node@v4` and `run:` in a way that isn’t standard for GitHub Actions.
  - No actual `npm install` or `npm test` is run for the frontend.
  - This contradicts the aspiration in `infra_status.md` and `e2e_plan.md` to include frontend/E2E checks in CI.
- No CI wiring for **root-level Jest tests** in `scratch/shared/test` or for **Playwright E2E tests**.

---

## Overall Coherence Assessment

- **Conceptual coherence**: High.
  - The story told by `master_plan.md`, `devplan.md`, `infra_status.md`, and `e2e_plan.md` is consistent and paints a clear target architecture.
- **Implementation coherence (today)**: Medium-low.
  - Individual pieces (modular user API, backend server, frontend skeleton, E2E tests, Docker config, CI) are each reasonable in isolation.
  - But **contracts between layers are not aligned** (paths, payload shapes, ports, DOM structure, env variables).
- **Primary sources of incoherence**:
  - **API paths and payload shapes**: `/users` vs `/api/users`, object vs array, missing game endpoints.
  - **UI → tests mismatch**: DOM IDs, navigation, and actual behaviour vs what Playwright scripts assert.
  - **Infra → tests mismatch**: ports and baseURL, VITE env wiring.
  - **Docs → implementation drift**: docs describing a slightly more advanced stage than the code actually reflects.

---

## Suggested Next Steps (at a high level)

_Not implementation instructions, just coherence-oriented suggestions._

1. **Pick a single source of truth for the Users API**
   - Decide whether the canonical implementation is `src/users.js` or `backend/server.js`.
   - Mount that router in the backend under a stable prefix (likely `/api`).
   - Align E2E tests, docs, and payload shape (`array` vs `{ users: [...] }`).

2. **Implement or downscope the Game API and UI**
   - Either:
     - Implement `/api/game/start|status|end` and wire `GameCanvas` to actually call them, plus DOM IDs expected by tests, **or**
     - Downgrade the E2E plan/tests/docs to match the simpler “visual sandbox only” state.

3. **Align E2E baseURL and services**
   - Decide whether E2E tests hit the frontend (`5173`) or a unified gateway (`3000`).
   - Update `playwright.config.js` and/or docker-compose to make that true.

4. **Bring CI in line with the test strategy**
   - Ensure Jest tests in `scratch/shared/test` and Playwright E2E tests are runnable and (optionally) wired into CI.
   - Fix the frontend CI step so it actually installs deps and runs at least a smoke test.

5. **Tighten frontend–backend env story**
   - Decide how `VITE_BACKEND_URL` is provided in dev vs Docker vs CI, and ensure the Dockerfile/compose setup matches that story.

If you want, I can next propose concrete code/infra diffs to reconcile one of these incoherences (e.g., standardizing the Users API and aligning E2E tests) without touching the rest yet.
