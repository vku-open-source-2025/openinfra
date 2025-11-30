"""Budget repository interface."""
from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.models.budget import Budget, BudgetTransaction


class BudgetRepository(ABC):
    """Budget repository interface."""

    @abstractmethod
    async def create(self, budget_data: dict) -> Budget:
        """Create a new budget."""
        pass

    @abstractmethod
    async def find_by_id(self, budget_id: str) -> Optional[Budget]:
        """Find budget by ID."""
        pass

    @abstractmethod
    async def find_by_code(self, budget_code: str) -> Optional[Budget]:
        """Find budget by code."""
        pass

    @abstractmethod
    async def update(self, budget_id: str, updates: dict) -> Optional[Budget]:
        """Update budget."""
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        fiscal_year: Optional[int] = None,
        status: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Budget]:
        """List budgets with filtering."""
        pass


class BudgetTransactionRepository(ABC):
    """Budget transaction repository interface."""

    @abstractmethod
    async def create(self, transaction_data: dict) -> BudgetTransaction:
        """Create a new transaction."""
        pass

    @abstractmethod
    async def find_by_id(self, transaction_id: str) -> Optional[BudgetTransaction]:
        """Find transaction by ID."""
        pass

    @abstractmethod
    async def find_by_budget(self, budget_id: str, skip: int = 0, limit: int = 100) -> List[BudgetTransaction]:
        """Find transactions for a budget."""
        pass

    @abstractmethod
    async def update(self, transaction_id: str, updates: dict) -> Optional[BudgetTransaction]:
        """Update transaction."""
        pass

    @abstractmethod
    async def calculate_budget_totals(self, budget_id: str) -> dict:
        """Calculate total spent and committed for a budget."""
        pass
