"""Budget service for managing budgets and transactions."""
from typing import Optional, List
from datetime import datetime
from app.domain.models.budget import (
    Budget, BudgetCreate, BudgetUpdate, BudgetTransaction,
    BudgetTransactionCreate, BudgetStatus
)
from app.domain.repositories.budget_repository import BudgetRepository, BudgetTransactionRepository
from app.core.exceptions import NotFoundError, ConflictError, ValidationError
import logging
import uuid

logger = logging.getLogger(__name__)


class BudgetService:
    """Budget service for business logic."""

    def __init__(
        self,
        budget_repository: BudgetRepository,
        transaction_repository: BudgetTransactionRepository
    ):
        self.budget_repository = budget_repository
        self.transaction_repository = transaction_repository

    def _generate_budget_code(self, fiscal_year: int, period_type: str) -> str:
        """Generate unique budget code."""
        period_short = period_type[:3].upper()
        sequence = uuid.uuid4().hex[:4].upper()
        return f"BDG-{fiscal_year}-{period_short}-{sequence}"

    def _generate_transaction_number(self) -> str:
        """Generate unique transaction number."""
        year = datetime.utcnow().year
        sequence = uuid.uuid4().hex[:8].upper()
        return f"TXN-{year}-{sequence}"

    async def create_budget(
        self,
        budget_data: BudgetCreate,
        created_by: str
    ) -> Budget:
        """Create a new budget."""
        # Generate budget code
        budget_code = self._generate_budget_code(
            budget_data.fiscal_year,
            budget_data.period_type.value
        )

        # Check if code exists
        existing = await self.budget_repository.find_by_code(budget_code)
        if existing:
            budget_code = self._generate_budget_code(
                budget_data.fiscal_year,
                budget_data.period_type.value
            )

        budget_dict = budget_data.dict(exclude_unset=True)
        budget_dict["budget_code"] = budget_code
        budget_dict["created_by"] = created_by
        budget_dict["status"] = BudgetStatus.DRAFT.value
        budget_dict["total_remaining"] = budget_data.total_allocated
        budget_dict["utilization_rate"] = 0.0

        # Calculate department remaining amounts
        for dept in budget_dict.get("departments", []):
            if isinstance(dept, dict):
                dept["remaining_amount"] = dept.get("allocated_amount", 0)

        # Calculate breakdown remaining amounts
        for item in budget_dict.get("breakdown", []):
            if isinstance(item, dict):
                item["remaining"] = item.get("allocated", 0)

        budget = await self.budget_repository.create(budget_dict)
        logger.info(f"Created budget: {budget.budget_code}")
        return budget

    async def get_budget_by_id(self, budget_id: str) -> Budget:
        """Get budget by ID."""
        budget = await self.budget_repository.find_by_id(budget_id)
        if not budget:
            raise NotFoundError("Budget", budget_id)
        return budget

    async def submit_budget_for_approval(
        self,
        budget_id: str,
        submitted_by: str
    ) -> Budget:
        """Submit budget for approval."""
        budget = await self.get_budget_by_id(budget_id)

        if budget.status != BudgetStatus.DRAFT.value:
            raise ValidationError("Only draft budgets can be submitted for approval")

        updated = await self.budget_repository.update(
            budget_id,
            {
                "status": BudgetStatus.PENDING_APPROVAL.value,
                "submitted_by": submitted_by,
                "submitted_at": datetime.utcnow()
            }
        )
        if not updated:
            raise NotFoundError("Budget", budget_id)
        return updated

    async def approve_budget(
        self,
        budget_id: str,
        approved_by: str
    ) -> Budget:
        """Approve a budget."""
        budget = await self.get_budget_by_id(budget_id)

        if budget.status != BudgetStatus.PENDING_APPROVAL.value:
            raise ValidationError("Only pending budgets can be approved")

        updated = await self.budget_repository.update(
            budget_id,
            {
                "status": BudgetStatus.APPROVED.value,
                "approved_by": approved_by,
                "approved_at": datetime.utcnow()
            }
        )
        if not updated:
            raise NotFoundError("Budget", budget_id)

        # Activate budget
        await self.activate_budget(budget_id)
        return await self.get_budget_by_id(budget_id)

    async def activate_budget(self, budget_id: str) -> Budget:
        """Activate an approved budget."""
        budget = await self.get_budget_by_id(budget_id)

        if budget.status != BudgetStatus.APPROVED.value:
            raise ValidationError("Only approved budgets can be activated")

        updated = await self.budget_repository.update(
            budget_id,
            {"status": BudgetStatus.ACTIVE.value}
        )
        if not updated:
            raise NotFoundError("Budget", budget_id)
        return updated

    async def create_transaction(
        self,
        transaction_data: BudgetTransactionCreate,
        created_by: str
    ) -> BudgetTransaction:
        """Create a budget transaction."""
        # Verify budget exists and is active
        budget = await self.get_budget_by_id(transaction_data.budget_id)

        if budget.status != BudgetStatus.ACTIVE.value:
            raise ValidationError("Transactions can only be created for active budgets")

        # Generate transaction number
        transaction_number = self._generate_transaction_number()

        transaction_dict = transaction_data.dict(exclude_unset=True)
        transaction_dict["transaction_number"] = transaction_number
        transaction_dict["created_by"] = created_by
        transaction_dict["status"] = "pending"

        transaction = await self.transaction_repository.create(transaction_dict)

        # Update budget totals
        await self._update_budget_totals(transaction_data.budget_id)

        logger.info(f"Created transaction: {transaction.transaction_number}")
        return transaction

    async def approve_transaction(
        self,
        transaction_id: str,
        approved_by: str
    ) -> BudgetTransaction:
        """Approve a transaction."""
        transaction = await self.transaction_repository.find_by_id(transaction_id)
        if not transaction:
            raise NotFoundError("Transaction", transaction_id)

        if transaction.status != "pending":
            raise ValidationError("Only pending transactions can be approved")

        # Check budget availability
        budget = await self.get_budget_by_id(transaction.budget_id)
        totals = await self.transaction_repository.calculate_budget_totals(transaction.budget_id)

        available = budget.total_allocated - totals["total_spent"] - totals["total_committed"]
        if transaction.amount > available:
            raise ValidationError(f"Insufficient budget. Available: {available}, Requested: {transaction.amount}")

        updated = await self.transaction_repository.update(
            transaction_id,
            {
                "status": "approved",
                "approved_by": approved_by,
                "approved_at": datetime.utcnow()
            }
        )
        if not updated:
            raise NotFoundError("Transaction", transaction_id)

        # Update budget totals
        await self._update_budget_totals(transaction.budget_id)

        return updated

    async def _update_budget_totals(self, budget_id: str):
        """Update budget totals based on transactions."""
        totals = await self.transaction_repository.calculate_budget_totals(budget_id)
        budget = await self.get_budget_by_id(budget_id)

        total_spent = totals["total_spent"]
        total_committed = totals["total_committed"]
        total_remaining = budget.total_allocated - total_spent - total_committed
        utilization_rate = (total_spent / budget.total_allocated * 100) if budget.total_allocated > 0 else 0

        await self.budget_repository.update(
            budget_id,
            {
                "total_spent": total_spent,
                "total_committed": total_committed,
                "total_remaining": total_remaining,
                "utilization_rate": utilization_rate
            }
        )

    async def list_budgets(
        self,
        skip: int = 0,
        limit: int = 100,
        fiscal_year: Optional[int] = None,
        status: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Budget]:
        """List budgets with filtering."""
        return await self.budget_repository.list(skip, limit, fiscal_year, status, category)

    async def list_transactions(
        self,
        budget_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[BudgetTransaction]:
        """List transactions for a budget."""
        return await self.transaction_repository.find_by_budget(budget_id, skip, limit)

    async def update_budget(
        self,
        budget_id: str,
        updates: BudgetUpdate
    ) -> Budget:
        """Update budget."""
        budget = await self.get_budget_by_id(budget_id)

        if budget.status not in [BudgetStatus.DRAFT.value, BudgetStatus.PENDING_APPROVAL.value]:
            raise ValidationError("Only draft or pending budgets can be updated")

        update_dict = updates.dict(exclude_unset=True)

        # Recalculate remaining if total_allocated changed
        if "total_allocated" in update_dict:
            update_dict["total_remaining"] = update_dict["total_allocated"] - budget.total_spent

        updated = await self.budget_repository.update(budget_id, update_dict)
        if not updated:
            raise NotFoundError("Budget", budget_id)
        return updated
