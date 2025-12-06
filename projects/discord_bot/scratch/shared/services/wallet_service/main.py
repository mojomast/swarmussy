import os
from fastapi import FastAPI, HTTPException
from typing import Optional
from .token_utils import decode_token
from pydantic import BaseModel

app = FastAPI(title="Wallet JWT Service")
JWT_SECRET = os.environ.get("JWT_SECRET", "REPLACE_ME")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_AUDIENCE = os.environ.get("JWT_AUDIENCE", "wallet")

class TokenRequest(BaseModel):
    user: str

@app.get("/balance")
def balance(authorization: Optional[str] = None):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Authorization header missing or invalid")
    token = authorization.split(" ")[1]
    try:
        payload = decode_token(token, secret=JWT_SECRET, algorithm=JWT_ALGORITHM, audience=JWT_AUDIENCE)
        return {"balance": 1000, "user": payload.get("sub")}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/transfer")
def transfer(authorization: Optional[str] = None, amount: int = 0):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Authorization header missing or invalid")
    token = authorization.split(" ")[1]
    try:
        payload = decode_token(token, secret=JWT_SECRET, algorithm=JWT_ALGORITHM, audience=JWT_AUDIENCE)
        return {"status": "transferred", "amount": amount, "to": "recipient", "user": payload.get("sub")}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
