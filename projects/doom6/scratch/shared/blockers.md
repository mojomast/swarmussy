# Active Blockers

Blockers reported by agents that need resolution.

## ⚠️ Blocker: Bugsy McTester (2025-12-08T14:14:37)
- **Type**: dependency
- **Task**: Expand QA plan to cover the MVP runtime: add tests for MovementSystem, ShootingSystem, and basic ren
- **Description**: Vitest not installed / npm test cannot run in current environment. Dependency not available prevents executing the new MVP ECS test suite. Recommend running 'npm install' in scratch/shared to install vitest and peers, or adjust CI to install dependencies before 'npm test'.

