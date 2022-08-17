from os import environ as env
import multiprocessing

PORT = int(env.get("PORT", 8080))
ADDRESS = env.get("ADDRESS", "0.0.0.0")
DEBUG_MODE = int(env.get("DEBUG_MODE", 1))
WORKER_TIMEOUT_MINUTES = 3

# Gunicorn config
bind = f"{ADDRESS}:{PORT}"
#workers = multiprocessing.cpu_count() * 2 + 1
workers = 4
threads = 2 * multiprocessing.cpu_count()
timeout = 60 * WORKER_TIMEOUT_MINUTES
