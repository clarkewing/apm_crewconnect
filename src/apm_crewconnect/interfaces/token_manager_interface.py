"""An interface for token managers."""

from abc import ABCMeta, abstractmethod
from typing import Optional


class TokenManagerInterface(metaclass=ABCMeta):
    """An interface for token managers."""

    @abstractmethod
    def set(self, **kwargs) -> None:
        """Set a token value."""
        raise NotImplementedError

    @abstractmethod
    def get(self, key: Optional[str] = None) -> dict[str, str | int] | None:
        """Get a token value."""
        raise NotImplementedError

    def has(self, key: str) -> bool:
        """Determine if a given key exists."""
        return self.get(key) != None
