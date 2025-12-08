import express, { Application, Request, Response, NextFunction, Router as ExpressRouter } from 'express'

// A minimal, production-friendly Express-like router wrapper with basic middleware support.
export class SimpleRouter {
  private router: ExpressRouter

  constructor() {
    this.router = express.Router()
  }

  // Global middleware akin to app.use(mw)
  use(mw: (req: Request, res: Response, next: NextFunction) => void) {
    this.router.use(mw)
    return this
  }

  get(path: string, handler: (req: Request, res: Response, next: NextFunction) => void) {
    this.router.get(path, handler)
    return this
  }

  post(path: string, handler: (req: Request, res: Response, next: NextFunction) => void) {
    this.router.post(path, handler)
    return this
  }

  put(path: string, handler: (req: Request, res: Response, next: NextFunction) => void) {
    this.router.put(path, handler)
    return this
  }

  // Mount the internal Express router onto the provided app
  mount(app: Application, basePath?: string) {
    app.use(basePath ?? '/', this.router)
  }

  // Expose the internal router for advanced usage if needed (read-only)
  get internalRouter(): ExpressRouter {
    return this.router
  }
}

export default SimpleRouter
