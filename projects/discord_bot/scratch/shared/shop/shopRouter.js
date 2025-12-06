const express = require('express');
const { listItems, buyItem } = require('./shopService');
const { authenticate } = require('../middleware/auth');
const router = express.Router();

router.use(authenticate);

router.get('/items', async (req, res) => {
  try {
    const items = await listItems();
    res.json(items);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

router.post('/buy', async (req, res) => {
  const { itemId, quantity } = req.body;
  try {
    const result = await buyItem(req.userId, itemId, quantity || 1);
    res.json(result);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

module.exports = router;
