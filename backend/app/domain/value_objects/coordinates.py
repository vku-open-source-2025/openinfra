"""Coordinates value object."""
from pydantic import BaseModel, field_validator
from typing import List


class Coordinates(BaseModel):
    """Geographic coordinates value object."""
    longitude: float
    latitude: float

    @field_validator('longitude')
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v

    @field_validator('latitude')
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    def to_geojson(self) -> dict:
        """Convert to GeoJSON Point."""
        return {
            "type": "Point",
            "coordinates": [self.longitude, self.latitude]
        }

    @classmethod
    def from_geojson(cls, geojson: dict) -> 'Coordinates':
        """Create from GeoJSON Point."""
        if geojson.get("type") != "Point":
            raise ValueError("GeoJSON type must be Point")
        coords = geojson.get("coordinates", [])
        if len(coords) < 2:
            raise ValueError("Coordinates must have at least 2 values")
        return cls(longitude=coords[0], latitude=coords[1])
