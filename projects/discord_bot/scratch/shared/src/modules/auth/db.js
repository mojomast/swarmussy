const path = require('path');
const fs = require('fs');
const sqlite3 = require('sqlite3').verbose();

// DB file lives under scratch/shared/data/auth.db
const DB_PATH = path.resolve(__dirname, '../../../data/auth.db');
let dbInstance = null;

async function initDb() {
  if (dbInstance) return;
  // Ensure directory exists
  const dir = path.dirname(DB_PATH);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  // Open database connection
  dbInstance = new sqlite3.Database(DB_PATH, (err) => {
    if (err) {
      throw err;
    }
  });
  // Create users table if not exists
  const createTableSQL = `
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `;
  return new Promise((resolve, reject) => {
    dbInstance.run(createTableSQL, (err) => {
      if (err) {
        reject(err);
      } else {
        resolve(true);
      }
    });
  });
}

function insert(sql, params = []) {
  return new Promise((resolve, reject) => {
    if (!dbInstance) return reject(new Error('DB not initialized'));
    dbInstance.run(sql, params, function (err) {
      if (err) return reject(err);
      // this.lastID is the id of the inserted row
      resolve(this.lastID);
    });
  });
}

function queryOne(sql, params = []) {
  return new Promise((resolve, reject) => {
    if (!dbInstance) return reject(new Error('DB not initialized'));
    dbInstance.get(sql, params, (err, row) => {
      if (err) return reject(err);
      resolve(row);
    });
  });
}

module.exports = { initDb, insert, queryOne };
