"""
Point d'entree de l'API CoVeX et assemblage de l'application FastAPI.

Execution depuis la racine du projet:
- `uv run --project backend uvicorn main:app --app-dir backend/src --reload`
- `main:app` cible l'objet FastAPI expose par ce module.
- `--app-dir backend/src` ajoute le dossier source backend aux imports.
- `--reload` redemarre le serveur local a chaque modification de code.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from settings import APP_LOGGER_NAME, configure_logging, ensure_project_env_loaded

ensure_project_env_loaded()
configure_logging()

from analysis import router as analysis_router  # noqa: E402


logger = logging.getLogger(APP_LOGGER_NAME)


def create_app() -> FastAPI:
    app = FastAPI(title="CoVeX API", version="0.1.0")
    app.include_router(analysis_router)

    logger.info("Application startup complete")

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        logger.warning(
            "Request validation failed for %s %s: %s",
            request.method,
            request.url.path,
            exc.errors(),
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": "Requete invalide: verifiez les champs obligatoires et leur format."
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        if exc.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            logger.error(
                "HTTP error for %s %s: status=%s detail=%s",
                request.method,
                request.url.path,
                exc.status_code,
                exc.detail,
            )
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"status": "ok", "service": "covex-backend-bootstrap"}

    return app


app = create_app()
