import { marshalState, unmarshalState } from '../api_editor';

describe('JSON IO marshal/unmarshal', () => {
  it('round trip', () => {
    const s = JSON.stringify({ a: 1 });
    const o = JSON.parse(s);
    expect(o.a).toBe(1);
  });
});
