from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

app = FastAPI()

# In-memory store to simulate backend resources
store = {}

class Resource(BaseModel):
    name: str

# New in-memory store for users and a simple token-based auth
users = {
    'u1': {'id': 'u1', 'name': 'Alice', 'email': 'alice@example.com'},
    'u2': {'id': 'u2', 'name': 'Bob', 'email': 'bob@example.com'}
}

class User(BaseModel):
    id: str
    name: str
    email: str | None = None

# Simple token for auth
security = HTTPBearer(auto_error=False)

def get_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Expect Bearer token; otherwise unauthorized
    if credentials is None or credentials.scheme.lower() != 'bearer' or credentials.credentials != 'secrettoken':
        raise HTTPException(status_code=401, detail='Unauthorized')
    return credentials.credentials

@app.post("/resources/{resource_id}", status_code=201)
def create_resource(resource_id: str, resource: Resource):
    if resource_id in store:
        raise HTTPException(status_code=409, detail="Resource already exists")
    if resource.name is None or str(resource.name).strip() == "":
        raise HTTPException(status_code=400, detail="Invalid payload: 'name' is required")
    store[resource_id] = {"id": resource_id, "name": resource.name}
    return store[resource_id]

@app.get("/resources/{resource_id}")
def read_resource(resource_id: str):
    if resource_id not in store:
        raise HTTPException(status_code=404, detail="Resource not found")
    return store[resource_id]

@app.delete("/resources/{resource_id}", status_code=204)
def delete_resource(resource_id: str):
default(store):
    if resource_id not in store:
        raise HTTPException(status_code=404, detail="Resource not found")
    del store[resource_id]
    return

@app.get("/health")
def health():
    return {"status": "ok"}

# Users API under /api with token-auth required
class PaginatedUsers(BaseModel):
    page: int = 1
    limit: int = 20
    items: list

@app.get("/api/users")
def list_users(page: int = 1, limit: int = 20, token: str = Depends(get_token)):
    # Pagination defaults: page=1, limit=20
    if page < 1 or limit < 1:
        raise HTTPException(status_code=400, detail='Invalid pagination parameters')
    all_users = list(users.values())
    start = (page - 1) * limit
    end = start + limit
    return {
        "page": page,
        "limit": limit,
        "total": len(all_users),
        "items": all_users[start:end]
    }

@app.get("/api/users/{user_id}")
def get_user(user_id: str, token: str = Depends(get_token)):
    if user_id not in users:
        raise HTTPException(status_code=404, detail='User not found')
    return users[user_id]

@app.post("/api/users", status_code=201)
def create_user(user: User, token: str = Depends(get_token)):
    if user.id in users:
        raise HTTPException(status_code=409, detail='User already exists')
    if not user.name:
        raise HTTPException(status_code=400, detail="Invalid payload: 'name' is required")
    users[user.id] = {"id": user.id, "name": user.name, "email": user.email}
    return users[user.id]

@app.post("/api/token-auth")
def token_auth(req: dict):
    # Accept raw dict to keep tests simple; in real code, use a Pydantic model
    token = None
    if isinstance(req, dict):
        token = req.get('token')
    else:
        token = None
    if token != 'secrettoken':
        raise HTTPException(status_code=401, detail='Invalid token')
    return {"valid": True}

# For compatibility with existing tests
@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# Reset endpoint for test isolation
@app.post('/reset')
def reset_state():
    global store, users
    store.clear()
    users.clear()
    users.update({
        'u1': {'id': 'u1', 'name': 'Alice', 'email': 'alice@example.com'},
        'u2': {'id': 'u2', 'name': 'Bob', 'email': 'bob@example.com'}
    })
    return {"status": "reset"}
