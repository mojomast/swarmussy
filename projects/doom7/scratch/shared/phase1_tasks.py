# Phase 1 UI task mapping helpers
UI_STATE_ENABLED = 1
UI_STATE_DISABLED = 0
UI_STATE_HIDDEN = -1


def map_phase1_tasks_to_ui(tasks):
    # Simple heuristic: pending/in_progress become enabled; done hidden
    ui_tasks = []
    for t in tasks:
        status = t.get('status')
        if status in ('pending', 'in_progress'):
            ui_state = UI_STATE_ENABLED
        else:
            ui_state = UI_STATE_HIDDEN
        ui_tasks.append({"id": t.get("id"), "name": t.get("name"), "ui_state": ui_state})
    return ui_tasks
