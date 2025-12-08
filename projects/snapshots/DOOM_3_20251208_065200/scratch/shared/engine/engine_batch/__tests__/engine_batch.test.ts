import { describe, it, expect } from 'vitest';
import { EngineBatch } from '../../engine_batch';

describe('EngineBatch tests', () => {
  it('start/stop', async () => {
    const eng = new EngineBatch();
    const st = eng.start ? await eng.start() : await (eng as any).start();
    expect(st.running).toBe(true);
    eng.stop ? eng.stop() : (eng as any).stop();
    const st2 = eng.status ? eng.status() : (eng as any).status();
    expect(st2.running).toBe(false);
  });

  it('tick', async () => {
    const eng = new EngineBatch();
    const st = await (eng as any).start();
    await (eng as any).tick();
    const st2 = (eng as any).status();
    expect(typeof st2.tick).toBe('number');
  });
});
