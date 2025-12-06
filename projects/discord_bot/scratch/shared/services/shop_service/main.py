import os
from fastapi import FastAPI, HTTPException
from typing import Optional
from .token_utils import encode_access_token, decode_token
from pydantic import BaseModel

app = FastAPI(title="Shop JWT Service")
JWT_SECRET = os.environ.get("JWT_SECRET", "REPLACE_ME")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRES_MIN = int(os.environ.get("ACCESS_TOKEN_EXPIRES_MIN", "15"))
JWT_AUDIENCE = os.environ.get("JWT_AUDIENCE", "shop")

class Item(BaseModel):
    id: int
    price: float

@app.get("/items")
def items(authorization: Optional[str] = None):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Authorization header missing or invalid")
    token = authorization.split(" ")[1]
    try:
        payload = decode_token(token, secret=JWT_SECRET, algorithm=JWT_ALGORITHM, audience=JWT_AUDIENCE)
        return [{"id": 1, "name": "Widget", "price": 9.99}]
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/purchase")
def purchase(authorization: Optional[str] = None, item_id: int = 1):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Authorization header missing or invalid")
    token = authorization.split(" ")[1]
    try:
        payload = decode_token(token, secret=JWT_SECRET, algorithm=JWT_ALGORITHM, audience=JWT_AUDIENCE)
        return {"status": "purchased", "item": item_id, "user": payload.get("sub")}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
