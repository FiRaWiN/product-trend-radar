"""Data source abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import ProductSnapshot


class Source(ABC):
    """A product data source.

    Implementations return a list of snapshots for one fetch round.
    Fetch failures should raise SourceError so the pipeline can report
    and continue with other sources.
    """

    name: str = "base"

    @abstractmethod
    def fetch(self, keyword: str, max_results: int = 10) -> list[ProductSnapshot]:
        """Fetch products for a search keyword."""
        raise NotImplementedError


class SourceError(RuntimeError):
    pass
