const request = require('supertest');
const app = require('./server');

describe('POST /users', () => {
  it('should create a user', async () => {
    const appInstance = app();
    const res = await request(appInstance)
      .post('/users')
      .send({ name: 'Alice' });
    expect(res.status).toBe(201);
    expect(res.body).toHaveProperty('id');
  });
});
