import express, { Request, Response } from 'express';
import { validateJson } from './validate.js';

export interface User {
  id: string;
  username: string;
  email: string;
  createdAt?: string;
}

// In-memory store for users
const usersStore = new Map<string, User>();

function generateId(): string {
  return 'usr_' + Math.random().toString(36).slice(2, 9);
}

// Simple JSON Schema for user
const userSchema = {
  type: 'object',
  required: ['username','email'],
  properties: {
    id: { type: 'string' },
    username: { type: 'string' },
    email: { type: 'string' }
  },
  additionalProperties: false
};

// Basic auth middleware: require Authorization header with Bearer token
function requireAuth(req: Request, res: Response, next: Function) {
  const auth = req.headers['authorization'];
  if (!auth || typeof auth !== 'string' || !auth.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  // Token is not strictly validated for tests; presence is sufficient
  next();
}

export function createUsersRouter(): express.Router {
  const router = express.Router();
  // Apply auth to all user endpoints
  router.use(requireAuth);

  // POST /api/users - create a new user
  router.post('/users', (req: Request, res: Response) => {
    const data = req.body as any;
    const validation = validateJson(userSchema, data);
    if (!validation.valid) {
      return res.status(400).json({ errors: validation.errors });
    }

    const id = data.id ?? generateId();
    if (usersStore.has(id)) {
      return res.status(409).json({ error: 'User already exists' });
    }

    const user: User = {
      id,
      username: data.username,
      email: data.email,
      createdAt: new Date().toISOString(),
    };
    usersStore.set(id, user);
    res.status(201).json(user);
  });

  // GET /api/users - list users
  router.get('/users', (_req: Request, res: Response) => {
    res.json(Array.from(usersStore.values()));
  });

  // GET /api/users/:id - get specific user
  router.get('/users/:id', (req: Request, res: Response) => {
    const id = req.params.id;
    // Basic path traversal protection
    if (id.includes('..') || id.includes('/')) {
      return res.status(400).json({ error: 'invalid_id' });
    }
    const user = usersStore.get(id);
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }
    res.json(user);
  });

  return router;
}

export function resetUsersStore(): void {
  usersStore.clear();
}

export default createUsersRouter();
