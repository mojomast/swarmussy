// A tiny Express-like router abstraction with middleware support for tests/tools
export type RequestLike = {
  method: string
  url: string
  body?: any
  headers?: Record<string, string>
}

export type ResponseLike = {
  statusCode?: number
  body?: any
  json: (value: any) => void
  send: (value: any) => void
}

type Handler = (req: RequestLike, res: ResponseLike, next: () => void) => void
type Middleware = (req: RequestLike, res: ResponseLike, next: () => void) => void

export class SimpleRouter {
  private routes: { method: string; path: string; handler: Handler }[] = []
  private middlewares: Middleware[] = []

  use(mw: Middleware) {
    this.middlewares.push(mw)
  }

  add(method: string, path: string, handler: Handler) {
    this.routes.push({ method: method.toUpperCase(), path, handler })
  }

  handle(req: RequestLike, res: ResponseLike) {
    const route = this.routes.find((r) => r.method === req.method.toUpperCase() && r.path === req.url)
    const stack: (() => void)[] = []
    this.middlewares.forEach((m) => stack.push(() => m(req, res, () => {})))
    // Run composed function: for simplicity execute middlewares then route
    let idx = 0
    const next = () => {
      if (idx < stack.length) {
        const fn = stack[idx++]
        fn()
      } else {
        route?.handler(req, res, () => {})
      }
    }
    next()
  }
}

export function createRouter(): SimpleRouter {
  const r = new SimpleRouter()
  return r
}

export default SimpleRouter
