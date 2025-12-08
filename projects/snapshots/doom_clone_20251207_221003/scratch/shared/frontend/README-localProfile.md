Doom Clone Local Profile UI - LocalStorage usage and bootstrap behavior

Overview
- The Profile UI stores profile data in localStorage under the key: doomClone.profile
- Data shape includes: name, avatar, level, health, score, inventory, lastSaved
- On app startup, the bootstrapping flow will automatically load the profile (if present) and emit a doom-bootstrap-profile event so the app shell can hydrate state.

Storage key and shape
- Key: doomClone.profile
- Example shape:
  {
    "name": "Doom Ranger",
    "avatar": "\uD83D\uDE80", // emoji avatar
    "level": 5,
    "health": 80,
    "score": 1200,
    "inventory": ["blaster", "shield"],
    "lastSaved": 1699999999999
  }

Bootstrap and app shell integration
- The doomBootstrapping.js module loads the profile via loadProfile() and dispatches a CustomEvent named doom-bootstrap-profile with the profile as event detail.
- If CustomEvent is unavailable, it falls back to window.__DOOM_BOOTSTRAP_PROFILE__ for simple access.
- The app shell should listen for doom-bootstrap-profile and hydrate its internal game/app state accordingly.

Using ProfilePanel in your UI
- ProfilePanel connects to the profile storage via loadProfile/saveProfile/deleteProfile.
- On startup, the host app can provide a callback onBootstrapped to receive the hydrated profile object when bootstrap occurs.
- Auto-load toggle persists to localStorage to control whether the profile should auto-load on startup.

Notes
- This implementation is intentionally lightweight for local development and offline scenarios.
- For production, replace localStorage usage with a backend API if needed.
