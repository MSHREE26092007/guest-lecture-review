"""Vercel serverless wrapper for FastAPI - exposes app/api/main.py as /api/index.py"""
from app.api.main import app
# Vercel will call `app` as ASGI app
