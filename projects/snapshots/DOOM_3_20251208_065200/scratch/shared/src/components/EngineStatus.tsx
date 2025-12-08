import React, { useEffect, useState, useRef } from 'react'
import type { Engine, EngineState } from '../../engine'
import type { WorldSnapshot } from '../../engine/core'
import { MockWorldProvider } from '../../engine/mock_provider'
import type { Engine as EngineInterface } from '../../engine'

// Lightweight EngineStatus widget that uses a mock engine to demonstrate start/tick wire-up
export const EngineStatus: React.FC = () => {
  // local mock world provider for integration with the mock engine
  const initialWorld: WorldSnapshot = {
    levels: {
      lvl1: {
        id: 'lvl1',
        name: 'Demo Level',
        width: 16,
        height: 12,
        tiles: Array.from({ length: 12 }, () => Array(16).fill('0')),
        players: {
          p1: { id: 'p1', x: 0, y: 0 }
        }
      }
    }
  }

  // Minimal in-component engine wrapper implementing Engine using the mock provider
  class MockEngine implements Engine {
    private running = false
    private tickCount = 0
    private state: EngineState = { running: false, tick: 0, fps: 60, lastTickMs: 16 }
    private provider?: MockWorldProvider

    constructor(provider: MockWorldProvider) {
      this.provider = provider
      // initial state
      this.state = { running: false, tick: 0, fps: 60, lastTickMs: 16 }
    }

    public async start(): Promise<EngineState> {
      this.running = true
      this.state.running = true
      this.state.tick = 0
      return this.state
    }

    public async tick(): Promise<EngineState> {
      if (!this.running) return this.state
      // advance a synthetic tick
      this.tickCount++
      this.state.tick = this.tickCount
      this.state.fps = 60
      this.state.lastTickMs = 16
      // Update could pull a world snapshot from provider if needed
      void this.provider?.getWorld()
      return this.state
    }

    public stop(): void {
      this.running = false
      this.state.running = false
    }

    public status(): EngineState {
      return this.state
    }
  }

  const engineRef = useRef<Engine | null>(null)
  const [state, setState] = useState<EngineState>({ running: false, tick: 0, fps: 0 })
  const [connected, setConnected] = useState(true)

  useEffect(() => {
    const provider = new MockWorldProvider(initialWorld)
    const eng = new MockEngine(provider)
    engineRef.current = eng

    eng.start().then((s) => {
      setState({ ...s })
    })

    // tick loop: every 400ms simulate a tick
    const timer = setInterval(async () => {
      if (!engineRef.current) return
      const s = await engineRef.current.tick()
      setState({ ...s })
    }, 400)

    return () => {
      clearInterval(timer)
      eng.stop()
    }
  }, [])

  const toggle = async () => {
    const eng = engineRef.current
    if (!eng) return
    if (state.running) {
      eng.stop()
      setState(eng.status())
    } else {
      const s = await eng.start()
      setState({ ...s })
    }
  }

  return (
    <section aria-label="Engine status" style={{ padding: 12, border: '1px solid #334', borderRadius: 8, width: 320, background: '#0b1020' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <strong style={{ color: '#fff' }}>Engine</strong>
        <span
          aria-live="polite"
          style={{ padding: '4px 8px', borderRadius: 6, color: '#fff', background: state.running ? '#16a34a' : '#ef4444' }}
        >{state.running ? 'Running' : 'Stopped'}</span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        <div style={{ color: '#e5e7eb' }}>Tick</div>
        <div style={{ color: '#e5e7eb', textAlign: 'right' }}>{state.tick}</div>
        <div style={{ color: '#e5e7eb' }}>FPS</div>
        <div style={{ color: '#e5e7eb', textAlign: 'right' }}>{state.fps}</div>
        <div style={{ color: '#e5e7eb' }}>Last Tick (ms)</div>
        <div style={{ color: '#e5e7eb', textAlign: 'right' }}>{state.lastTickMs ?? 0}</div>
      </div>
      <div style={{ marginTop: 8, textAlign: 'right' }}>
        <button onClick={toggle} aria-label="Toggle engine" style={{ padding: '6px 12px', borderRadius: 6, border: 'none', background: '#1e40af', color: '#fff' }}>
          {state.running ? 'Stop' : 'Start'}
        </button>
      </div>
    </section>
  )
}
