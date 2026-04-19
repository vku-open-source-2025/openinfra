"""After-action report repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.models.after_action_report import AfterActionReport


class AfterActionReportRepository(ABC):
    """Repository contract for after-action reports."""

    @abstractmethod
    async def create(self, payload: dict) -> AfterActionReport:
        """Create a new after-action report."""
        pass

    @abstractmethod
    async def find_by_id(self, report_id: str) -> Optional[AfterActionReport]:
        """Find report by id."""
        pass

    @abstractmethod
    async def find_latest_by_event(self, emergency_event_id: str) -> Optional[AfterActionReport]:
        """Find latest report for one emergency event."""
        pass

    @abstractmethod
    async def update(self, report_id: str, updates: dict) -> Optional[AfterActionReport]:
        """Update report by id."""
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        emergency_event_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[AfterActionReport]:
        """List reports with optional filtering."""
        pass
