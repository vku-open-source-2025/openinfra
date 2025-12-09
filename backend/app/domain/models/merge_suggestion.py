"""Merge suggestion domain models."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum
from bson import ObjectId


class MergeSuggestionStatus(str, Enum):
    """Merge suggestion status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class DuplicateMatch(BaseModel):
    """Duplicate match result."""
    incident_id: str
    similarity_score: float
    match_reasons: List[str] = Field(default_factory=list)  # e.g., "same_asset", "similar_description", "nearby_location", "similar_images"


class MergeSuggestion(BaseModel):
    """Merge suggestion model."""
    id: Optional[str] = Field(validation_alias="_id", serialization_alias="id", default=None)
    primary_incident_id: str
    duplicate_incident_ids: List[str]
    similarity_score: float
    match_reasons: List[str] = Field(default_factory=list)
    suggested_by: str  # "system" or user_id
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: MergeSuggestionStatus = MergeSuggestionStatus.PENDING
    approved_by: Optional[str] = None
    rejected_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary."""
        if "_id" in data:
            data["id"] = str(data["_id"])
        return cls(**data)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class MergeRequest(BaseModel):
    """Merge request schema."""
    duplicate_ids: List[str]
    merge_notes: Optional[str] = None

