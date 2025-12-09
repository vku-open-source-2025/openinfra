"""
SOSA (Sensor, Observation, Sample, and Actuator) Metadata Models.

This module provides semantic metadata models following W3C SOSA ontology.
It creates a "Device Registry" layer on top of raw sensor data for semantic interoperability.

SOSA Ontology: https://www.w3.org/TR/vocab-ssn/
SSN Ontology: https://www.w3.org/TR/vocab-ssn/

Key Concepts:
- sosa:Sensor - A device that observes a property
- sosa:observes - The property being observed (e.g., Temperature)
- sosa:hasFeatureOfInterest - The feature being observed (e.g., Server Room)
- sosa:madeObservation - Link to observations
- sosa:Platform - The entity hosting sensors

This follows the Hybrid Store pattern:
- MongoDB stores raw measurements (high-performance time-series)
- sensors_metadata stores semantic descriptions (SOSA-compliant)
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SOSAType(str, Enum):
    """SOSA entity types."""
    SENSOR = "sosa:Sensor"
    ACTUATOR = "sosa:Actuator"
    SAMPLER = "sosa:Sampler"
    PLATFORM = "sosa:Platform"


class ObservableProperty(str, Enum):
    """Observable properties with SOSA URIs."""
    TEMPERATURE = "http://openinfra.space/properties/Temperature"
    HUMIDITY = "http://openinfra.space/properties/Humidity"
    PRESSURE = "http://openinfra.space/properties/Pressure"
    WATER_LEVEL = "http://openinfra.space/properties/WaterLevel"
    FLOW_RATE = "http://openinfra.space/properties/FlowRate"
    AIR_QUALITY = "http://openinfra.space/properties/AirQuality"
    VIBRATION = "http://openinfra.space/properties/Vibration"
    POWER = "http://openinfra.space/properties/Power"
    VOLTAGE = "http://openinfra.space/properties/Voltage"
    CURRENT = "http://openinfra.space/properties/Current"
    CUSTOM = "http://openinfra.space/properties/Custom"


class MeasurementUnit(BaseModel):
    """Measurement unit specification following QUDT ontology."""
    symbol: str  # "°C", "cm", "L/s"
    qudt_uri: Optional[str] = None  # "http://qudt.org/vocab/unit/DEG_C"
    label: str  # "Degree Celsius"


class FeatureOfInterest(BaseModel):
    """
    SOSA Feature of Interest - the entity being observed.
    
    In infrastructure context:
    - A drainage point
    - A power station
    - A road segment
    - A building
    """
    id: str  # Asset ID or location ID
    type: str = "sosa:FeatureOfInterest"
    name: str  # "Điểm thoát nước số 5, Đường Nguyễn Huệ"
    description: Optional[str] = None
    location: Optional[Dict[str, Any]] = None  # GeoJSON geometry
    properties: Dict[str, Any] = Field(default_factory=dict)


class Platform(BaseModel):
    """
    SOSA Platform - entity hosting one or more sensors.
    
    Examples:
    - A weather station hosting temperature, humidity, pressure sensors
    - A drainage monitoring box hosting water level and flow rate sensors
    - A smart pole hosting camera, light sensor, air quality sensor
    """
    id: str
    type: str = "sosa:Platform"
    name: str
    description: Optional[str] = None
    location: Optional[Dict[str, Any]] = None  # GeoJSON geometry
    hosted_sensors: List[str] = Field(default_factory=list)  # sensor_ids


class ObservationConfig(BaseModel):
    """
    Configuration for how observations are made.
    Maps to sosa:madeObservation metadata.
    """
    unit: MeasurementUnit
    result_type: str = "xsd:float"  # Data type of observation result
    sampling_interval: Optional[int] = None  # seconds
    accuracy: Optional[float] = None
    precision: Optional[float] = None


class SensorMetadata(BaseModel):
    """
    SOSA-compliant Sensor Metadata.
    
    This is the "Device Registry" entry that provides semantic context
    for raw sensor readings stored in sensor_readings collection.
    
    The _id field matches the sensor_id in iot_sensors collection.
    """
    id: str = Field(alias="_id")  # Same as sensor_id in iot_sensors
    type: SOSAType = SOSAType.SENSOR
    
    # Human-readable label
    label: str  # "Cảm biến mực nước - Cống thoát nước số 5"
    description: Optional[str] = None
    
    # SOSA Core Properties
    observes: ObservableProperty  # What property does this sensor measure?
    has_feature_of_interest: FeatureOfInterest  # What is being observed?
    is_hosted_by: Optional[str] = None  # Platform ID
    
    # Observation configuration
    observation_config: ObservationConfig
    
    # SSN Extensions
    implements_procedure: Optional[str] = None  # URI of measurement procedure
    has_deployment: Optional[str] = None  # Deployment context
    
    # Additional semantic annotations
    same_as: List[str] = Field(default_factory=list)  # owl:sameAs links
    see_also: List[str] = Field(default_factory=list)  # rdfs:seeAlso links
    
    # Provenance
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    
    # Custom properties (for domain-specific extensions)
    custom_properties: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True


class SensorMetadataCreate(BaseModel):
    """Schema for creating sensor metadata."""
    sensor_id: str  # Links to iot_sensors._id
    label: str
    description: Optional[str] = None
    observes: ObservableProperty
    feature_of_interest_id: str  # Asset ID
    feature_of_interest_name: str
    feature_of_interest_description: Optional[str] = None
    unit_symbol: str
    unit_label: str
    qudt_uri: Optional[str] = None
    sampling_interval: Optional[int] = None
    is_hosted_by: Optional[str] = None
    custom_properties: Dict[str, Any] = Field(default_factory=dict)


class SensorMetadataUpdate(BaseModel):
    """Schema for updating sensor metadata."""
    label: Optional[str] = None
    description: Optional[str] = None
    observes: Optional[ObservableProperty] = None
    feature_of_interest_name: Optional[str] = None
    unit_symbol: Optional[str] = None
    unit_label: Optional[str] = None
    is_hosted_by: Optional[str] = None
    custom_properties: Optional[Dict[str, Any]] = None


# JSON-LD Context for SOSA
SOSA_JSONLD_CONTEXT = {
    "@context": {
        "sosa": "http://www.w3.org/ns/sosa/",
        "ssn": "http://www.w3.org/ns/ssn/",
        "qudt": "http://qudt.org/schema/qudt/",
        "schema": "https://schema.org/",
        "geo": "http://www.w3.org/2003/01/geo/wgs84_pos#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "owl": "http://www.w3.org/2002/07/owl#",
        "dcterms": "http://purl.org/dc/terms/",
        
        # SOSA Core mappings
        "Sensor": "sosa:Sensor",
        "Observation": "sosa:Observation",
        "Platform": "sosa:Platform",
        "FeatureOfInterest": "sosa:FeatureOfInterest",
        "ObservableProperty": "sosa:ObservableProperty",
        
        # SOSA Properties
        "observes": {"@id": "sosa:observes", "@type": "@id"},
        "hasFeatureOfInterest": {"@id": "sosa:hasFeatureOfInterest", "@type": "@id"},
        "isHostedBy": {"@id": "sosa:isHostedBy", "@type": "@id"},
        "madeObservation": {"@id": "sosa:madeObservation", "@type": "@id"},
        "madeBySensor": {"@id": "sosa:madeBySensor", "@type": "@id"},
        "hasResult": "sosa:hasResult",
        "hasSimpleResult": "sosa:hasSimpleResult",
        "resultTime": {"@id": "sosa:resultTime", "@type": "xsd:dateTime"},
        
        # SSN Extensions
        "implementsProcedure": {"@id": "ssn:implementsProcedure", "@type": "@id"},
        "hasDeployment": {"@id": "ssn:hasDeployment", "@type": "@id"},
        
        # Schema.org
        "name": "schema:name",
        "description": "schema:description",
        "identifier": "schema:identifier",
        "dateCreated": {"@id": "schema:dateCreated", "@type": "xsd:dateTime"},
        "dateModified": {"@id": "schema:dateModified", "@type": "xsd:dateTime"},
        
        # Measurement
        "unit": "qudt:unit",
        "unitSymbol": "qudt:symbol",
        "value": "qudt:value",
        
        # Links
        "sameAs": {"@id": "owl:sameAs", "@type": "@id"},
        "seeAlso": {"@id": "rdfs:seeAlso", "@type": "@id"},
        
        # License (OGL)
        "license": {"@id": "dcterms:license", "@type": "@id"},
        "rights": "dcterms:rights",
        "publisher": "dcterms:publisher"
    }
}


def sensor_type_to_observable_property(sensor_type: str) -> ObservableProperty:
    """Map IoT sensor type to SOSA ObservableProperty."""
    mapping = {
        "temperature": ObservableProperty.TEMPERATURE,
        "humidity": ObservableProperty.HUMIDITY,
        "pressure": ObservableProperty.PRESSURE,
        "water_level": ObservableProperty.WATER_LEVEL,
        "flow_rate": ObservableProperty.FLOW_RATE,
        "air_quality": ObservableProperty.AIR_QUALITY,
        "vibration": ObservableProperty.VIBRATION,
        "power": ObservableProperty.POWER,
        "voltage": ObservableProperty.VOLTAGE,
        "current": ObservableProperty.CURRENT,
    }
    return mapping.get(sensor_type.lower(), ObservableProperty.CUSTOM)


def unit_to_qudt_uri(unit: str) -> Optional[str]:
    """Map unit symbol to QUDT URI."""
    mapping = {
        "°C": "http://qudt.org/vocab/unit/DEG_C",
        "°F": "http://qudt.org/vocab/unit/DEG_F",
        "%": "http://qudt.org/vocab/unit/PERCENT",
        "kPa": "http://qudt.org/vocab/unit/KiloPA",
        "Pa": "http://qudt.org/vocab/unit/PA",
        "cm": "http://qudt.org/vocab/unit/CentiM",
        "m": "http://qudt.org/vocab/unit/M",
        "L/s": "http://qudt.org/vocab/unit/L-PER-SEC",
        "m³/s": "http://qudt.org/vocab/unit/M3-PER-SEC",
        "Hz": "http://qudt.org/vocab/unit/HZ",
        "kW": "http://qudt.org/vocab/unit/KiloW",
        "W": "http://qudt.org/vocab/unit/W",
        "V": "http://qudt.org/vocab/unit/V",
        "A": "http://qudt.org/vocab/unit/A",
        "ppm": "http://qudt.org/vocab/unit/PPM",
    }
    return mapping.get(unit)


def unit_to_label(unit: str) -> str:
    """Get human-readable label for unit."""
    mapping = {
        "°C": "Degree Celsius",
        "°F": "Degree Fahrenheit",
        "%": "Percent",
        "kPa": "Kilopascal",
        "Pa": "Pascal",
        "cm": "Centimeter",
        "m": "Meter",
        "L/s": "Liters per Second",
        "m³/s": "Cubic Meters per Second",
        "Hz": "Hertz",
        "kW": "Kilowatt",
        "W": "Watt",
        "V": "Volt",
        "A": "Ampere",
        "ppm": "Parts per Million",
    }
    return mapping.get(unit, unit)
