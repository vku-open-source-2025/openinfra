"""Budgets API router."""
from fastapi import APIRouter, Query, Depends, HTTPException, status
from typing import List, Optional
from app.domain.models.budget import (
    Budget, BudgetCreate, BudgetUpdate, BudgetTransaction,
    BudgetTransactionCreate
)
from app.domain.services.budget_service import BudgetService
from app.api.v1.dependencies import get_budget_service
from app.api.v1.middleware import get_current_user
from app.domain.models.user import User

router = APIRouter()


@router.get("", response_model=List[Budget])
async def list_budgets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    fiscal_year: Optional[int] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    budget_service: BudgetService = Depends(get_budget_service)
):
    """List budgets with filtering."""
    return await budget_service.list_budgets(skip, limit, fiscal_year, status, category)


@router.post("", response_model=Budget, status_code=status.HTTP_201_CREATED)
async def create_budget(
    budget_data: BudgetCreate,
    current_user: User = Depends(get_current_user),
    budget_service: BudgetService = Depends(get_budget_service)
):
    """Create a new budget."""
    return await budget_service.create_budget(budget_data, str(current_user.id))


@router.get("/{budget_id}", response_model=Budget)
async def get_budget(
    budget_id: str,
    budget_service: BudgetService = Depends(get_budget_service)
):
    """Get budget details."""
    return await budget_service.get_budget_by_id(budget_id)


@router.put("/{budget_id}", response_model=Budget)
async def update_budget(
    budget_id: str,
    updates: BudgetUpdate,
    budget_service: BudgetService = Depends(get_budget_service)
):
    """Update budget."""
    return await budget_service.update_budget(budget_id, updates)


@router.post("/{budget_id}/submit", response_model=Budget)
async def submit_budget(
    budget_id: str,
    current_user: User = Depends(get_current_user),
    budget_service: BudgetService = Depends(get_budget_service)
):
    """Submit budget for approval."""
    return await budget_service.submit_budget_for_approval(budget_id, str(current_user.id))


@router.post("/{budget_id}/approve", response_model=Budget)
async def approve_budget(
    budget_id: str,
    current_user: User = Depends(get_current_user),
    budget_service: BudgetService = Depends(get_budget_service)
):
    """Approve a budget."""
    return await budget_service.approve_budget(budget_id, str(current_user.id))


@router.get("/{budget_id}/transactions", response_model=List[BudgetTransaction])
async def list_budget_transactions(
    budget_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    budget_service: BudgetService = Depends(get_budget_service)
):
    """List transactions for a budget."""
    return await budget_service.list_transactions(budget_id, skip, limit)


@router.post("/{budget_id}/transactions", response_model=BudgetTransaction, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    budget_id: str,
    transaction_data: BudgetTransactionCreate,
    current_user: User = Depends(get_current_user),
    budget_service: BudgetService = Depends(get_budget_service)
):
    """Create a budget transaction."""
    transaction_data.budget_id = budget_id
    return await budget_service.create_transaction(transaction_data, str(current_user.id))


@router.post("/transactions/{transaction_id}/approve", response_model=BudgetTransaction)
async def approve_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    budget_service: BudgetService = Depends(get_budget_service)
):
    """Approve a budget transaction."""
    return await budget_service.approve_transaction(transaction_id, str(current_user.id))
