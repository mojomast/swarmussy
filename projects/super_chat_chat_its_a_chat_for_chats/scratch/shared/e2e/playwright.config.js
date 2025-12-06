module.exports = {
  testDir: './e2e/tests',
  timeout: 60000,
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    headless: true
  },
};
