from typing import Any

from fastapi import HTTPException, status


class LabStockException(HTTPException):
    """Base exception for all domain and operational errors."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Any | None = None,
        headers: dict | None = None,
    ):
        super().__init__(status_code=status_code, detail=message, headers=headers)
        self.code = code
        self.message = message
        self.details = details


class AuthenticationFailedException(LabStockException):
    def __init__(self, message: str = "Invalid credentials provided"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTHENTICATION_FAILED",
            message=message,
            headers={"WWW-Authenticate": "Bearer"},
        )


class TokenExpiredException(LabStockException):
    def __init__(self, message: str = "Session token has expired"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="TOKEN_EXPIRED",
            message=message,
            headers={"WWW-Authenticate": "Bearer"},
        )


class PermissionDeniedException(LabStockException):
    def __init__(self, message: str = "Action not permitted for your current role"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="PERMISSION_DENIED",
            message=message,
        )


class UserInactiveException(LabStockException):
    def __init__(self, message: str = "User account has been deactivated"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="USER_INACTIVE",
            message=message,
        )


class NotFoundException(LabStockException):
    def __init__(self, entity: str, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code=f"{entity.upper()}_NOT_FOUND",
            message=f"{entity} '{identifier}' does not exist",
        )


class DuplicateSKUException(LabStockException):
    def __init__(self, sku: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="DUPLICATE_SKU",
            message=f"An item with SKU '{sku}' already exists",
            details={"sku": sku},
        )


class InsufficientStockException(LabStockException):
    def __init__(self, item_name: str, available: float, requested: float):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="INSUFFICIENT_STOCK",
            message=f"Insufficient available stock for '{item_name}'. Available: {available}, Requested: {requested}",
            details={"available": available, "requested": requested},
        )


class InvalidMovementException(LabStockException):
    def __init__(self, message: str, details: Any | None = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="INVALID_MOVEMENT",
            message=message,
            details=details,
        )


class PurchaseRequestStateConflictException(LabStockException):
    def __init__(self, message: str, details: Any | None = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="PURCHASE_REQUEST_STATE_CONFLICT",
            message=message,
            details=details,
        )


class ConflictException(LabStockException):
    def __init__(self, code: str, message: str, details: Any | None = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code=code,
            message=message,
            details=details,
        )


class DatabaseUnavailableException(LabStockException):
    def __init__(self, message: str = "Database service temporarily unavailable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="DATABASE_UNAVAILABLE",
            message=message,
        )
