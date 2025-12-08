import { startServer } from './server'

async function main() {
  const s = await startServer()
  console.log('Server started')
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
