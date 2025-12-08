// Minimal unit tests for the ECS core scaffold
// NOTE: This file is a lightweight TS/JS test harness. It is not a replacement for a full test framework.

import { World, RenderSystem, demoCreateSampleWorld, demoTickAndRender, Position, Velocity, Sprite } from "../ecs_core";

function assert(condition: boolean, message: string) {
  if (!condition) throw new Error("Assertion failed: " + message);
}

function testWorldCreationAndRendering() {
  const world = new World();
  const e1 = world.createEntity();
  world.addPosition(e1, { x: 0, y: 0 });
  world.addVelocity(e1, { dx: 1, dy: 0 });
  world.addSprite(e1, { key: 'hero' });

  // After one tick of dt=1, position should update
  world.step(1.0);
  const renderItems = RenderSystem.render(world);
  // Expect at least one render item corresponding to e1
  const found = renderItems.find(r => r.entity === e1);
  assert(!!found, 'Render list should include the created entity.');
  assert(found!.x === 1 && found!.y === 0, 'Entity should have moved to (1,0) after dt=1.');
  assert(found!.spriteKey === 'hero', 'Sprite key should be preserved.');
}

function testDemoTickAndRender() {
  const w = demoCreateSampleWorld();
  const initial = RenderSystem.render(w);
  // Tick by 0.5
  const after = demoTickAndRender(w, 0.5);
  assert(after.length >= initial.length, 'Render list should have entities after tick.');
}

function runAll() {
  try {
    testWorldCreationAndRendering();
    testDemoTickAndRender();
    console.log('ecs_core_tests: PASS');
  } catch (e: any) {
    console.error('ecs_core_tests: FAIL', e?.message ?? e);
  }
}

// Execute tests if this file is run directly (node will ignore TS types at runtime if compiled to JS)
runAll();
