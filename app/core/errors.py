"""Stable, centralized error codes and client-facing messages."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ErrorDefinition:
    code: str
    message: str
    status_code: int


PAYLOAD_NOT_FOUND = ErrorDefinition(
    "PAYLOAD_NOT_FOUND", "The requested payload was not found.", 404
)
INVALID_INPUT = ErrorDefinition("INVALID_INPUT", "The request contains invalid input.", 422)
INTERNAL_ERROR = ErrorDefinition("INTERNAL_ERROR", "An unexpected error occurred.", 500)
DATABASE_UNAVAILABLE = ErrorDefinition(
    "DATABASE_UNAVAILABLE", "The service is temporarily unavailable.", 503
)
HTTP_ERROR = ErrorDefinition("HTTP_ERROR", "The request could not be completed.", 400)
