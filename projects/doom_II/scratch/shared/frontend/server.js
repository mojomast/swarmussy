import http from 'http';
import path from 'path';
import express from 'express';
import levelsRouter from './engine/api/levels.js';

const app = express();
app.use(express.json());
app.use('/levels', levelsRouter);

app.get('/', (_req, res) => res.send('Levels Admin API'));

const PORT = process.env.PORT ? parseInt(process.env.PORT) : 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
