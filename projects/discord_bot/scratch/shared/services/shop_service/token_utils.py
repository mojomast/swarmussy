from datetime import datetime, timedelta
import jwt


def encode_access_token(subject: str, audience: str, secret: str, algorithm: str = "HS256", expires_min: int = 15) -> str:
    exp = datetime.utcnow() + timedelta(minutes=expires_min)
    payload = {
        "sub": subject,
        "aud": audience,
        "exp": exp,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_token(token: str, secret: str, algorithm: str = "HS256", audience: str = None) -> dict:
    options = {"verify_aud": True} if audience is not None else {"verify_aud": False}
    return jwt.decode(token, secret, algorithms=[algorithm], audience=audience, options=options)
