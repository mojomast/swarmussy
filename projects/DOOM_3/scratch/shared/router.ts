// Minimal Express-like Router with middleware support
export type Request = any;
export type Response = any;
export type NextFunction = (err?: any) => void;

export type RouteHandler = (req: Request, res: Response, next?: NextFunction) => void | Promise<void>;

// Simple colored logger middleware
export function colorfulLogger(req: Request, res: Response, next: NextFunction) {
  const t = new Date().toISOString();
  const method = req?.method || 'GET';
  const url = req?.url || '/';
  // Green color for logs
  console.log(`\x1b[32m[${t}] ${method} ${url}\x1b[0m`);
  next?.();
}

export class Router {
  private globalMiddlewares: RouteHandler[] = [];
  private routes: { [method: string]: { [path: string]: RouteHandler[] } } = {};

  use(mw: RouteHandler) {
    this.globalMiddlewares.push(mw);
  }

  get(path: string, ...handlers: RouteHandler[]) {
    this.register('GET', path, handlers);
  }

  post(path: string, ...handlers: RouteHandler[]) {
    this.register('POST', path, handlers);
  }

  private register(method: string, path: string, handlers: RouteHandler[]) {
    if (!this.routes[method]) this.routes[method] = {};
    if (!this.routes[method][path]) this.routes[method][path] = [];
    this.routes[method][path].push(...handlers);
  }

  // Very small URL matcher (exact path). For simplicity, query params are ignored in path matching.
  handle(req: Request, res: Response) {
    const method = (req?.method || 'GET').toUpperCase();
    const path = (req?.url || '/').split('?')[0];

    const stack: RouteHandler[] = [];
    if (this.globalMiddlewares.length) stack.push(...this.globalMiddlewares);
    const routeChain = this.routes?.[method]?.[path] ?? [];
    stack.push(...routeChain);

    let idx = 0;
    const next: NextFunction = (err?: any) => {
      if (err) {
        // Simple error handling
        try {
          res.statusCode = 500;
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify({ error: String(err) }));
        } catch (e) {
          // ignore
        }
        return;
      }
      if (idx >= stack.length) {
        if (!res.headersSent && !res.writableEnded) {
          res.end();
        }
        return;
      }
      const fn = stack[idx++];
      try {
        const ret = fn(req, res, next);
        if (ret && typeof (ret as any).then === 'function') {
          (ret as Promise<void>).then(() => next(), (e) => next(e));
        }
      } catch (e) {
        next(e);
      }
    };
    next();
  }
}

// Basic JSON body validator helper (used by endpoints if needed)
export function jsonBodyParser(req: Request, res: Response, next: NextFunction) {
  // Only parse JSON bodies for POST/PUT/PATCH with content-type json
  const method = req?.method?.toUpperCase?.() ?? '';
  const contentType = req?.headers?.['content-type'] || '';
  if (!['POST','PUT','PATCH'].includes(method) || !contentType.toLowerCase().includes('application/json')) {
    return next?.();
  }
  let body = '';
  req.on('data', (chunk: any) => {
    body += chunk;
  });
  req.on('end', () => {
    try {
      req.body = body ? JSON.parse(body) : {};
      next?.();
    } catch (e) {
      res.statusCode = 400;
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify({ error: 'Invalid JSON' }));
    }
  });
}

export { Router, colorfulLogger };
