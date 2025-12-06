import { test, expect } from '@playwright/test';

test('Game end flow', async ({ page }) => {
  await page.goto('/game');
  await page.click('#end-game');
  await page.waitForSelector('#game-status', { state: 'visible' });
  const status = await page.$eval('#game-status', el => el.textContent);
  expect(status?.toLowerCase()).toContain('completed');
});
