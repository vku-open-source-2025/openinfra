"""Budget domain model."""
from pydantic import BaseModel, Field, field_serializer, field_validator
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum
from bson import ObjectId


class BudgetPeriodType(str, Enum):
    """Budget period type enumeration."""
    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    MONTHLY = "monthly"
    PROJECT_BASED = "project-based"


class BudgetCategory(str, Enum):
    """Budget category enumeration."""
    MAINTENANCE = "maintenance"
    CAPITAL = "capital"
    OPERATIONS = "operations"
    EMERGENCY = "emergency"


class BudgetStatus(str, Enum):
    """Budget status enumeration."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ACTIVE = "active"
    CLOSED = "closed"


class DepartmentAllocation(BaseModel):
    """Department allocation value object."""
    department: str
    allocated_amount: float
    spent_amount: float = 0.0
    remaining_amount: float = 0.0


class BudgetBreakdown(BaseModel):
    """Budget breakdown by type value object."""
    category: str  # "labor" | "materials" | "equipment" | "contractors"
    allocated: float
    spent: float = 0.0
    remaining: float = 0.0


class AssetAllocation(BaseModel):
    """Asset category allocation value object."""
    feature_type: str
    allocated: float
    spent: float = 0.0
    count: int = 0


class BudgetAttachment(BaseModel):
    """Budget attachment model."""
    file_name: str
    file_url: str
    file_type: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class Budget(BaseModel):
    """Budget domain entity."""
    id: Optional[str] = Field(alias="_id", default=None)
    budget_code: str

    # Budget Period
    fiscal_year: int
    period_type: BudgetPeriodType
    start_date: datetime
    end_date: datetime

    # Budget Details
    name: str
    description: Optional[str] = None
    category: BudgetCategory

    # Allocation
    total_allocated: float
    departments: List[DepartmentAllocation] = Field(default_factory=list)

    # Breakdown by Type
    breakdown: List[BudgetBreakdown] = Field(default_factory=list)

    # Asset Categories
    asset_allocations: List[AssetAllocation] = Field(default_factory=list)

    # Financial Tracking
    currency: str = "VND"
    total_spent: float = 0.0
    total_committed: float = 0.0
    total_remaining: float = 0.0
    utilization_rate: float = 0.0  # percentage

    # Approval
    status: BudgetStatus = BudgetStatus.DRAFT
    submitted_by: Optional[str] = None
    submitted_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    # Tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    closed_at: Optional[datetime] = None
    closed_by: Optional[str] = None

    # Notes
    notes: Optional[str] = None
    attachments: List[BudgetAttachment] = Field(default_factory=list)

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, v: Any):
        """Convert ObjectId to string."""
        if isinstance(v, ObjectId):
            return str(v)
        return v

    @field_serializer("id")
    def serialize_id(self, value: Any, _info):
        if value is None:
            return None
        return str(value)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class BudgetTransaction(BaseModel):
    """Budget transaction domain entity."""
    id: Optional[str] = Field(alias="_id", default=None)
    transaction_number: str
    budget_id: str

    # Transaction Details
    amount: float
    currency: str = "VND"
    transaction_date: datetime
    description: str
    category: str  # "labor" | "materials" | "equipment" | "contractors" | "other"

    # Linked Records
    maintenance_record_id: Optional[str] = None
    asset_id: Optional[str] = None

    # Vendor/Contractor
    vendor_name: Optional[str] = None
    vendor_id: Optional[str] = None
    invoice_number: Optional[str] = None

    # Approval
    status: str = "pending"  # "pending" | "approved" | "rejected" | "paid"
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    # Payment
    payment_date: Optional[datetime] = None
    payment_method: Optional[str] = None  # "cash" | "transfer" | "check"
    payment_reference: Optional[str] = None

    # Tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

    # Metadata
    notes: Optional[str] = None
    attachments: List[BudgetAttachment] = Field(default_factory=list)

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, v: Any):
        """Convert ObjectId to string."""
        if isinstance(v, ObjectId):
            return str(v)
        return v

    @field_serializer("id")
    def serialize_id(self, value: Any, _info):
        if value is None:
            return None
        return str(value)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class BudgetCreate(BaseModel):
    """Budget creation schema."""
    fiscal_year: int
    period_type: BudgetPeriodType
    start_date: datetime
    end_date: datetime
    name: str
    description: Optional[str] = None
    category: BudgetCategory
    total_allocated: float
    departments: List[DepartmentAllocation] = Field(default_factory=list)
    breakdown: List[BudgetBreakdown] = Field(default_factory=list)
    asset_allocations: List[AssetAllocation] = Field(default_factory=list)
    currency: str = "VND"
    notes: Optional[str] = None


class BudgetUpdate(BaseModel):
    """Budget update schema."""
    name: Optional[str] = None
    description: Optional[str] = None
    total_allocated: Optional[float] = None
    departments: Optional[List[DepartmentAllocation]] = None
    breakdown: Optional[List[BudgetBreakdown]] = None
    notes: Optional[str] = None


class BudgetTransactionCreate(BaseModel):
    """Budget transaction creation schema."""
    budget_id: str
    amount: float
    currency: str = "VND"
    transaction_date: datetime
    description: str
    category: str
    maintenance_record_id: Optional[str] = None
    asset_id: Optional[str] = None
    vendor_name: Optional[str] = None
    invoice_number: Optional[str] = None
    notes: Optional[str] = None
