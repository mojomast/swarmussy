export type LevelData = {
  id: string
  name: string
  width: number
  height: number
  grid?: number[][]
}

export type InventoryItem = {
  id: string
  name: string
  icon?: string
}

// Frontend API wrappers that mirror in-memory backend endpoints

// Health check wrapper (exposed as fetchHealth for tests)
export async function healthCheck(): Promise<{ status: string; uptime?: number }> {
  try {
    const res = await fetch('/api/health')
    if (!res.ok) return { status: 'error' } as any
    return await res.json()
  } catch {
    return { status: 'error' } as any
  }
}

// Levels
export async function fetchLevels(): Promise<LevelData[]> {
  try {
    const res = await fetch('/api/levels')
    if (!res.ok) return []
    const data = await res.json()
    return Array.isArray(data) ? data : []
  } catch {
    return []
  }
}

export async function fetchInventory(): Promise<InventoryItem[]> {
  try {
    const res = await fetch('/api/inventory')
    if (!res.ok) return []
    const data = await res.json()
    return Array.isArray(data) ? data : []
  } catch {
    return []
  }
}

// Create or update a level via POST (create)
export async function saveLevel(level: LevelData): Promise<{ ok?: boolean; success?: boolean; id?: string }> {
  try {
    const res = await fetch('/api/levels', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(level),
    })
    if (!res.ok) return { ok: false } as any
    return await res.json()
  } catch {
    return { ok: false } as any
  }
}

// Health alias for tests
export const fetchHealth = healthCheck

// Load a level by id
export async function loadLevelById(levelId: string): Promise<{ ok: boolean; level?: LevelData }> {
  try {
    const res = await fetch('/api/levels/load', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ levelId }),
    })
    if (!res.ok) return { ok: false }
    return await res.json()
  } catch {
    return { ok: false }
  }
}

// Update a level by id
export async function updateLevel(level: LevelData): Promise<{ ok: boolean; updatedAt?: number; id?: string }> {
  try {
    const res = await fetch(`/api/levels/${level.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(level),
    })
    if (!res.ok) return { ok: false } as any
    return await res.json()
  } catch {
    return { ok: false } as any
  }
}

// Move player
export async function movePlayer(playerId: string, dx: number, dy: number): Promise<{ ok: boolean; pos?: { x: number; y: number } }> {
  try {
    const res = await fetch('/api/player/move', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ playerId, dx, dy }),
    })
    if (!res.ok) return { ok: false } as any
    return await res.json()
  } catch {
    return { ok: false } as any
  }
}

// Shoot player
export async function shootPlayer(playerId: string, direction: { x: number; y: number }): Promise<{ ok: boolean; event?: { playerId: string; direction: { x: number; y: number } } | { ts?: number } }> {
  try {
    const res = await fetch('/api/player/shoot', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ playerId, direction }),
    })
    if (!res.ok) return { ok: false } as any
    return await res.json()
  } catch {
    return { ok: false } as any
  }
}

export type LevelPayload = LevelData
export type InventoryPayload = InventoryItem

// Re-export API surface for convenience
export * from './types'
