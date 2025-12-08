import express from 'express';
import levelsRouter, { seedFromData } from './src/levels_api.js';
import { sampleLevels } from './src/data_seed.js';

// Seed initial data on startup
seedFromData(sampleLevels);

const app = express();
app.use(express.json());

// Mount the Levels API
app.use('/levels', levelsRouter);

// Health check
app.get('/health', (_req, res) => res.status(200).json({ status: 'ok' }));

const PORT = process.env.PORT ? parseInt(process.env.PORT) : 3000;
app.listen(PORT, () => {
  console.log(`Levels API listening on port ${PORT}`);
});

export default app;
