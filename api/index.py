"""Vercel serverless wrapper for FastAPI - exposes app/api/main.py as /api/index.py"""
import sys
import os
import traceback

# Ensure project root is in sys.path for Vercel serverless functions
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from app.api.main import app
except Exception as exc:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    err_tb = traceback.format_exc()
    app = FastAPI(title="Vercel Startup Diagnostic")
    
    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    def error_handler(path: str = ""):
        return JSONResponse(status_code=500, content={"error": str(exc), "traceback": err_tb})


