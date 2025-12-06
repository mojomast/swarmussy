"use strict";
const fs = require('fs');
const path = require('path');

const STORE_PATH = path.resolve(__dirname, 'points.json');

function ensureStoreExists() {
  if (!fs.existsSync(STORE_PATH)) {
    fs.writeFileSync(STORE_PATH, JSON.stringify({ entries: [] }, null, 2));
  }
}

function loadStore() {
  ensureStoreExists();
  const raw = fs.readFileSync(STORE_PATH, 'utf8');
  try {
    const obj = JSON.parse(raw);
    if (!Array.isArray(obj.entries)) {
      obj.entries = [];
    }
    return obj;
  } catch (e) {
    // Corrupt store, reset
    fs.writeFileSync(STORE_PATH, JSON.stringify({ entries: [] }, null, 2));
    return { entries: [] };
  }
}

function saveStore(store) {
  fs.writeFileSync(STORE_PATH, JSON.stringify(store, null, 2));
}

function resetStore() {
  fs.writeFileSync(STORE_PATH, JSON.stringify({ entries: [] }, null, 2));
  return { entries: [] };
}

function addPoints(userId, username, amount, reason) {
  const store = loadStore();
  const amt = Number(amount) || 0;
  let entry = store.entries.find(e => e.userId === userId);
  if (entry) {
    entry.points = (entry.points || 0) + amt;
    if (reason) entry.reason = reason;
  } else {
    entry = {
      userId,
      username: username || 'unknown',
      points: amt,
      reason,
      awardedAt: new Date().toISOString()
    };
    store.entries.push(entry);
  }
  saveStore(store);
  return entry;
}

function top(n) {
  const store = loadStore();
  const list = store.entries.slice().sort((a, b) => (b.points || 0) - (a.points || 0));
  return list.slice(0, n || 10);
}

module.exports = { addPoints, top, loadStore, saveStore, resetStore };
