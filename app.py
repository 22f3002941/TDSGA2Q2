from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import yaml
import os
import jwt

load_dotenv()

app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# 1. CONFIG SERVICE (/effective-config)
# =====================================================

config = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

# YAML layer
with open("config.development.yaml") as f:
    config.update(yaml.safe_load(f))

# .env layer
if os.getenv("NUM_WORKERS"):
    config["workers"] = int(os.getenv("NUM_WORKERS"))

if os.getenv("APP_LOG_LEVEL"):
    config["log_level"] = os.getenv("APP_LOG_LEVEL")

if os.getenv("APP_API_KEY"):
    config["api_key"] = os.getenv("APP_API_KEY")

# OS env overrides (simulated)
os.environ["APP_PORT"] = "8195"
os.environ["APP_LOG_LEVEL"] = "error"

if os.getenv("APP_PORT"):
    config["port"] = int(os.getenv("APP_PORT"))

if os.getenv("APP_LOG_LEVEL"):
    config["log_level"] = os.getenv("APP_LOG_LEVEL")


def coerce(key, value):
    if key in ("port", "workers"):
        return int(value)

    if key == "debug":
        return str(value).lower() in ("true", "1", "yes", "on")

    return str(value)


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    result = config.copy()

    for item in set:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)

        if key in result:
            result[key] = coerce(key, value)

    result["api_key"] = "****"
    return result


# =====================================================
# 2. OAUTH SERVICE (/verify)
# =====================================================

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----"""

ISSUER = "https://idp.exam.local"
AUDIENCE = "tds-bx76wkki.apps.exam.local"


class TokenRequest(BaseModel):
    token: str


@app.post("/verify")
def verify(req: TokenRequest):
    try:
        payload = jwt.decode(
            req.token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            issuer=ISSUER,
            audience=AUDIENCE,
        )

        return {
            "valid": True,
            "email": payload.get("email"),
            "sub": payload.get("sub"),
            "aud": payload.get("aud"),
        }

    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail={"valid": False}
        )


# Optional root
@app.get("/")
def root():
    return {"status": "running"}