"""Application-level exceptions."""

from fastapi import status


class AppException(Exception):
    """Base application exception that maps to an API error response."""

    def __init__(
        self,
        *,
        message: str,
        error_code: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


class NotFoundException(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str = "Resource not found", details: dict | None = None) -> None:
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class ConflictException(AppException):
    """Raised when a resource conflicts with an existing state."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(
            message=message,
            error_code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class AuthorizationException(AppException):
    """Raised when a user lacks required permissions."""

    def __init__(self, message: str = "Forbidden", details: dict | None = None) -> None:
        super().__init__(
            message=message,
            error_code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class AuthenticationException(AppException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Unauthorized", details: dict | None = None) -> None:
        super().__init__(
            message=message,
            error_code="UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class ValidationException(AppException):
    """Raised for business-rule validation failures."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(
            message=message,
            error_code="BUSINESS_RULE_VIOLATION",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )
