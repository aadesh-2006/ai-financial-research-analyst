"""Centralized exception handlers and HTTP error mapping for FastAPI."""
from typing import Any, Dict
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import requests
from sqlalchemy.exc import SQLAlchemyError

from app.research.llm import LLMAPIError, LLMKeyMissingError, LLMResponseParsingError
from app.utils.logging import logger


class APIError(Exception):
    """Base API exception carrying HTTP status and structured error code."""
    def __init__(self, status_code: int, code: str, message: str, details: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


def build_error_response(status_code: int, code: str, message: str, details: Any = None) -> JSONResponse:
    """Builds a standardized, sanitized JSON error payload."""
    content: Dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    if details is not None:
        content["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=content)


def register_exception_handlers(app: FastAPI) -> None:
    """Registers standardized error handlers across the FastAPI application."""

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        logger.warning(f"APIError [{exc.code}] on {request.url.path}: {exc.message}")
        return build_error_response(exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
        # Sanitize error messages
        clean_errors = []
        for err in exc.errors():
            loc = " -> ".join(str(l) for l in err.get("loc", []))
            msg = err.get("msg", "Invalid value")
            clean_errors.append(f"{loc}: {msg}")
        return build_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_REQUEST",
            message="Request validation failed. Please check your parameters.",
            details=clean_errors,
        )

    @app.exception_handler(LLMKeyMissingError)
    async def llm_key_missing_handler(request: Request, exc: LLMKeyMissingError) -> JSONResponse:
        logger.warning(f"LLMKeyMissingError on {request.url.path}: {exc}")
        return build_error_response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="OPENAI_API_KEY_MISSING",
            message="AI research synthesis is unavailable because OPENAI_API_KEY is not configured.",
        )

    @app.exception_handler(LLMAPIError)
    async def llm_api_error_handler(request: Request, exc: LLMAPIError) -> JSONResponse:
        logger.error(f"LLMAPIError on {request.url.path}: {exc}")
        exc_str = str(exc).lower()
        if "rate limit" in exc_str:
            return build_error_response(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                code="OPENAI_RATE_LIMIT",
                message="OpenAI rate limit exceeded. Please try again shortly.",
            )
        elif "timeout" in exc_str:
            return build_error_response(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                code="OPENAI_TIMEOUT",
                message="AI research service request timed out.",
            )
        elif "authentication" in exc_str:
            return build_error_response(
                status_code=status.HTTP_502_BAD_GATEWAY,
                code="OPENAI_AUTH_ERROR",
                message="Authentication failure with AI research provider.",
            )
        return build_error_response(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="OPENAI_API_ERROR",
            message="Upstream AI research service encountered a communication error.",
        )

    @app.exception_handler(LLMResponseParsingError)
    async def llm_parsing_error_handler(request: Request, exc: LLMResponseParsingError) -> JSONResponse:
        logger.error(f"LLMResponseParsingError on {request.url.path}: {exc}")
        return build_error_response(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="RESEARCH_PARSING_ERROR",
            message="Failed to parse structured research report from model response.",
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        logger.warning(f"ValueError on {request.url.path}: {exc}")
        # Typically raised by DataOrchestrator when ticker has no data
        return build_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="TICKER_NOT_FOUND",
            message=str(exc),
        )

    @app.exception_handler(requests.RequestException)
    async def upstream_network_error_handler(request: Request, exc: requests.RequestException) -> JSONResponse:
        logger.error(f"Upstream network error on {request.url.path}: {exc}")
        return build_error_response(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="UPSTREAM_DATA_ERROR",
            message="Failed to retrieve upstream market or SEC financial data.",
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        # Strictly sanitize database exceptions: never disclose connection strings, credentials or internals
        logger.error(f"Database error on {request.url.path}: {exc}")
        return build_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="DATABASE_ERROR",
            message="A database operation failed while persisting or retrieving data.",
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Strictly sanitize internal exceptions: never leak stack traces or credentials
        logger.exception(f"Unhandled exception on {request.url.path}: {exc}")
        return build_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal server error occurred.",
        )