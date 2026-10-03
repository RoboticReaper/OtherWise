"""Run with .venv/bin/python -m uvicorn main:app --host 127.0.0.1."""

from service.api import create_app

app = create_app()
