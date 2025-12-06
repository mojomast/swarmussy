const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const morgan = require('morgan');

const app = express();
app.use(express.json());
app.use(morgan('dev'));

const DB_PATH = process.env.DB_PATH || path.join(__dirname, 'db.sqlite');
const PORT = process.env.PORT || 3000;

// Ensure DB initialization
const db = new sqlite3.Database(DB_PATH, (err) => {
  if (err) {
    console.error('DB open error:', err.message);
  } else {
    console.log('DB connected at', DB_PATH);
    db.run(`CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      email TEXT UNIQUE NOT NULL
    )`);
+  }
+});
+
+// Seed some data if empty
+db.get('SELECT COUNT(*) as c FROM users', (err, row) => {
+  if (!err && row && row.c === 0) {
+    const stmt = db.prepare('INSERT INTO users (name, email) VALUES (?, ?)');
+    stmt.run('Alice', 'alice@example.com');
+    stmt.run('Bob', 'bob@example.com');
+    stmt.finalize();
+  }
+});
+
+app.get('/health', (req, res) => res.json({ status: 'ok' }));
+
+app.get('/users', (req, res) => {
+  db.all('SELECT id, name, email FROM users', [], (err, rows) => {
+    if (err) return res.status(500).json({ error: err.message });
+    res.json({ users: rows });
+  });
+});
+
+app.get('/users/:id', (req, res) => {
+  const id = req.params.id;
+  db.get('SELECT id, name, email FROM users WHERE id = ?', [id], (err, row) => {
+    if (err) return res.status(500).json({ error: err.message });
+    if (!row) return res.status(404).json({ error: 'User not found' });
+    res.json(row);
+  });
+});
+
+app.post('/users', (req, res) => {
+  const { name, email } = req.body;
+  if (!name || !email) {
+    return res.status(400).json({ error: 'name and email required' });
+  }
+  const stmt = db.prepare('INSERT INTO users (name, email) VALUES (?, ?)');
+  stmt.run(name, email, function(err) {
+    if (err) {
+      return res.status(500).json({ error: err.message });
+    }
+    res.status(201).json({ id: this.lastID, name, email });
+  });
+  stmt.finalize();
+});
+
+const start = () => {
+  app.listen(PORT, () => {
+    console.log(`Backend running on port ${PORT}`);
+  });
+};
+
+start();
