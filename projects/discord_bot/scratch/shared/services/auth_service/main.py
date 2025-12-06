import os
from fastapi import FastAPI, HTTPException
from typing import Optional
from pydantic import BaseModel
from .token_utils import encode_access_token, decode_token

app = FastAPI(title="Auth JWT Service")

JWT_SECRET = os.environ.get("JWT_SECRET", "REPLACE_ME")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRES_MIN = int(os.environ.get("ACCESS_TOKEN_EXPIRES_MIN", "15"))
REFRESH_TOKEN_EXPIRES_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRES_DAYS", "7"))
JWT_AUDIENCE = os.environ.get("JWT_AUDIENCE", "auth")

class SignupRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@app.post("/signup")
def signup(req: SignupRequest):
    # In a real system, persist user
    return {"msg": f"user {req.username} signed up"}

@app.post("/login")
def login(req: LoginRequest):
    token = encode_access_token(
        subject=req.username,
        audience=JWT_AUDIENCE,
        secret=JWT_SECRET,
        algorithm=JWT_ALGORITHM,
        expires_min=ACCESS_TOKEN_EXPIRES_MIN,
    )
    return TokenResponse(access_token=token)

@app.get("/me")
def me(authorization: Optional[str] = None):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Authorization header missing or invalid")
    token = authorization.split(" ")[1]
    try:
        payload = decode_token(token, secret=JWT_SECRET, algorithm=JWT_ALGORITHM, audience=JWT_AUDIENCE)
        return {"user": payload.get("sub"), "aud": payload.get("aud")}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/refresh")
def refresh():
    # Placeholder refresh endpoint
    return {"msg": "refresh placeholder"}
