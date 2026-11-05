"""Errores de la API y su cuerpo común `{"error": {"code", "message"}}` (api.md §6)."""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

STATUS_BAD_REQUEST = 400
STATUS_NOT_FOUND = 404
STATUS_METHOD_NOT_ALLOWED = 405
STATUS_INTERNAL_ERROR = 500
STATUS_SERVICE_UNAVAILABLE = 503

CODE_INVALID_PARAMETER = "invalid_parameter"
CODE_INVALID_CURSOR = "invalid_cursor"
CODE_NOT_FOUND = "not_found"
CODE_METHOD_NOT_ALLOWED = "method_not_allowed"
CODE_DATABASE_UNAVAILABLE = "database_unavailable"
CODE_INTERNAL_ERROR = "internal_error"

MESSAGE_NOT_FOUND = "La ruta solicitada no existe."
MESSAGE_METHOD_NOT_ALLOWED = "Método no permitido: esta ruta solo admite GET."
MESSAGE_DATABASE_UNAVAILABLE = "No se pudo consultar la base de datos. Inténtalo de nuevo más tarde."
MESSAGE_INTERNAL_ERROR = "Error interno de la API. Inténtalo de nuevo más tarde."

# Códigos HTTP de Starlette que se traducen al cuerpo común; cualquier otro usa un código genérico.
_HTTP_ERRORS = {
    STATUS_NOT_FOUND: (CODE_NOT_FOUND, MESSAGE_NOT_FOUND),
    STATUS_METHOD_NOT_ALLOWED: (CODE_METHOD_NOT_ALLOWED, MESSAGE_METHOD_NOT_ALLOWED),
}


class ApiError(Exception):
    """Error previsto de la API: se responde con su estado y el cuerpo de error común."""

    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def error_response(status: int, code: str, message: str, headers: dict[str, str] | None = None) -> JSONResponse:
    """Construye la respuesta JSON de error con el cuerpo común.

    Qué hace:
        Devuelve `{"error": {"code": ..., "message": ...}}` con el estado dado.
    Recibe:
        status: estado HTTP; code: código del contrato; message: texto en español; headers: opcionales.
    Devuelve:
        JSONResponse con `Content-Type: application/json`.
    Por qué existe:
        Todos los errores comparten una sola forma, sin `detail` (api.md §6, FR-013).
    """
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}},
                        headers=headers)


async def handle_api_error(request: Request, error: ApiError) -> JSONResponse:
    """Responde un `ApiError` con su estado y su cuerpo."""
    return error_response(error.status, error.code, error.message)


async def handle_http_error(request: Request, error: StarletteHTTPException) -> JSONResponse:
    """Traduce los 404 y 405 de Starlette (ruta o método inexistentes) al cuerpo común.

    Conserva la cabecera `Allow` del 405.
    """
    code, message = _HTTP_ERRORS.get(error.status_code, (CODE_INTERNAL_ERROR, MESSAGE_INTERNAL_ERROR))
    return error_response(error.status_code, code, message, dict(error.headers or {}))


async def handle_unexpected_error(request: Request, error: Exception) -> JSONResponse:
    """Responde 500 sin traza ni SQL; el detalle queda solo en el registro."""
    logger.error("Error inesperado en %s: %s", request.url.path, type(error).__name__, exc_info=error)
    return error_response(STATUS_INTERNAL_ERROR, CODE_INTERNAL_ERROR, MESSAGE_INTERNAL_ERROR)


def register_error_handlers(app: FastAPI) -> None:
    """Registra los manejadores globales de error en la aplicación."""
    app.add_exception_handler(ApiError, handle_api_error)
    app.add_exception_handler(StarletteHTTPException, handle_http_error)
    app.add_exception_handler(Exception, handle_unexpected_error)
