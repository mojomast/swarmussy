from flask import Flask, request, jsonify, abort
import threading
import time

app = Flask(__name__)

# In-memory storage for profiles: id -> data dict
profiles = {}
current_profile_id = None

@app.route('/reset', methods=['POST'])
def reset_state():
    global profiles, current_profile_id
    profiles.clear()
    current_profile_id = None
    return jsonify({'status': 'reset'}), 200

@app.route('/profiles', methods=['POST'])
def save_profile():
    global current_profile_id
    payload = request.get_json(silent=True)
    if not payload or 'id' not in payload or 'data' not in payload:
        return jsonify({'error': 'Missing id or data'}), 400
    pid = payload['id']
    pdata = payload['data']
    # Conflict if exists with different data
    if pid in profiles and profiles[pid] != pdata:
        return jsonify({'error': 'Conflict: profile with same id exists with different data'}), 409
    profiles[pid] = pdata
    # If no current profile set, set the first one as current
    if current_profile_id is None:
        current_profile_id = pid
    return jsonify({'id': pid, 'data': pdata}), 201, {'Location': f'/profiles/{pid}'}

@app.route('/profiles/<pid>', methods=['GET'])
def load_profile(pid):
    if pid not in profiles:
        return jsonify({'error': 'Profile not found'}), 404
    return jsonify({'id': pid, 'data': profiles[pid]}), 200

@app.route('/profiles/<pid>', methods=['DELETE'])
def delete_profile(pid):
    global current_profile_id
    if pid not in profiles:
        return jsonify({'error': 'Profile not found'}), 404
    del profiles[pid]
    # Adjust current if needed
    if current_profile_id == pid:
        current_profile_id = None if not profiles else next(iter(profiles))
        # If there is a remaining profile, set it as current
        if current_profile_id is not None:
            current_profile_id = current_profile_id
    return '', 204

@app.route('/profiles/current', methods=['GET'])
def get_current():
    if current_profile_id is None or current_profile_id not in profiles:
        return jsonify({'error': 'No current profile'}), 404
    return jsonify({'id': current_profile_id, 'data': profiles[current_profile_id]}), 200

@app.route('/profiles/bootstrap', methods=['POST'])
def bootstrap():
    global current_profile_id
    if profiles:
        return jsonify({'error': 'Profiles already exist'}), 409
    # Create a default profile
    default_id = 'default'
    profiles[default_id] = {'name': 'Default User'}
    current_profile_id = default_id
    return jsonify({'id': default_id, 'data': profiles[default_id]}), 201

def run_app():
    # Run the server in a thread
    app.run(port=5001, use_reloader=False)

if __name__ == '__main__':
    run_app()
