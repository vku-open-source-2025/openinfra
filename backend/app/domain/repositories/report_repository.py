"""Report repository interface."""
from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.models.report import Report


class ReportRepository(ABC):
    """Report repository interface."""

    @abstractmethod
    async def create(self, report_data: dict) -> Report:
        """Create a new report."""
        pass

    @abstractmethod
    async def find_by_id(self, report_id: str) -> Optional[Report]:
        """Find report by ID."""
        pass

    @abstractmethod
    async def find_by_code(self, report_code: str) -> Optional[Report]:
        """Find report by code."""
        pass

    @abstractmethod
    async def update(self, report_id: str, updates: dict) -> Optional[Report]:
        """Update report."""
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Report]:
        """List reports with filtering."""
        pass

    @abstractmethod
    async def find_scheduled_reports(self) -> List[Report]:
        """Find reports that need to be generated."""
        pass
