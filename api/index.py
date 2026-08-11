"""Punto de entrada para Vercel (runtime Python).

Agrega backend/src al path e importa la app FastAPI. Vercel enruta todo aquí.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend", "src"))

from main import app  # noqa: E402,F401
