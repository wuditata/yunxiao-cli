from __future__ import annotations

from typing import Any


class CliError(Exception):
    """CLI business error."""

    def __init__(self, message: str, *, response: dict[str, Any] | None = None):
        super().__init__(message)
        self.response = response or {}
