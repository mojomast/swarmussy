export const saveEditorState = async (name: string, data: any) => {
  // Placeholder: pretend to persist to backend or localStorage
  try {
    const key = `editor_state:${name}`;
    localStorage.setItem(key, JSON.stringify(data));
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : String(e) };
  }
};

export const loadEditorState = async (name: string) => {
  try {
    const key = `editor_state:${name}`;
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    return null;
  }
};
