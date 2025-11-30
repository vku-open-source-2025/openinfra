"""MongoDB implementation of budget repository."""

from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.domain.models.budget import Budget, BudgetTransaction
from app.domain.repositories.budget_repository import (
    BudgetRepository,
    BudgetTransactionRepository,
)
from app.infrastructure.database.repositories.base_repository import (
    convert_objectid_to_str,
)
from datetime import datetime


class MongoBudgetRepository(BudgetRepository):
    """MongoDB budget repository implementation."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["budgets"]

    async def create(self, budget_data: dict) -> Budget:
        """Create a new budget."""
        budget_data["created_at"] = datetime.utcnow()
        budget_data["updated_at"] = datetime.utcnow()
        # Calculate initial remaining
        if "total_remaining" not in budget_data:
            budget_data["total_remaining"] = budget_data.get("total_allocated", 0)
        result = await self.collection.insert_one(budget_data)
        budget_doc = await self.collection.find_one({"_id": result.inserted_id})
        budget_doc = convert_objectid_to_str(budget_doc)
        return Budget(**budget_doc)

    async def find_by_id(self, budget_id: str) -> Optional[Budget]:
        """Find budget by ID."""
        if not ObjectId.is_valid(budget_id):
            return None
        budget_doc = await self.collection.find_one({"_id": ObjectId(budget_id)})
        if budget_doc:
            budget_doc = convert_objectid_to_str(budget_doc)
            return Budget(**budget_doc)
        return None

    async def find_by_code(self, budget_code: str) -> Optional[Budget]:
        """Find budget by code."""
        budget_doc = await self.collection.find_one({"budget_code": budget_code})
        if budget_doc:
            budget_doc = convert_objectid_to_str(budget_doc)
            return Budget(**budget_doc)
        return None

    async def update(self, budget_id: str, updates: dict) -> Optional[Budget]:
        """Update budget."""
        if not ObjectId.is_valid(budget_id):
            return None
        updates["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(budget_id)}, {"$set": updates}
        )
        return await self.find_by_id(budget_id)

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        fiscal_year: Optional[int] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Budget]:
        """List budgets with filtering."""
        query = {}
        if fiscal_year:
            query["fiscal_year"] = fiscal_year
        if status:
            query["status"] = status
        if category:
            query["category"] = category

        cursor = (
            self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        )
        budgets = []
        async for budget_doc in cursor:
            budget_doc = convert_objectid_to_str(budget_doc)
            budgets.append(Budget(**budget_doc))
        return budgets


class MongoBudgetTransactionRepository(BudgetTransactionRepository):
    """MongoDB budget transaction repository implementation."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["budget_transactions"]

    async def create(self, transaction_data: dict) -> BudgetTransaction:
        """Create a new transaction."""
        transaction_data["created_at"] = datetime.utcnow()
        transaction_data["updated_at"] = datetime.utcnow()
        result = await self.collection.insert_one(transaction_data)
        transaction_doc = await self.collection.find_one({"_id": result.inserted_id})
        transaction_doc = convert_objectid_to_str(transaction_doc)
        return BudgetTransaction(**transaction_doc)

    async def find_by_id(self, transaction_id: str) -> Optional[BudgetTransaction]:
        """Find transaction by ID."""
        if not ObjectId.is_valid(transaction_id):
            return None
        transaction_doc = await self.collection.find_one(
            {"_id": ObjectId(transaction_id)}
        )
        if transaction_doc:
            transaction_doc = convert_objectid_to_str(transaction_doc)
            return BudgetTransaction(**transaction_doc)
        return None

    async def find_by_budget(
        self, budget_id: str, skip: int = 0, limit: int = 100
    ) -> List[BudgetTransaction]:
        """Find transactions for a budget."""
        query = {"budget_id": budget_id}
        cursor = (
            self.collection.find(query)
            .sort("transaction_date", -1)
            .skip(skip)
            .limit(limit)
        )
        transactions = []
        async for transaction_doc in cursor:
            transaction_doc = convert_objectid_to_str(transaction_doc)
            transactions.append(BudgetTransaction(**transaction_doc))
        return transactions

    async def update(
        self, transaction_id: str, updates: dict
    ) -> Optional[BudgetTransaction]:
        """Update transaction."""
        if not ObjectId.is_valid(transaction_id):
            return None
        updates["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(transaction_id)}, {"$set": updates}
        )
        return await self.find_by_id(transaction_id)

    async def calculate_budget_totals(self, budget_id: str) -> dict:
        """Calculate total spent and committed for a budget."""
        pipeline = [
            {"$match": {"budget_id": budget_id}},
            {"$group": {"_id": "$status", "total": {"$sum": "$amount"}}},
        ]

        results = {}
        async for doc in self.collection.aggregate(pipeline):
            status = doc["_id"]
            results[status] = doc["total"]

        total_spent = results.get("paid", 0.0) + results.get("approved", 0.0)
        total_committed = results.get("pending", 0.0) + results.get("approved", 0.0)

        return {
            "total_spent": total_spent,
            "total_committed": total_committed,
            "by_status": results,
        }
