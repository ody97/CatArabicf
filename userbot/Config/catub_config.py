import os

ENV = bool(os.environ.get("ENV", False))

if ENV:
    pass
elif os.path.exists("config.py"):
    pass
