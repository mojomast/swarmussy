# Local profile bootstrapping notes

- The app bootstraps the profile on startup via the doomBootstrapping module.
- The app shell listens for the doom-bootstrap-profile event to hydrate engine state.
- Profile data is persisted in localStorage under key `doomClone.profile`.
