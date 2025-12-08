// Input handling for WASD, mouse look, and shooting

export interface InputState {
  up: boolean;
  down: boolean;
  left: boolean;
  right: boolean;
  mouseX: number;
  mouseY: number;
  shoot: boolean;
}

export class Input {
  state: InputState = {
    up: false, down: false, left: false, right: false,
    mouseX: 0, mouseY: 0, shoot: false,
  };

  constructor(private element: HTMLElement = document.body) {
    window.addEventListener('keydown', (e) => this.onKey(e, true));
    window.addEventListener('keyup', (e) => this.onKey(e, false));
    // Pointer lock for mouse look
    this.element.addEventListener('click', () => {
      if (document.pointerLockElement !== (this.element as any)) {
        (this.element as any).requestPointerLock();
      }
    });
    document.addEventListener('pointerlockchange', () => {
      // Reset deltas on lock change if needed
    });
    window.addEventListener('mousemove', (e) => this.onMouseMove(e));
  }

  private onKey(e: KeyboardEvent, down: boolean) {
    switch (e.code) {
      case 'KeyW': this.state.up = down; break;
      case 'KeyS': this.state.down = down; break;
      case 'KeyA': this.state.left = down; break;
      case 'KeyD': this.state.right = down; break;
    }
  }

  private onMouseMove(e: MouseEvent) {
    // Use movementX/y for pointer locked mode
    if (document.pointerLockElement) {
      this.state.mouseX = e.movementX;
      this.state.mouseY = e.movementY;
    }
  }

  // Simple shooting trigger by mouse button
  attachShootListener(handler: (dx: number, dy: number) => void) {
    window.addEventListener('mousedown', (e) => {
      if (e.button === 0) {
        this.state.shoot = true;
        handler(0, 0);
      }
    });
    window.addEventListener('mouseup', () => { this.state.shoot = false; });
  }
}
