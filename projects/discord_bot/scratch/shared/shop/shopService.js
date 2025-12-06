const { initDb, get, run } = require('../db');

async function listItems() {
  const db = await initDb();
  const rows = await new Promise((resolve, reject) => {
    db.all('SELECT id, name, price, stock FROM items', [], (err, rows) => {
      if (err) reject(err); else resolve(rows);
    });
  });
  return rows;
}

async function buyItem(userId, itemId, quantity) {
  const db = await initDb();
  const item = await get(db, 'SELECT * FROM items WHERE id = ?', [itemId]);
  if (!item) throw new Error('item_not_found');
  const total = item.price * (quantity || 1);
  // debit user
  const wallet = await getBalance(db, userId);
  if (!wallet && wallet !== 0) {
    // If wallet retrieval failed, set 0
  }
  // We will reuse wallet balance from wallet table via separate call:
  const { getBalance } = require('../wallet/walletService');
  const bal = await getBalance(userId);
  if (bal < total) throw new Error('insufficient_funds');
  // deduct
  const { modifyBalance } = require('../wallet/walletService');
  const newBal = await modifyBalance(userId, -total);
  // update inventories - simple insertion
  await updateInventory(userId, itemId, quantity || 1);
  return { itemId, quantity, total, balance: newBal };
}

async function updateInventory(userId, itemId, quantity) {
  const db = await initDb();
  // upsert into inventories
  const existing = await get(db, 'SELECT quantity FROM inventories WHERE user_id = ? AND item_id = ?', [userId, itemId]);
  if (existing && existing.quantity) {
    await run(db, 'UPDATE inventories SET quantity = ? WHERE user_id = ? AND item_id = ?', [existing.quantity + quantity, userId, itemId]);
  } else {
    await run(db, 'INSERT INTO inventories (user_id, item_id, quantity) VALUES (?, ?, ?)', [userId, itemId, quantity]);
  }
}

module.exports = { listItems, buyItem };
