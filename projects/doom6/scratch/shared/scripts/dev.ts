import { build } from 'esbuild';
import { createServer } from 'vite';

async function startDevServer() {
  const server = await createServer({ root: '.', server: { port: Number(process.env.VITE_DEV_PORT) || 5173, host: process.env.VITE_DEV_HOST || '0.0.0.0' } });
  await server.listen();
  console.log(`Dev server started at http://${server.config.server.host}:${server.config.server.port}`);
}

startDevServer().catch((e) => {
  console.error(e);
  process.exit(1);
});
