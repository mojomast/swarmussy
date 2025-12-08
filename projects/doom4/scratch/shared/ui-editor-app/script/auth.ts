// Minimal auth module for UI (TypeScript version)
export class AuthService {
  static login(username: string, password: string): string {
    const token = 'demo-token';
    try { localStorage.setItem('authToken', token); } catch {}
    return token;
  }
  static isAuthed(): boolean {
    try { return !!localStorage.getItem('authToken'); } catch { return false; }
  }
}
