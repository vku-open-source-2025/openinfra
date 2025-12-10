"""
NGSI-LD API Router for IoT Sensor Data with SOSA Semantic Metadata.

This module provides NGSI-LD endpoints following ETSI NGSI-LD standard
with W3C SOSA (Sensor, Observation, Sample, Actuator) ontology integration.

Standards implemented:
- NGSI-LD Core Context (JSON-LD based) - ETSI standard
- SOSA/SSN Ontology - W3C recommendation for sensor semantics
- Schema.org vocabulary - General-purpose
- QUDT - Units of measurement

Architecture (Hybrid Store Pattern):
- MongoDB stores raw measurements (high-performance time-series)
- sensors_metadata stores SOSA semantic descriptions
- API combines both for full semantic interoperability

API Documentation: https://api.openinfra.space/docs (see NGSI-LD section)
"""

from fastapi import APIRouter, Query, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime, timedelta
from app.domain.services.iot_service import IoTService
from app.api.v1.dependencies import get_iot_service
from app.domain.models.sosa_metadata import (
    SOSA_JSONLD_CONTEXT,
    sensor_type_to_observable_property,
    unit_to_qudt_uri,
    unit_to_label,
)

router = APIRouter()

# NGSI-LD + SOSA Combined Context for sensor data
NGSI_LD_CONTEXT = [
    "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
    {
        # Standard vocabularies
        "schema": "https://schema.org/",
        "geo": "http://www.w3.org/2003/01/geo/wgs84_pos#",
        "dcterms": "http://purl.org/dc/terms/",
        
        # SOSA/SSN Ontology (W3C)
        "sosa": "http://www.w3.org/ns/sosa/",
        "ssn": "http://www.w3.org/ns/ssn/",
        "qudt": "http://qudt.org/schema/qudt/",
        
        # SOSA Core Classes
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
        
        # OpenInfra specific terms (backward compatible)
        "sensorCode": "schema:identifier",
        "sensorType": "schema:additionalType",
        "manufacturer": "schema:manufacturer",
        "model": "schema:model",
        "measurementUnit": "qudt:unit",
        "sampleRate": "schema:frequency",
        "assetId": "schema:identifier",
        "featureType": "schema:category",
        "featureCode": "schema:propertyID",
        "quality": "schema:quality",
        
        # Unit measurement
        "unit": "qudt:unit",
        "unitSymbol": "qudt:symbol",
        
        # License
        "license": {"@id": "dcterms:license", "@type": "@id"},
        "rights": "dcterms:rights",
        "publisher": "dcterms:publisher"
    }
]

# OGL License info
LICENSE_INFO = {
    "license": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
    "rights": "Open Government Licence (OGL)",
    "publisher": {
        "@type": "schema:Organization",
        "schema:name": "VKU.OneLove - OpenInfra",
        "schema:url": "https://openinfra.space",
    },
}


def create_sensor_ngsi_ld(sensor, base_url: str = "https://openinfra.space", metadata: dict = None) -> dict:
    """
    Convert sensor to NGSI-LD format with SOSA semantics.
    
    If metadata is provided (from sensors_metadata collection), 
    includes full SOSA semantic description.
    """
    sensor_id = str(sensor.id) if sensor.id else sensor.sensor_code
    sensor_type_value = sensor.sensor_type.value if hasattr(sensor.sensor_type, "value") else sensor.sensor_type
    
    # Map sensor type to SOSA ObservableProperty
    observable_property = sensor_type_to_observable_property(sensor_type_value)
    
    entity = {
        "id": f"urn:ngsi-ld:Sensor:{sensor_id}",
        "type": "Sensor",  # Maps to sosa:Sensor via context
        "sensorCode": {
            "type": "Property",
            "value": sensor.sensor_code
        },
        "sensorType": {
            "type": "Property",
            "value": sensor_type_value
        },
        "status": {
            "type": "Property",
            "value": sensor.status.value if hasattr(sensor.status, "value") else sensor.status
        },
        # SOSA: observes - what property is being measured
        "observes": {
            "type": "Relationship",
            "object": observable_property.value if hasattr(observable_property, "value") else observable_property
        },
        # SOSA: hasFeatureOfInterest - link to the asset
        "hasFeatureOfInterest": {
            "type": "Relationship",
            "object": f"urn:ngsi-ld:Asset:{sensor.asset_id}"
        },
        # Legacy compatibility
        "refAsset": {
            "type": "Relationship",
            "object": f"urn:ngsi-ld:Asset:{sensor.asset_id}"
        }
    }
    
    if sensor.manufacturer:
        entity["manufacturer"] = {"type": "Property", "value": sensor.manufacturer}
    if sensor.model:
        entity["model"] = {"type": "Property", "value": sensor.model}
    if sensor.measurement_unit:
        qudt_uri = unit_to_qudt_uri(sensor.measurement_unit)
        entity["measurementUnit"] = {
            "type": "Property", 
            "value": sensor.measurement_unit,
            "unitCode": qudt_uri if qudt_uri else sensor.measurement_unit
        }
    if sensor.sample_rate:
        entity["sampleRate"] = {"type": "Property", "value": sensor.sample_rate}
    if sensor.last_seen:
        entity["dateObserved"] = {
            "type": "Property",
            "value": {"@type": "DateTime", "@value": sensor.last_seen.isoformat()}
        }
    
    # Add SOSA metadata if available
    if metadata:
        if metadata.get("label"):
            entity["name"] = {"type": "Property", "value": metadata["label"]}
        if metadata.get("description"):
            entity["description"] = {"type": "Property", "value": metadata["description"]}
        if metadata.get("is_hosted_by"):
            entity["isHostedBy"] = {
                "type": "Relationship",
                "object": f"urn:ngsi-ld:Platform:{metadata['is_hosted_by']}"
            }
    
    return entity


def create_observation_ngsi_ld(
    reading, sensor_info: dict = None, base_url: str = "https://openinfra.space"
) -> dict:
    """
    Convert sensor reading to NGSI-LD Observation following SOSA ontology.
    
    SOSA Observation structure:
    - sosa:madeBySensor - link to the sensor
    - sosa:hasFeatureOfInterest - what was observed
    - sosa:observedProperty - what property was measured
    - sosa:hasSimpleResult - the measured value
    - sosa:resultTime - when the observation was made
    """
    reading_id = (
        str(reading.id)
        if reading.id
        else f"{reading.sensor_id}-{int(reading.timestamp.timestamp())}"
    )
    
    timestamp_str = reading.timestamp.isoformat()
    if not timestamp_str.endswith('Z'):
        timestamp_str += "Z"
    
    # Get unit info for QUDT mapping
    unit = reading.unit if hasattr(reading, 'unit') else None
    qudt_uri = unit_to_qudt_uri(unit) if unit else None
    
    entity = {
        "id": f"urn:ngsi-ld:Observation:{reading_id}",
        "type": "Observation",  # Maps to sosa:Observation via context
        
        # SOSA: resultTime - when the observation was made
        "resultTime": {
            "type": "Property",
            "value": timestamp_str
        },
        "observedAt": timestamp_str,
        
        # SOSA: hasSimpleResult - the measured value
        "hasSimpleResult": {
            "type": "Property",
            "value": reading.value
        },
        
        # Full result with unit (QUDT)
        "hasResult": {
            "type": "Property",
            "value": {
                "numericValue": reading.value,
                "unit": qudt_uri if qudt_uri else unit,
                "unitSymbol": unit
            }
        },
        
        # Legacy format (backward compatible)
        "value": {
            "type": "Property",
            "value": reading.value,
            "unitCode": unit,
            "observedAt": timestamp_str
        },
        
        # SOSA: madeBySensor - link to sensor
        "madeBySensor": {
            "type": "Relationship",
            "object": f"urn:ngsi-ld:Sensor:{reading.sensor_id}"
        },
        
        # SOSA: hasFeatureOfInterest - link to asset
        "hasFeatureOfInterest": {
            "type": "Relationship",
            "object": f"urn:ngsi-ld:Asset:{reading.asset_id}"
        },
        
        # Legacy (backward compatible)
        "refSensor": {
            "type": "Relationship",
            "object": f"urn:ngsi-ld:Sensor:{reading.sensor_id}"
        },
        "refAsset": {
            "type": "Relationship",
            "object": f"urn:ngsi-ld:Asset:{reading.asset_id}"
        }
    }
    
    if reading.quality:
        entity["quality"] = {
            "type": "Property",
            "value": reading.quality
        }
    
    # SOSA: observedProperty - what was measured
    if sensor_info and sensor_info.get("sensor_type"):
        observable_property = sensor_type_to_observable_property(sensor_info["sensor_type"])
        entity["observedProperty"] = {
            "type": "Relationship",
            "object": observable_property.value if hasattr(observable_property, "value") else observable_property
        }
    
    return entity


@router.get(
    "/context",
    summary="Get NGSI-LD Context",
    description="""
    Returns the NGSI-LD context document defining the vocabulary mappings.

    This context follows ETSI NGSI-LD standard:
    - **NGSI-LD Core**: Base context for entity types, properties, and relationships
    - **Schema.org**: General-purpose vocabulary for additional properties
    - **GeoSPARQL/WGS84**: Geographic coordinates

    Use this context with `@context` in NGSI-LD documents for semantic interoperability.
    """,
    tags=["NGSI-LD"],
    responses={
        200: {
            "description": "NGSI-LD Context document",
            "content": {"application/ld+json": {"example": NGSI_LD_CONTEXT}},
        }
    },
)
async def get_context():
    """Return the NGSI-LD context for sensor data."""
    return JSONResponse(content={"@context": NGSI_LD_CONTEXT}, media_type="application/ld+json")


@router.get(
    "/sosa/context",
    summary="Get SOSA/SSN Context",
    description="""
    Returns the W3C SOSA (Sensor, Observation, Sample, Actuator) context document.

    This context provides semantic vocabulary for:
    - **sosa:Sensor** - IoT sensor devices
    - **sosa:Observation** - Sensor readings/measurements
    - **sosa:Platform** - Entity hosting sensors
    - **sosa:FeatureOfInterest** - The thing being observed (e.g., asset)
    - **sosa:ObservableProperty** - What property is being measured

    SOSA is a W3C recommendation for describing sensors and observations
    with proper semantic meaning for machine interoperability.

    Reference: https://www.w3.org/TR/vocab-ssn/
    """,
    tags=["SOSA"],
    responses={
        200: {
            "description": "SOSA Context document",
            "content": {"application/ld+json": {}},
        }
    },
)
async def get_sosa_context():
    """Return the SOSA/SSN context for semantic sensor data."""
    return JSONResponse(content=SOSA_JSONLD_CONTEXT, media_type="application/ld+json")


@router.get(
    "/sosa/observable-properties",
    summary="List Observable Properties",
    description="""
    Returns the list of observable properties supported by OpenInfra.

    Each property follows SOSA ontology pattern:
    - URI identifier for the property
    - Human-readable label
    - Common units of measurement

    Use these URIs in `sosa:observes` relationships.
    """,
    tags=["SOSA"],
)
async def list_observable_properties():
    """List all supported observable properties."""
    from app.domain.models.sosa_metadata import ObservableProperty, unit_to_qudt_uri
    
    properties = []
    property_info = {
        "Temperature": {"units": ["°C", "°F"], "description": "Temperature measurement"},
        "Humidity": {"units": ["%"], "description": "Relative humidity"},
        "Pressure": {"units": ["kPa", "Pa"], "description": "Atmospheric or fluid pressure"},
        "WaterLevel": {"units": ["cm", "m"], "description": "Water level in drainage/tanks"},
        "FlowRate": {"units": ["L/s", "m³/s"], "description": "Fluid flow rate"},
        "AirQuality": {"units": ["ppm"], "description": "Air quality index"},
        "Vibration": {"units": ["Hz"], "description": "Vibration frequency"},
        "Power": {"units": ["kW", "W"], "description": "Electrical power"},
        "Voltage": {"units": ["V"], "description": "Electrical voltage"},
        "Current": {"units": ["A"], "description": "Electrical current"},
    }
    
    for prop in ObservableProperty:
        prop_name = prop.name.replace("_", "")
        info = property_info.get(prop_name.title().replace("_", ""), {})
        
        properties.append({
            "@id": prop.value,
            "@type": "sosa:ObservableProperty",
            "label": prop_name.replace("_", " ").title(),
            "description": info.get("description", ""),
            "commonUnits": [
                {"symbol": u, "qudt": unit_to_qudt_uri(u)} 
                for u in info.get("units", [])
            ]
        })
    
    return JSONResponse(
        content={
            "@context": SOSA_JSONLD_CONTEXT["@context"],
            "@type": "schema:ItemList",
            "schema:numberOfItems": len(properties),
            "schema:itemListElement": properties
        },
        media_type="application/ld+json"
    )


@router.get(
    "/sensors",
    summary="List Sensors as NGSI-LD",
    description="""
    Returns a list of IoT sensors in NGSI-LD format following the ETSI NGSI-LD standard.

    Each sensor is represented as an NGSI-LD entity with:
    - Unique `id` URI (urn:ngsi-ld:Sensor:xxx)
    - `type`: Sensor
    - Properties with `{"type": "Property", "value": ...}` structure
    - Relationships with `{"type": "Relationship", "object": ...}` structure
    - `refAsset`: Relationship to the monitored asset

    **Pagination**: Use `skip` and `limit` parameters.
    **Filtering**: Filter by `asset_id`, `sensor_type`, or `status`.

    The response follows NGSI-LD specification for interoperability.
    """,
    tags=["NGSI-LD"],
    responses={
        200: {
            "description": "Collection of sensors in JSON-LD format",
            "content": {
                "application/ld+json": {
                    "example": {
                        "@context": "https://openinfra.space/api/v1/ld/context",
                        "@type": "schema:ItemList",
                        "schema:numberOfItems": 2,
                        "schema:itemListElement": [
                            {
                                "@id": "https://openinfra.space/api/v1/ld/sensors/sensor-001",
                                "@type": "Sensor",
                                "sensorCode": "TEMP-001",
                                "sensorType": "temperature",
                                "measurementUnit": "°C",
                            }
                        ],
                    }
                }
            },
        }
    },
)
async def list_sensors_ngsi_ld(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=500, description="Maximum number of records to return"
    ),
    asset_id: Optional[str] = Query(None, description="Filter by asset ID"),
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    status: Optional[str] = Query(None, description="Filter by sensor status"),
    iot_service: IoTService = Depends(get_iot_service),
):
    """List all sensors in NGSI-LD format."""
    sensors = await iot_service.list_sensors(skip, limit, asset_id, sensor_type, status)

    sensors_ld = [create_sensor_ngsi_ld(sensor) for sensor in sensors]

    result = [
        {
            "@context": NGSI_LD_CONTEXT,
            **LICENSE_INFO,
            **sensor
        }
        for sensor in sensors_ld
    ]

    return JSONResponse(content=result, media_type="application/ld+json")


@router.get(
    "/sensors/{sensor_id}",
    summary="Get Sensor as NGSI-LD",
    description="""
    Returns a single IoT sensor in NGSI-LD format.

    The sensor is represented as an NGSI-LD entity following the ETSI NGSI-LD standard.

    **Related endpoints**:
    - `/ld/sensors/{sensor_id}/observations` - Get observations from this sensor
    - `/ld/assets/{asset_id}` - Get the monitored asset
    """,
    tags=["NGSI-LD"],
    responses={
        200: {
            "description": "Sensor in NGSI-LD format",
            "content": {"application/ld+json": {}},
        },
        404: {"description": "Sensor not found"},
    },
)
async def get_sensor_ngsi_ld(
    sensor_id: str, iot_service: IoTService = Depends(get_iot_service)
):
    """Get single sensor in NGSI-LD format."""
    sensor = await iot_service.get_sensor_by_id(sensor_id)

    result = {"@context": NGSI_LD_CONTEXT, **LICENSE_INFO, **create_sensor_ngsi_ld(sensor)}

    return JSONResponse(content=result, media_type="application/ld+json")


@router.get(
    "/sensors/{sensor_id}/observations",
    summary="Get Sensor Observations as NGSI-LD",
    description="""
    Returns observations (readings) from a specific sensor in NGSI-LD format.

    Each observation is an NGSI-LD entity with:
    - `type`: Observation
    - `observedAt`: When the observation was made
    - `value`: Property with measured value, unitCode, and observedAt
    - `refAsset`: Relationship to the monitored asset
    - `refSensor`: Relationship to the sensor
    - `observedProperty`: What property was measured

    **Time range**: Specify `from_time` and `to_time` in ISO 8601 format.
    **Pagination**: Use `limit` to control the number of results.

    Example time format: `2024-01-01T00:00:00Z`
    """,
    tags=["NGSI-LD"],
    responses={
        200: {
            "description": "Collection of observations in JSON-LD format",
            "content": {
                "application/ld+json": {
                    "example": {
                        "@context": "https://openinfra.space/api/v1/ld/context",
                        "@type": "schema:ItemList",
                        "schema:itemListElement": [
                            {
                                "@type": "Observation",
                                "resultTime": "2024-01-15T10:30:00Z",
                                "hasResult": {
                                    "value": 25.5,
                                    "unit": "°C",
                                    "quality": "good",
                                },
                            }
                        ],
                    }
                }
            },
        }
    },
)
async def get_sensor_observations_ngsi_ld(
    sensor_id: str,
    from_time: str = Query(
        ..., description="Start time in ISO 8601 format (e.g., 2024-01-01T00:00:00Z)"
    ),
    to_time: str = Query(
        ..., description="End time in ISO 8601 format (e.g., 2024-01-31T23:59:59Z)"
    ),
    limit: int = Query(
        1000, ge=1, le=10000, description="Maximum number of observations"
    ),
    iot_service: IoTService = Depends(get_iot_service),
):
    """Get sensor observations in NGSI-LD format."""
    from_time_dt = datetime.fromisoformat(from_time.replace("Z", "+00:00"))
    to_time_dt = datetime.fromisoformat(to_time.replace("Z", "+00:00"))

    # Get sensor info for context
    sensor = await iot_service.get_sensor_by_id(sensor_id)
    sensor_info = {
        "sensor_type": (
            sensor.sensor_type.value
            if hasattr(sensor.sensor_type, "value")
            else sensor.sensor_type
        )
    }

    readings = await iot_service.get_sensor_readings(
        sensor_id, from_time_dt, to_time_dt, limit
    )

    observations_ld = [
        create_observation_ngsi_ld(reading, sensor_info) for reading in readings
    ]

    result = [
        {
            "@context": NGSI_LD_CONTEXT,
            **LICENSE_INFO,
            **obs
        }
        for obs in observations_ld
    ]

    return JSONResponse(content=result, media_type="application/ld+json")


@router.get(
    "/assets/{asset_id}",
    summary="Get Asset with IoT Data as NGSI-LD",
    description="""
    Returns an infrastructure asset with its associated IoT sensor data in NGSI-LD format.

    The response includes:
    - **Asset metadata**: ID, feature type, feature code
    - **Associated sensors**: List of sensors monitoring this asset
    - **Recent observations**: Latest readings from all sensors
    - **Summary statistics**: Total sensors, readings count

    This endpoint returns NGSI-LD entities with proper Property and Relationship structures.

    **Time range**: Use `hours` parameter to specify how far back to retrieve data (default: 24 hours).
    """,
    tags=["NGSI-LD"],
    responses={
        200: {
            "description": "Asset with IoT data in JSON-LD format",
            "content": {
                "application/ld+json": {
                    "example": {
                        "@context": "https://openinfra.space/api/v1/ld/context",
                        "@type": "FeatureOfInterest",
                        "@id": "https://openinfra.space/api/v1/ld/assets/asset-123",
                        "assetId": "asset-123",
                        "featureType": "Trạm điện",
                        "isFeatureOfInterestOf": [
                            {"@type": "Sensor", "sensorCode": "TEMP-001"}
                        ],
                    }
                }
            },
        }
    },
)
async def get_asset_ngsi_ld(
    asset_id: str,
    hours: int = Query(
        24, ge=1, le=168, description="Number of hours of historical data to include"
    ),
    iot_service: IoTService = Depends(get_iot_service),
):
    """Get asset with IoT data in NGSI-LD format."""
    from_time = datetime.utcnow() - timedelta(hours=hours)
    to_time = datetime.utcnow()

    # Get sensors for this asset
    sensors = await iot_service.list_sensors(0, 100, asset_id=asset_id)

    sensors_ld = [create_sensor_ngsi_ld(sensor) for sensor in sensors]

    # Get recent readings
    all_observations = []
    for sensor in sensors:
        try:
            readings = await iot_service.get_sensor_readings(
                str(sensor.id), from_time, to_time, limit=100
            )
            sensor_info = {
                "sensor_type": (
                    sensor.sensor_type.value
                    if hasattr(sensor.sensor_type, "value")
                    else sensor.sensor_type
                )
            }
            for reading in readings:
                all_observations.append(create_observation_ngsi_ld(reading, sensor_info))
        except Exception:
            pass

    # Sort by time descending
    all_observations.sort(key=lambda x: x.get("observedAt", ""), reverse=True)

    # Get asset info from first sensor if available
    feature_type = sensors[0].sensor_type.value if sensors else "Unknown"

    result = {
        "@context": NGSI_LD_CONTEXT,
        **LICENSE_INFO,
        "id": f"urn:ngsi-ld:Asset:{asset_id}",
        "type": "Asset",
        "assetId": {
            "type": "Property",
            "value": asset_id
        },
        "featureType": {
            "type": "Property",
            "value": feature_type
        },
        "associatedSensors": {
            "type": "Property",
            "value": sensors_ld[:10]  # Limit sensors
        },
        "recentObservations": {
            "type": "Property",
            "value": all_observations[:50]  # Limit observations
        },
        "summary": {
            "type": "Property",
            "value": {
                "totalSensors": len(sensors),
                "totalObservations": len(all_observations),
                "timeRangeHours": hours
            }
        }
    }

    return JSONResponse(content=result, media_type="application/ld+json")


@router.get(
    "/observations",
    summary="List All Observations as NGSI-LD",
    description="""
    Returns recent observations from all sensors in NGSI-LD format.

    This is useful for:
    - Building a complete observation dataset
    - Integrating with NGSI-LD context brokers
    - Smart city data platforms

    **Filtering**:
    - `asset_id`: Filter by specific asset
    - `sensor_type`: Filter by sensor type (temperature, humidity, etc.)

    **Time range**: Use `hours` to specify how far back to retrieve (default: 1 hour).
    """,
    tags=["NGSI-LD"],
    responses={
        200: {
            "description": "Collection of observations in JSON-LD format",
            "content": {"application/ld+json": {}},
        }
    },
)
async def list_observations_ngsi_ld(
    hours: int = Query(
        1, ge=1, le=24, description="Number of hours of data to retrieve"
    ),
    asset_id: Optional[str] = Query(None, description="Filter by asset ID"),
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    limit: int = Query(
        500, ge=1, le=5000, description="Maximum observations to return"
    ),
    iot_service: IoTService = Depends(get_iot_service),
):
    """List all recent observations in NGSI-LD format."""
    from_time = datetime.utcnow() - timedelta(hours=hours)
    to_time = datetime.utcnow()

    # Get sensors
    sensors = await iot_service.list_sensors(
        0, 500, asset_id=asset_id, sensor_type=sensor_type
    )

    all_observations = []
    for sensor in sensors:
        try:
            readings = await iot_service.get_sensor_readings(
                str(sensor.id), from_time, to_time, limit=limit // max(len(sensors), 1)
            )
            sensor_info = {
                "sensor_type": (
                    sensor.sensor_type.value
                    if hasattr(sensor.sensor_type, "value")
                    else sensor.sensor_type
                )
            }
            for reading in readings:
                all_observations.append(create_observation_ngsi_ld(reading, sensor_info))
        except Exception:
            pass

    # Sort by time descending and limit
    all_observations.sort(key=lambda x: x.get("observedAt", ""), reverse=True)
    all_observations = all_observations[:limit]

    result = [
        {
            "@context": NGSI_LD_CONTEXT,
            **LICENSE_INFO,
            **obs
        }
        for obs in all_observations
    ]

    return JSONResponse(content=result, media_type="application/ld+json")


@router.get(
    "/vocab",
    summary="Get OpenInfra Vocabulary",
    description="""
    Returns the OpenInfra vocabulary definition in NGSI-LD/JSON-LD format.

    This vocabulary extends NGSI-LD and Schema.org with
    OpenInfra-specific terms for infrastructure management.

    Use this for understanding the semantic meaning of properties in the API responses.
    """,
    tags=["NGSI-LD"],
)
async def get_vocabulary():
    """Return the OpenInfra vocabulary."""
    vocab = {
        "@context": {
            "@vocab": "https://openinfra.space/vocab#",
            "ngsi-ld": "https://uri.etsi.org/ngsi-ld/",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "owl": "http://www.w3.org/2002/07/owl#",
        },
        "@graph": [
            {
                "@id": "https://openinfra.space/vocab#InfrastructureAsset",
                "@type": "owl:Class",
                "rdfs:label": "Infrastructure Asset",
                "rdfs:comment": "A physical infrastructure asset being monitored",
                "rdfs:subClassOf": "ngsi-ld:Entity",
            },
            {
                "@id": "https://openinfra.space/vocab#Sensor",
                "@type": "owl:Class",
                "rdfs:label": "IoT Sensor",
                "rdfs:comment": "An IoT sensor device monitoring infrastructure",
                "rdfs:subClassOf": "ngsi-ld:Entity",
            },
            {
                "@id": "https://openinfra.space/vocab#Observation",
                "@type": "owl:Class",
                "rdfs:label": "Sensor Observation",
                "rdfs:comment": "A single observation/reading from a sensor",
                "rdfs:subClassOf": "ngsi-ld:Entity",
            },
            {
                "@id": "https://openinfra.space/vocab#sensorCode",
                "@type": "ngsi-ld:Property",
                "rdfs:label": "Sensor Code",
                "rdfs:comment": "Unique identifier code for the sensor device",
                "rdfs:domain": "https://openinfra.space/vocab#Sensor",
                "rdfs:range": "xsd:string",
            },
            {
                "@id": "https://openinfra.space/vocab#refAsset",
                "@type": "ngsi-ld:Relationship",
                "rdfs:label": "Reference to Asset",
                "rdfs:comment": "Relationship pointing to the monitored asset",
                "rdfs:domain": "https://openinfra.space/vocab#Sensor",
                "rdfs:range": "https://openinfra.space/vocab#InfrastructureAsset",
            },
        ],
    }

    return JSONResponse(content=vocab, media_type="application/ld+json")
