"use strict";

const jwt = require('jsonwebtoken');
const { authenticate } = require('../middleware/auth');

describe('Auth middleware - JWT handling', () => {
  const ORIGINAL_SECRET = process.env.JWT_SECRET;
  beforeAll(() => {
    process.env.JWT_SECRET = 'testsecret';
  });
  afterAll(() => {
    process.env.JWT_SECRET = ORIGINAL_SECRET;
  });

  test('valid JWT passes', () => {
    const token = jwt.sign({ id: 'u1', username: 'tester' }, 'testsecret', { expiresIn: '1h' });
    const req = { headers: { authorization: `Bearer ${token}` } };
    const res = { status: jest.fn().mockReturnThis(), json: jest.fn() };
    const next = jest.fn();

    authenticate(req, res, next);
    expect(next).toHaveBeenCalled();
  });

  test('invalid JWT returns 401', () => {
    const req = { headers: { authorization: `Bearer invalid` } };
    const res = { status: jest.fn().mockReturnThis(), json: jest.fn() };
    const next = jest.fn();

    authenticate(req, res, next);
    expect(res.status).toHaveBeenCalledWith(401);
  });

  test('fallback x-user-id header works', () => {
    const req = { headers: { authorization: '', 'x-user-id': 'abc123' } };
    const res = { status: jest.fn().mockReturnThis(), json: jest.fn() };
    const next = jest.fn();

    authenticate(req, res, next);
    expect(next).toHaveBeenCalled();
  });
});
  
  test('missing token returns 401', () => {
    const req = { headers: {} };
    const res = { status: jest.fn().mockReturnThis(), json: jest.fn() };
    const next = jest.fn();

    authenticate(req, res, next);
    expect(res.status).toHaveBeenCalledWith(401);
  });
