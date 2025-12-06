const express = require('express');
const { getBalance, modifyBalance } = require('./walletService');
const { authenticate } = require('../middleware/auth');
const router = express.Router();

router.use(authenticate);

router.get('/balance', async (req, res) => {
  try {
    const bal = await getBalance(req.userId);
    res.json({ balance: bal });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

router.post('/deposit', async (req, res) => {
  const amount = Number(req.body.amount);
  if (!req.userId) return res.status(400).json({ error: 'user-id header required' });
  if (isNaN(amount) || amount <= 0) return res.status(400).json({ error: 'invalid amount' });
  try {
    const newBal = await modifyBalance(req.userId, amount);
    res.json({ balance: newBal });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

module.exports = router;
