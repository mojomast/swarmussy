Bonus Mode: Leaderboard and incentivization for top performers.
- Endpoints:
  - GET /api/bonus/top?limit=N
  - POST /api/bonus/award (admin only) with payload { userId|username, amount, reason }
- Admin checks via header x-admin: true
- Points are persisted in a simple JSON-backed store under shared/bonus_mode/points.json
