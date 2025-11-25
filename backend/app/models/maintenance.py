from pydantic import BaseModel, Field, field_serializer
from typing import Any, Optional
from datetime import datetime
from bson import ObjectId

class MaintenanceLogBase(BaseModel):
    asset_id: str
    description: str
    technician: str
    status: str = "Pending" # Pending, In Progress, Completed
    scheduled_date: datetime
    completed_date: Optional[datetime] = None

class MaintenanceLogCreate(MaintenanceLogBase):
    pass

class MaintenanceLog(MaintenanceLogBase):
    id: Any = Field(alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_serializer('id')
    def serialize_id(self, value: Any, _info):
        return str(value)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
