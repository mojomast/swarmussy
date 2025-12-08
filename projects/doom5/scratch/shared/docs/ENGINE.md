Engine Core: ECS Scaffold (TypeScript)

Overview
- Lightweight ECS scaffold with a World container and three component types: Position, Velocity, and Sprite.
- A simple RenderSystem converts world state into render-ready items for a renderer.
- Exports include a small demo harness and a tick/render helper for demos/tests.

Public API (exports)
- World: class that holds entities and their components.
- Position: interface { x: number; y: number }
- Velocity: interface { dx: number; dy: number }
- Sprite: interface { key: string; layer?: number }
- RenderItem: interface { entity: Entity; x: number; y: number; spriteKey: string }
- RenderSystem: class with static render(world: World): ReadonlyArray<RenderItem>
- demoCreateSampleWorld(): World
- demoTickAndRender(world: World, dt: number): ReadonlyArray<RenderItem>
- default export: World (for convenient new World import)

Usage
- Create a world, attach components, and step the world:

  import { World, Position, Velocity, Sprite, RenderSystem, demoCreateSampleWorld, demoTickAndRender } from './ecs_core';

  const world = new World();
  const e = world.createEntity();
  world.addPosition(e, { x: 0, y: 0 });
  world.addVelocity(e, { dx: 1, dy: 0 });
  world.addSprite(e, { key: 'hero' });

  // Advance one tick (dt may be seconds, choose units consistently)
  world.step(1.0);

  // Render data for a renderer
  const renderItems = RenderSystem.render(world);

Export points
- You can import by:
  - import { World, Position, Velocity, Sprite, RenderSystem, demoCreateSampleWorld, demoTickAndRender } from './ecs_core';
  - Or rely on default export: import World from './ecs_core';

Testing and Demos
- There is a tiny test harness and a demo helper exported for quick checks:
  - demoCreateSampleWorld(): World
  - demoTickAndRender(world, dt): RenderItem[]

Notes
- This ECS scaffold is intentionally minimal and focused on providing a solid foundation for the engine core and rendering workflow. It is suitable for demonstration, QA harnesses, and integration with a UI level editor.
