"use strict";
const express = require('express');
const { top, addPoints } = require('../bonus_mode/bonusStore');

const router = express.Router();

// Simple admin check: require header x-admin: true
function requireAdmin(req, res, next) {
  const admin = req.headers['x-admin'];
  if (admin === 'true' || admin === '1' || admin === 'yes') {
    return next();
  }
  return res.status(403).json({ error: 'forbidden' });
}

// Public: show top bonuses
router.get('/top', async (req, res) => {
  const limit = parseInt(req.query.limit, 10) || 10;
  try {
    const topList = await top(limit);
    res.json(topList);
  } catch (e) {
    res.status(500).json({ error: e?.message || 'internal_error' });
  }
});

// Admin: award points to a user
router.post('/award', requireAdmin, async (req, res) => {
  const { userId, username, amount, reason } = req.body;
  const amt = Number(amount);
  if (!userId && !username) return res.status(400).json({ error: 'userId or username required' });
  if (isNaN(amt) || amt <= 0) return res.status(400).json({ error: 'invalid amount' });
  try {
    const entry = addPoints(userId, username, amt, reason);
    res.json({ entry });
  } catch (e) {
    res.status(500).json({ error: e?.message || 'internal_error' });
  }
});

module.exports = router;
