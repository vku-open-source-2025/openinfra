"""Location value object."""
from pydantic import BaseModel
from typing import Optional


class Location(BaseModel):
    """Location value object."""
    address: str
    ward: Optional[str] = None  # Phường/Xã
    district: Optional[str] = None  # Quận/Huyện
    city: Optional[str] = None  # Thành phố
    country: str = "Vietnam"
