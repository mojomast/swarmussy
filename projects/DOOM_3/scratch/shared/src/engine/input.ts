export class InputController {
  private keys: Set<string> = new Set();

  constructor() {
    if (typeof window !== 'undefined') {
      window.addEventListener('keydown', (e) => {
        this.keys.add(e.key.toLowerCase());
      });
      window.addEventListener('keyup', (e) => {
        this.keys.delete(e.key.toLowerCase());
      });
    }
  }

  isDown(key: string): boolean {
    return this.keys.has(key.toLowerCase());
  }
}
