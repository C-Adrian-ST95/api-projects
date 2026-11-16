"""Enlaza el panel web de InventarioAPI con FastAPI, sin modificar el backend."""
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

RUTA_WEB = Path(__file__).resolve().parent / "web"


def montar_frontend(app: FastAPI) -> None:
    if not (RUTA_WEB / "index.html").exists():
        raise RuntimeError(f"No encuentro web/index.html en: {RUTA_WEB}")
    # URL principal: /app/  (con barra final)
    app.mount("/app", StaticFiles(directory=str(RUTA_WEB), html=True), name="web")
