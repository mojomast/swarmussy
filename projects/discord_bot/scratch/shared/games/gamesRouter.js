const express = require('express');
const { startBlackjackSession, joinGame, getSessionState } = require('./gameService');
const { authenticate } = require('../middleware/auth');
const router = express.Router();

router.use(authenticate);

router.post('/blackjack/start', async (req, res) => {
  try {
    const sessionId = await startBlackjackSession(req.user.id);
    res.json({ sessionId });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

router.post('/blackjack/join', async (req, res) => {
  try {
    const { sessionId } = req.body;
    await joinGame(req.user.id, sessionId);
    res.json({ joined: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

router.get('/blackjack/state/:sessionId', async (req, res) => {
  try {
    const state = await getSessionState(req.params.sessionId);
    res.json(state);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

module.exports = router;
