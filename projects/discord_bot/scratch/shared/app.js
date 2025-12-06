"use strict";

const express = require('express');
const bodyParser = require('body-parser');

function createApp() {
  const app = express();
  app.use(bodyParser.json());

  // Public auth routes
  const { register, login, refresh } = require('./auth/userController');
  const authRouter = express.Router();
  authRouter.post('/register', register);
  authRouter.post('/login', login);
  authRouter.post('/refresh', refresh);
  app.use('/api/auth', authRouter);

  // Protected routes
  const walletRouter = require('./wallet/walletRouter');
  const shopRouter = require('./shop/shopRouter');
  const gamesRouter = require('./games/gamesRouter');
  app.use('/api/wallet', walletRouter);
  app.use('/api/shop', shopRouter);
  app.use('/api/games', gamesRouter);

  // Bonus/leaderboard admin endpoints (bonus mode)
  try {
    // Optional: mount bonus endpoints if available
    const bonusRouter = require('./bonus_mode/bonusRouter');
    if (bonusRouter) {
      app.use('/api/bonus', bonusRouter);
    }
  } catch (e) {
    // ignore if bonus module not present
  }

  // Health check
  app.get('/health', (req, res) => res.json({ ok: true }));

  // 404 fallback
  app.use((req, res) => res.status(404).json({ error: 'not_found' }));

  return app;
}

module.exports = { createApp };
