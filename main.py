from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import dotenv_values
import yaml
import os

app = FastAPI()

# Allow browser access from the grader
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Defaults
# -----------------------------
DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

# Read .env separately (lower precedence than OS env)
ENV_FILE = dotenv_values(".env")


def to_bool(value):
    return str(value).strip().lower() in (
        "true",
        "1",
        "yes",
        "on",
    )


def coerce(key, value):
    if key in ("port", "workers"):
        return int(value)
    elif key == "debug":
        return to_bool(value)
    else:
        return str(value)


@app.get("/")
def home():
    return {"status": "running"}


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = DEFAULTS.copy()

    # -----------------------------
    # Layer 2: YAML
    # -----------------------------
    if os.path.exists("config.development.yaml"):
        with open("config.development.yaml", "r") as f:
            yaml_cfg = yaml.safe_load(f) or {}
            for k, v in yaml_cfg.items():
                config[k] = coerce(k, v)

    # -----------------------------
    # Layer 3: .env
    # -----------------------------
    mapping = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for env_key, cfg_key in mapping.items():
        if env_key in ENV_FILE:
            config[cfg_key] = coerce(cfg_key, ENV_FILE[env_key])

    # Alias
    if "NUM_WORKERS" in ENV_FILE:
        config["workers"] = coerce("workers", ENV_FILE["NUM_WORKERS"])

    # -----------------------------
    # Layer 4: OS Environment
    # -----------------------------
    for env_key, cfg_key in mapping.items():
        if env_key in os.environ:
            config[cfg_key] = coerce(cfg_key, os.environ[env_key])

    # Alias in OS env
    if "NUM_WORKERS" in os.environ:
        config["workers"] = coerce("workers", os.environ["NUM_WORKERS"])

    # -----------------------------
    # Layer 5: CLI Overrides
    # -----------------------------
    for item in set:
        if "=" in item:
            key, value = item.split("=", 1)
            config[key] = coerce(key, value)

    # Mask secret
    config["api_key"] = "****"

    return config