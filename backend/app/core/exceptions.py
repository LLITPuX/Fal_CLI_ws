"""Custom exceptions for domain-specific errors."""


class GeminiServiceException(Exception):
    """Base exception for Gemini service errors."""

    pass


class CLIExecutionError(GeminiServiceException):
    """CLI command execution failed."""

    pass


class JSONParsingError(GeminiServiceException):
    """Failed to parse JSON from CLI output."""

    pass


class ValidationException(GeminiServiceException):
    """Data validation failed."""

    pass


class DatabaseError(Exception):
    """Database operation failed."""

    pass


class ValidationError(Exception):
    """Input validation failed."""

    pass