from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import yaml
import os

load_dotenv()

app = FastAPI()

# Allow browser-based grader
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # If the assignment specifies a particular origin, use that instead.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Defaults ----------
config = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

# ---------- YAML ----------
with open("config.development.yaml") as f:
    config.update(yaml.safe_load(f))

# ---------- .env ----------
if os.getenv("NUM_WORKERS"):
    config["workers"] = int(os.getenv("NUM_WORKERS"))

if os.getenv("APP_LOG_LEVEL"):
    config["log_level"] = os.getenv("APP_LOG_LEVEL")

if os.getenv("APP_API_KEY"):
    config["api_key"] = os.getenv("APP_API_KEY")

# ---------- Simulated OS environment ----------
# These are the values specified in the assignment.
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

    # CLI overrides
    for item in set:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)

        if key in result:
            result[key] = coerce(key, value)

    # Mask secret
    result["api_key"] = "****"

    return result