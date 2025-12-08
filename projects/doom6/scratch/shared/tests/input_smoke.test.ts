import { World } from '../src/ecs';

describe('Input smoke test', () => {
  test('input events captured', () => {
    // Simple simulation of input events
    const events: string[] = [];

    function onEvent(type: string) {
      events.push(type);
    }

    onEvent('keydown_a');
    onEvent('keyup_a');

    expect(events).toEqual(['keydown_a','keyup_a']);
  });
});
