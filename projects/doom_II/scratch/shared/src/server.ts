import express from 'express';
import { createLevelsRouter } from './levels_api.js';

const app = express();
app.use(express.json({ limit: '10mb' }));
// Mount API routes under /api
app.use('/api', createLevelsRouter());

const PORT = process.env.PORT ? parseInt(process.env.PORT) : 3000;
app.listen(PORT, () => {
  console.log(`Levels API listening on port ${PORT}`);
});

export default app;
