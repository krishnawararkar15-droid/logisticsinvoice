"""Vercel Serverless Function entrypoint for /api routes."""
import sys
from pathlib import Path

# Ensure root directory is in sys.path
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app, application, handler

__all__ = ["app", "application", "handler"]
