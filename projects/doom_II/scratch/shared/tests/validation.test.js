import { validateJson } from '../src/validate.js';

const levelSchema = {
  type: 'object',
  required: ['id','name','dimensions','tiles','monsters','weapons','assets','spawn_points','version'],
  properties: {
    id: { type: 'string' },
    name: { type: 'string' },
    dimensions: {
      type: 'object', required: ['width','height','depth'], properties: {
        width: { type: 'number' }, height: { type: 'number' }, depth: { type: 'number' }
      }
    },
    tiles: { type: 'array', items: { type: 'string' } },
    monsters: { type: 'array', items: { type: 'string' } },
    weapons: { type: 'array', items: { type: 'string' } },
    assets: { type: 'array', items: { type: 'string' } },
    spawn_points: {
      type: 'array', items: {
        type: 'object', required: ['x','y','z'], properties: { x: { type: 'number' }, y: { type: 'number' }, z: { type: 'number' } }
      }
    },
    version: { type: 'string', pattern: '^\\d+\\.\\d+\\.\\d+$' }
  },
  additionalProperties: false
};

test('validate level schema - valid', () => {
  const lvl = { id: 'lvl1', name: 'Test', dimensions: { width: 10, height: 10, depth: 2 }, tiles: [], monsters: [], weapons: [], assets: [], spawn_points: [{ x:0,y:0,z:0 }], version: '1.0.0' };
  const res = validateJson(levelSchema, lvl);
  expect(res.valid).toBe(true);
});

test('validate level schema - missing required', () => {
  const lvl = { id: 'lvl1' };
  const res = validateJson(levelSchema, lvl);
  expect(res.valid).toBe(false);
  expect(res.errors.length).toBeGreaterThan(0);
});
