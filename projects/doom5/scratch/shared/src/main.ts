// Minimal dev server facade using vanilla TS/JS and WebGL canvas
window.addEventListener('DOMContentLoaded', () => {
  // Create a full-window canvas with a WebGL context
  const canvas = document.createElement('canvas')
  canvas.style.display = 'block'
  canvas.style.width = '100%'
  canvas.style.height = '70vh'
  canvas.width = Math.floor(window.innerWidth * window.devicePixelRatio)
  canvas.height = Math.floor(window.innerHeight * window.devicePixelRatio)
  document.body.appendChild(canvas)

  let gl: WebGLRenderingContext | null = null
  try {
    gl = canvas.getContext('webgl') as WebGLRenderingContext
  } catch (e) {
    gl = null
  }

  if (gl) {
    // Simple clear color animation
    let t = 0
    const render = () => {
      t += 0.01
      const r = (Math.sin(t) + 1) / 2
      const g = (Math.cos(t * 0.7) + 1) / 2
      const b = 0.5
      gl!.clearColor(r, g, b, 1.0)
      gl!.clear(gl!.COLOR_BUFFER_BIT)
      requestAnimationFrame(render)
    }
    render()
  } else {
    // Fallback message if WebGL is not available
    const msg = document.createElement('div')
    msg.textContent = 'WebGL not available. Canvas fallback active.'
    msg.style.padding = '1rem'
    document.body.appendChild(msg)
  }

  // Simple status text showing dev server facade
  const status = document.createElement('div')
  status.style.position = 'fixed'
  status.style.bottom = '1rem'
  status.style.left = '1rem'
  status.style.padding = '0.5rem 1rem'
  status.style.background = 'rgba(0,0,0,0.6)'
  status.style.color = '#fff'
  status.style.borderRadius = '4px'
  status.style.fontFamily = 'sans-serif'
  status.style.fontSize = '12px'
  status.textContent = 'Dev Server Facade: running (public assets served from /public)'
  document.body.appendChild(status)
})
