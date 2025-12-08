export function healthStatus(): { status: string; uptime: number } {
  return { status: 'ok', uptime: 0 }
}
