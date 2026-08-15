"""Rutas comunes para ejecutar toda la suite desde cualquier directorio."""
import os
import sys


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(BACKEND_DIR, "src")

for ruta in (BACKEND_DIR, SRC_DIR):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)
