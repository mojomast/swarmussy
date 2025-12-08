from typing import List, Dict, Any

# UI states exposed to the frontend Flow
UI_STATE_ENABLED = 'enabled'
UI_STATE_DISABLED = 'disabled'
UI_STATE_HIDDEN = 'hidden'


def map_phase1_tasks_to_ui(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Map Phase 1 backlog tasks to lightweight UI state descriptors.

    Each task dict may contain:
      - id: str
      - name: str
      - status: str (e.g., 'pending', 'in_progress', 'done', or other)

    Returns:
      List of dicts: { 'id', 'label', 'ui_state' }
    """
    result: List[Dict[str, Any]] = []
    for t in tasks or []:
        t_id = t.get('id')
        label = t.get('name') or f"Task {t_id}"
        status = (t.get('status') or '').lower()
        if status == 'done':
            ui_state = UI_STATE_HIDDEN
        elif status in ('pending', 'in_progress'):
            ui_state = UI_STATE_ENABLED
        else:
            ui_state = UI_STATE_DISABLED
        result.append({'id': t_id, 'label': label, 'ui_state': ui_state})
    return result


__all__ = ['map_phase1_tasks_to_ui', 'UI_STATE_ENABLED', 'UI_STATE_DISABLED', 'UI_STATE_HIDDEN']
