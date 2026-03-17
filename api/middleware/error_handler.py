from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def _err(code: str, message: str, status: int, details: dict = None) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "details": details or {}}}
    )


def register_error_handlers(app: FastAPI):
    @app.exception_handler(ValueError)
    async def value_error_handler(req: Request, exc: ValueError):
        code = str(exc)
        status = 409 if "EXISTS" in code else 400
        return _err(code, str(exc), status)

    @app.exception_handler(PermissionError)
    async def permission_error_handler(req: Request, exc: PermissionError):
        return _err(str(exc), "Authentication failed.", 401)

    @app.exception_handler(KeyError)
    async def key_error_handler(req: Request, exc: KeyError):
        return _err(str(exc).strip("'"), "Resource not found.", 404)

    @app.exception_handler(Exception)
    async def generic_handler(req: Request, exc: Exception):
        return _err("INTERNAL_ERROR", "An unexpected error occurred.", 500)
