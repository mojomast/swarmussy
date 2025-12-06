# Master Plan — Web Game Project

## 1) Project Goal
Build a lightweight, web-based 2D game with a responsive UI and a simple, reliable backend to manage game state and scores.

## 2) Deliverables
- Playable web game (frontend) with a canvas-based renderer
- REST API backend for game data (games, players, scores)
- CI/CD pipeline and Dockerized deployment
- Basic documentation and test plan

## 3) Tech Stack (preferred)
- Frontend: React + HTML5 Canvas (Vite)
- Backend: Node.js + Express
- Database: SQLite (embedded) or simple JSON store for prototyping
- Deployment: Docker + GitHub Actions
- Tests: Jest + supertest (API) and Playwright (UI) as optional

## 4) Architecture Overview
- Frontend: UI components, game canvas, API glue, local state
- Backend: REST endpoints for games, players, scores; persistent storage
- DevOps: Dockerfiles, docker-compose for local dev, CI/CD scripts
- Docs: Developer docs, API spec, test plan

## 5) Milestones & Timeline (high-level)
- Milestone 1: Scaffolding (frontend + backend scaffolds, repo wiring) – Week 1
- Milestone 2: Core Game Mechanics API – Week 2
- Milestone 3: Frontend Game Canvas – Week 2-3
- Milestone 4: CI/CD & Deployment – Week 3
- Milestone 5: Polish, Tests, Documentation – Week 4

## 6) Non-functional Requirements
- Performance: Aim for <16ms frame updates on the canvas; API latency under 100ms locally
- Security: Basic input validation, rate limiting for API
- Accessibility: Keyboard controls, high-contrast UI in canvas overlays

## 7) Risks & Mitigations
- Risk: Scope creep – Mitigation: Stick to MVP scope and defer extras
- Risk: Backend schema changes – Mitigation: Start with minimal viable schema; versioned migrations

## 8) Acceptance Criteria
- Playable game on desktop/mobile
- Core API endpoints functional with basic persistence
- Dockerized project and at least one (auto)deploy workflow

