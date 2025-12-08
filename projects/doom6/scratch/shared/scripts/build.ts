import { build } from 'esbuild';
import path from 'path';
import { globby } from 'globby';

async function main() {
  const outDir = process.env.BUILD_OUT ?? 'dist';
  await build({ entryPoints: ['src/main.ts'], bundle: true, outdir: outDir, platform: 'browser', format: 'esm' }).catch((e) => {
    console.error(e);
    process.exit(1);
  });
  console.log(`Build output -> ${outDir}`);
}

main();
