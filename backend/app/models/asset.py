from pydantic import BaseModel, Field, field_serializer
from typing import Any, Dict, List, Optional
from datetime import datetime
from bson import ObjectId

class AssetBase(BaseModel):
    feature_type: str
    feature_code: str
    geometry: Dict[str, Any]  # GeoJSON format: {"type": "Point", "coordinates": [...]}
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AssetCreate(AssetBase):
    pass

class Asset(AssetBase):
    id: Any = Field(alias="_id")

    @field_serializer('id')
    def serialize_id(self, value: Any, _info):
        return str(value)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "feature_type": "Trạm điện",
                "feature_code": "tram_dien",
                "geometry": {
                    "type": "Point",
                    "coordinates": [108.2544869184494, 15.974846711696628]
                },
                "created_at": "2025-11-22T14:27:29.567Z"
            }
        }
