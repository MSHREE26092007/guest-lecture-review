"""Vercel serverless wrapper for FastAPI - exposes app/api/main.py as /api/index.py"""
import sys
import os

# Ensure project root is in sys.path for Vercel serverless functions
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.api.main import app
# Vercel will call `app` as ASGI app

