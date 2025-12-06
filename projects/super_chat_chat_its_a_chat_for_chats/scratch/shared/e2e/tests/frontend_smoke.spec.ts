import { test, expect } from '@playwright/test';

test('Frontend smoke: routes load and Start wiring works', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveURL('/');
  // Navigate to game page
  await page.click('a[href="/game"]');
  await page.waitForSelector('#game-canvas', { state: 'visible' });

  // Start game
  await page.click('button#start-game');
  // Expect status to be displayed after starting
  await page.waitForSelector('#game-status', { state: 'visible' });
});
