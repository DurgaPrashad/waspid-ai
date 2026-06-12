from typing import Any

from fastapi import HTTPException, status


class WaspidError(HTTPException):
    """General Error"""

    def __init__(
        self,
        detail: Any = None,
        headers: dict[str, str] | None = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class AuthError(WaspidError):
    """Error in authentication."""

    def __init__(
        self,
        detail: Any = None,
        headers: dict[str, str] | None = None,
        status_code: int = status.HTTP_401_UNAUTHORIZED,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class PermissionsError(WaspidError):
    """Error in permissions."""

    def __init__(
        self,
        detail: Any = None,
        headers: dict[str, str] | None = None,
        status_code: int = status.HTTP_403_FORBIDDEN,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class SandboxError(WaspidError):
    """Error in Sandbox."""
