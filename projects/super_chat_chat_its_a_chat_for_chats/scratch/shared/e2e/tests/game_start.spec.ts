import { test, expect } from '@playwright/test';

test('Game start flow', async ({ page }) => {
  await page.goto('/game');
  // Assume Start button with id start-game
  await page.click('#start-game');
  // Status should update
  await page.waitForSelector('#game-status', { state: 'visible' });
  const status = await page.$eval('#game-status', el => el.textContent);
  expect(['starting','running']).toContain(status?.toLowerCase());
});
