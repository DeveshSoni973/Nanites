class DomainError(Exception):
    """Base class for all application errors."""

    pass


class ValidationError(DomainError):
    """Raised when business logic rules fail."""

    pass


class ResourceNotFoundError(DomainError):
    """Raised when a DB record isn't found."""

    pass


class AuthenticationError(DomainError):
    """Raised when login/auth fails."""

    pass
