// Simple keyboard input system

export type InputState = {
  left: boolean;
  right: boolean;
  up: boolean;
  down: boolean;
};

export class KeyboardInput {
  private state: InputState = { left: false, right: false, up: false, down: false };
  constructor() {
    window.addEventListener('keydown', (e) => this.onKey(e, true));
    window.addEventListener('keyup', (e) => this.onKey(e, false));
  }
  private onKey(e: KeyboardEvent, down: boolean) {
    switch (e.code) {
      case 'ArrowLeft': case 'KeyA': this.state.left = down; break;
      case 'ArrowRight': case 'KeyD': this.state.right = down; break;
      case 'ArrowUp': case 'KeyW': this.state.up = down; break;
      case 'ArrowDown': case 'KeyS': this.state.down = down; break;
      default: break;
    }
  }
  getState(): InputState {
    return this.state;
  }
}
