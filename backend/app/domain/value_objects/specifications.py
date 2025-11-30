"""Asset specifications value object."""
from pydantic import BaseModel
from typing import Optional
from datetime import date


class AssetSpecifications(BaseModel):
    """Asset specifications value object."""
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    installation_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    capacity: Optional[str] = None  # e.g., "500kW", "100L"
    dimensions: Optional[str] = None  # e.g., "2m x 3m x 1.5m"
    weight: Optional[str] = None
    material: Optional[str] = None
    custom_fields: dict = {}
