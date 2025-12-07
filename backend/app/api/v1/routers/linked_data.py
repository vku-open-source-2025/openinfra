"""
JSON-LD (Linked Data) API Router for IoT Sensor Data.

This module provides Linked Data endpoints following W3C standards:
- SSN (Semantic Sensor Network) Ontology
- SOSA (Sensor, Observation, Sample, and Actuator) Ontology
- Schema.org vocabulary

API Documentation: https://openinfra.space/docs
"""

from fastapi import APIRouter, Query, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime, timedelta
from app.domain.services.iot_service import IoTService
from app.api.v1.dependencies import get_iot_service

router = APIRouter()

# JSON-LD Context for sensor data
SENSOR_CONTEXT = {
    "@context": {
        "@vocab": "https://openinfra.space/vocab#",
        "sosa": "http://www.w3.org/ns/sosa/",
        "ssn": "http://www.w3.org/ns/ssn/",
        "schema": "https://schema.org/",
        "geo": "http://www.w3.org/2003/01/geo/wgs84_pos#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "qudt": "http://qudt.org/schema/qudt/",
        "dcterms": "http://purl.org/dc/terms/",
        
        # Sensor mappings
        "Sensor": "sosa:Sensor",
        "Observation": "sosa:Observation",
        "FeatureOfInterest": "sosa:FeatureOfInterest",
        "ObservableProperty": "sosa:ObservableProperty",
        "Result": "sosa:Result",
        
        # Properties
        "observes": {"@id": "sosa:observes", "@type": "@id"},
        "madeObservation": {"@id": "sosa:madeObservation", "@type": "@id"},
        "hasFeatureOfInterest": {"@id": "sosa:hasFeatureOfInterest", "@type": "@id"},
        "observedProperty": {"@id": "sosa:observedProperty", "@type": "@id"},
        "hasResult": {"@id": "sosa:hasResult"},
        "resultTime": {"@id": "sosa:resultTime", "@type": "xsd:dateTime"},
        "phenomenonTime": {"@id": "sosa:phenomenonTime", "@type": "xsd:dateTime"},
        
        # Sensor details
        "sensorCode": "schema:identifier",
        "sensorType": "ssn:hasProperty",
        "manufacturer": "schema:manufacturer",
        "model": "schema:model",
        "measurementUnit": "qudt:unit",
        "sampleRate": "ssn:hasSamplingRate",
        "status": "schema:status",
        "lastSeen": {"@id": "schema:dateModified", "@type": "xsd:dateTime"},
        
        # Location
        "location": "geo:location",
        "latitude": {"@id": "geo:lat", "@type": "xsd:float"},
        "longitude": {"@id": "geo:long", "@type": "xsd:float"},
        
        # Asset
        "Asset": "schema:Place",
        "assetId": "schema:identifier",
        "featureType": "schema:additionalType",
        "featureCode": "schema:propertyID",
        
        # Value
        "value": {"@id": "schema:value", "@type": "xsd:float"},
        "unit": "qudt:unit",
        "quality": "schema:quality",
        
        # License
        "license": {"@id": "dcterms:license", "@type": "@id"},
        "rights": "dcterms:rights",
        "publisher": "dcterms:publisher"
    }
}

# ODC-BY License info
LICENSE_INFO = {
    "license": "https://opendatacommons.org/licenses/by/1-0/",
    "rights": "Open Data Commons Attribution License (ODC-BY)",
    "publisher": {
        "@type": "schema:Organization",
        "schema:name": "VKU.OneLove - OpenInfra",
        "schema:url": "https://openinfra.space"
    }
}


def create_sensor_jsonld(sensor, base_url: str = "https://openinfra.space") -> dict:
    """Convert sensor to JSON-LD format following SOSA ontology."""
    sensor_id = str(sensor.id) if sensor.id else sensor.sensor_code
    
    return {
        "@id": f"{base_url}/api/v1/ld/sensors/{sensor_id}",
        "@type": "Sensor",
        "sensorCode": sensor.sensor_code,
        "sensorType": sensor.sensor_type.value if hasattr(sensor.sensor_type, 'value') else sensor.sensor_type,
        "manufacturer": sensor.manufacturer,
        "model": sensor.model,
        "measurementUnit": sensor.measurement_unit,
        "sampleRate": sensor.sample_rate,
        "status": sensor.status.value if hasattr(sensor.status, 'value') else sensor.status,
        "lastSeen": sensor.last_seen.isoformat() if sensor.last_seen else None,
        "hasFeatureOfInterest": {
            "@id": f"{base_url}/api/v1/ld/assets/{sensor.asset_id}",
            "@type": "Asset",
            "assetId": sensor.asset_id
        },
        "observes": {
            "@type": "ObservableProperty",
            "schema:name": sensor.sensor_type.value if hasattr(sensor.sensor_type, 'value') else sensor.sensor_type
        }
    }


def create_observation_jsonld(reading, sensor_info: dict = None, base_url: str = "https://openinfra.space") -> dict:
    """Convert sensor reading to JSON-LD Observation following SOSA ontology."""
    reading_id = str(reading.id) if reading.id else f"{reading.sensor_id}-{reading.timestamp.timestamp()}"
    
    observation = {
        "@id": f"{base_url}/api/v1/ld/observations/{reading_id}",
        "@type": "Observation",
        "resultTime": reading.timestamp.isoformat(),
        "phenomenonTime": reading.timestamp.isoformat(),
        "hasResult": {
            "@type": "Result",
            "value": reading.value,
            "unit": reading.unit,
            "quality": reading.quality
        },
        "hasFeatureOfInterest": {
            "@id": f"{base_url}/api/v1/ld/assets/{reading.asset_id}",
            "@type": "Asset",
            "assetId": reading.asset_id
        },
        "madeObservation": {
            "@id": f"{base_url}/api/v1/ld/sensors/{reading.sensor_id}",
            "@type": "Sensor"
        }
    }
    
    if sensor_info:
        observation["observedProperty"] = {
            "@type": "ObservableProperty",
            "schema:name": sensor_info.get("sensor_type", "unknown")
        }
    
    return observation


@router.get(
    "/context",
    summary="Get JSON-LD Context",
    description="""
    Returns the JSON-LD context document defining the vocabulary mappings.
    
    This context follows W3C standards:
    - **SOSA**: Sensor, Observation, Sample, and Actuator Ontology
    - **SSN**: Semantic Sensor Network Ontology  
    - **Schema.org**: General-purpose vocabulary
    - **GeoSPARQL/WGS84**: Geographic coordinates
    - **QUDT**: Quantities, Units, Dimensions, Types
    
    Use this context with `@context` in JSON-LD documents for semantic interoperability.
    """,
    tags=["Linked Data"],
    responses={
        200: {
            "description": "JSON-LD Context document",
            "content": {
                "application/ld+json": {
                    "example": SENSOR_CONTEXT
                }
            }
        }
    }
)
async def get_context():
    """Return the JSON-LD context for sensor data."""
    return JSONResponse(
        content=SENSOR_CONTEXT,
        media_type="application/ld+json"
    )


@router.get(
    "/sensors",
    summary="List Sensors as JSON-LD",
    description="""
    Returns a list of IoT sensors in JSON-LD format following the SOSA (Sensor, Observation, Sample, and Actuator) ontology.
    
    Each sensor is represented as a `sosa:Sensor` with:
    - Unique `@id` URI
    - `sensorCode`: Device identifier
    - `sensorType`: Observable property type (temperature, humidity, etc.)
    - `hasFeatureOfInterest`: Link to the asset being monitored
    - `observes`: The property being measured
    
    **Pagination**: Use `skip` and `limit` parameters.
    **Filtering**: Filter by `asset_id`, `sensor_type`, or `status`.
    
    The response includes full JSON-LD context for semantic processing.
    """,
    tags=["Linked Data"],
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
                                "measurementUnit": "°C"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def list_sensors_jsonld(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    asset_id: Optional[str] = Query(None, description="Filter by asset ID"),
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    status: Optional[str] = Query(None, description="Filter by sensor status"),
    iot_service: IoTService = Depends(get_iot_service)
):
    """List all sensors in JSON-LD format."""
    sensors = await iot_service.list_sensors(skip, limit, asset_id, sensor_type, status)
    
    sensors_ld = [create_sensor_jsonld(sensor) for sensor in sensors]
    
    result = {
        **SENSOR_CONTEXT,
        **LICENSE_INFO,
        "@type": "schema:ItemList",
        "@id": "https://openinfra.space/api/v1/ld/sensors",
        "schema:name": "OpenInfra IoT Sensors Collection",
        "schema:description": "Collection of IoT sensors monitoring infrastructure assets. Licensed under ODC-BY.",
        "schema:numberOfItems": len(sensors_ld),
        "schema:itemListElement": sensors_ld
    }
    
    return JSONResponse(content=result, media_type="application/ld+json")


@router.get(
    "/sensors/{sensor_id}",
    summary="Get Sensor as JSON-LD",
    description="""
    Returns a single IoT sensor in JSON-LD format.
    
    The sensor is represented as a `sosa:Sensor` entity with full semantic annotations
    following the W3C SOSA ontology.
    
    **Related endpoints**:
    - `/ld/sensors/{sensor_id}/observations` - Get observations from this sensor
    - `/ld/assets/{asset_id}` - Get the monitored asset
    """,
    tags=["Linked Data"],
    responses={
        200: {
            "description": "Sensor in JSON-LD format",
            "content": {
                "application/ld+json": {}
            }
        },
        404: {"description": "Sensor not found"}
    }
)
async def get_sensor_jsonld(
    sensor_id: str,
    iot_service: IoTService = Depends(get_iot_service)
):
    """Get single sensor in JSON-LD format."""
    sensor = await iot_service.get_sensor_by_id(sensor_id)
    
    result = {
        **SENSOR_CONTEXT,
        **LICENSE_INFO,
        **create_sensor_jsonld(sensor)
    }
    
    return JSONResponse(content=result, media_type="application/ld+json")


@router.get(
    "/sensors/{sensor_id}/observations",
    summary="Get Sensor Observations as JSON-LD",
    description="""
    Returns observations (readings) from a specific sensor in JSON-LD format.
    
    Each observation follows the SOSA ontology:
    - `@type`: sosa:Observation
    - `resultTime`: When the observation was made
    - `hasResult`: The measured value with unit and quality
    - `hasFeatureOfInterest`: The asset being monitored
    - `observedProperty`: What property was measured
    
    **Time range**: Specify `from_time` and `to_time` in ISO 8601 format.
    **Pagination**: Use `limit` to control the number of results.
    
    Example time format: `2024-01-01T00:00:00Z`
    """,
    tags=["Linked Data"],
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
                                    "quality": "good"
                                }
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def get_sensor_observations_jsonld(
    sensor_id: str,
    from_time: str = Query(..., description="Start time in ISO 8601 format (e.g., 2024-01-01T00:00:00Z)"),
    to_time: str = Query(..., description="End time in ISO 8601 format (e.g., 2024-01-31T23:59:59Z)"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of observations"),
    iot_service: IoTService = Depends(get_iot_service)
):
    """Get sensor observations in JSON-LD format."""
    from_time_dt = datetime.fromisoformat(from_time.replace('Z', '+00:00'))
    to_time_dt = datetime.fromisoformat(to_time.replace('Z', '+00:00'))
    
    # Get sensor info for context
    sensor = await iot_service.get_sensor_by_id(sensor_id)
    sensor_info = {
        "sensor_type": sensor.sensor_type.value if hasattr(sensor.sensor_type, 'value') else sensor.sensor_type
    }
    
    readings = await iot_service.get_sensor_readings(sensor_id, from_time_dt, to_time_dt, limit)
    
    observations_ld = [
        create_observation_jsonld(reading, sensor_info) 
        for reading in readings
    ]
    
    result = {
        **SENSOR_CONTEXT,
        **LICENSE_INFO,
        "@type": "schema:ItemList",
        "@id": f"https://openinfra.space/api/v1/ld/sensors/{sensor_id}/observations",
        "schema:name": f"Observations from sensor {sensor.sensor_code}",
        "schema:description": f"Time series observations from {from_time} to {to_time}. Licensed under ODC-BY.",
        "schema:numberOfItems": len(observations_ld),
        "madeObservation": {
            "@id": f"https://openinfra.space/api/v1/ld/sensors/{sensor_id}",
            "@type": "Sensor",
            "sensorCode": sensor.sensor_code
        },
        "schema:itemListElement": observations_ld
    }
    
    return JSONResponse(content=result, media_type="application/ld+json")


@router.get(
    "/assets/{asset_id}",
    summary="Get Asset with IoT Data as JSON-LD",
    description="""
    Returns an infrastructure asset with its associated IoT sensor data in JSON-LD format.
    
    The response includes:
    - **Asset metadata**: ID, feature type, feature code
    - **Associated sensors**: List of sensors monitoring this asset
    - **Recent observations**: Latest readings from all sensors
    - **Summary statistics**: Total sensors, readings count
    
    This endpoint links assets (sosa:FeatureOfInterest) with their sensors (sosa:Sensor)
    and observations (sosa:Observation) following the SOSA ontology.
    
    **Time range**: Use `hours` parameter to specify how far back to retrieve data (default: 24 hours).
    """,
    tags=["Linked Data"],
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
                        ]
                    }
                }
            }
        }
    }
)
async def get_asset_jsonld(
    asset_id: str,
    hours: int = Query(24, ge=1, le=168, description="Number of hours of historical data to include"),
    iot_service: IoTService = Depends(get_iot_service)
):
    """Get asset with IoT data in JSON-LD format."""
    from_time = datetime.utcnow() - timedelta(hours=hours)
    to_time = datetime.utcnow()
    
    # Get sensors for this asset
    sensors = await iot_service.list_sensors(0, 100, asset_id=asset_id)
    
    sensors_ld = [create_sensor_jsonld(sensor) for sensor in sensors]
    
    # Get recent readings
    all_observations = []
    for sensor in sensors:
        try:
            readings = await iot_service.get_sensor_readings(
                str(sensor.id), from_time, to_time, limit=100
            )
            sensor_info = {
                "sensor_type": sensor.sensor_type.value if hasattr(sensor.sensor_type, 'value') else sensor.sensor_type
            }
            for reading in readings:
                all_observations.append(create_observation_jsonld(reading, sensor_info))
        except Exception:
            pass
    
    # Sort by time descending
    all_observations.sort(
        key=lambda x: x.get("resultTime", ""), 
        reverse=True
    )
    
    # Get asset info from first sensor if available
    feature_type = sensors[0].sensor_type.value if sensors else "Unknown"
    
    result = {
        **SENSOR_CONTEXT,
        **LICENSE_INFO,
        "@type": "FeatureOfInterest",
        "@id": f"https://openinfra.space/api/v1/ld/assets/{asset_id}",
        "assetId": asset_id,
        "featureType": feature_type,
        "schema:name": f"Asset {asset_id}",
        "schema:description": f"Infrastructure asset with {len(sensors)} IoT sensors. Licensed under ODC-BY.",
        "isFeatureOfInterestOf": sensors_ld,
        "schema:subjectOf": all_observations[:50],  # Limit observations
        "schema:additionalProperty": {
            "@type": "schema:PropertyValue",
            "schema:name": "summary",
            "schema:value": {
                "totalSensors": len(sensors),
                "totalObservations": len(all_observations),
                "timeRangeHours": hours
            }
        }
    }
    
    return JSONResponse(content=result, media_type="application/ld+json")


@router.get(
    "/observations",
    summary="List All Observations as JSON-LD",
    description="""
    Returns recent observations from all sensors in JSON-LD format.
    
    This is useful for:
    - Building a complete observation dataset
    - Integrating with semantic web tools
    - SPARQL endpoint data ingestion
    
    **Filtering**:
    - `asset_id`: Filter by specific asset
    - `sensor_type`: Filter by sensor type (temperature, humidity, etc.)
    
    **Time range**: Use `hours` to specify how far back to retrieve (default: 1 hour).
    """,
    tags=["Linked Data"],
    responses={
        200: {
            "description": "Collection of observations in JSON-LD format",
            "content": {
                "application/ld+json": {}
            }
        }
    }
)
async def list_observations_jsonld(
    hours: int = Query(1, ge=1, le=24, description="Number of hours of data to retrieve"),
    asset_id: Optional[str] = Query(None, description="Filter by asset ID"),
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    limit: int = Query(500, ge=1, le=5000, description="Maximum observations to return"),
    iot_service: IoTService = Depends(get_iot_service)
):
    """List all recent observations in JSON-LD format."""
    from_time = datetime.utcnow() - timedelta(hours=hours)
    to_time = datetime.utcnow()
    
    # Get sensors
    sensors = await iot_service.list_sensors(0, 500, asset_id=asset_id, sensor_type=sensor_type)
    
    all_observations = []
    for sensor in sensors:
        try:
            readings = await iot_service.get_sensor_readings(
                str(sensor.id), from_time, to_time, limit=limit // max(len(sensors), 1)
            )
            sensor_info = {
                "sensor_type": sensor.sensor_type.value if hasattr(sensor.sensor_type, 'value') else sensor.sensor_type
            }
            for reading in readings:
                all_observations.append(create_observation_jsonld(reading, sensor_info))
        except Exception:
            pass
    
    # Sort by time descending and limit
    all_observations.sort(key=lambda x: x.get("resultTime", ""), reverse=True)
    all_observations = all_observations[:limit]
    
    result = {
        **SENSOR_CONTEXT,
        **LICENSE_INFO,
        "@type": "schema:ItemList",
        "@id": "https://openinfra.space/api/v1/ld/observations",
        "schema:name": "OpenInfra IoT Observations",
        "schema:description": f"Recent sensor observations from the past {hours} hour(s). Licensed under ODC-BY.",
        "schema:numberOfItems": len(all_observations),
        "schema:dateCreated": datetime.utcnow().isoformat(),
        "schema:itemListElement": all_observations
    }
    
    return JSONResponse(content=result, media_type="application/ld+json")


@router.get(
    "/vocab",
    summary="Get OpenInfra Vocabulary",
    description="""
    Returns the OpenInfra vocabulary definition in JSON-LD format.
    
    This vocabulary extends standard ontologies (SOSA, SSN, Schema.org) with
    OpenInfra-specific terms for infrastructure management.
    
    Use this for understanding the semantic meaning of properties in the API responses.
    """,
    tags=["Linked Data"]
)
async def get_vocabulary():
    """Return the OpenInfra vocabulary."""
    vocab = {
        "@context": {
            "@vocab": "https://openinfra.space/vocab#",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "owl": "http://www.w3.org/2002/07/owl#"
        },
        "@graph": [
            {
                "@id": "https://openinfra.space/vocab#InfrastructureAsset",
                "@type": "owl:Class",
                "rdfs:label": "Infrastructure Asset",
                "rdfs:comment": "A physical infrastructure asset being monitored",
                "rdfs:subClassOf": "sosa:FeatureOfInterest"
            },
            {
                "@id": "https://openinfra.space/vocab#IoTSensor",
                "@type": "owl:Class",
                "rdfs:label": "IoT Sensor",
                "rdfs:comment": "An IoT sensor device monitoring infrastructure",
                "rdfs:subClassOf": "sosa:Sensor"
            },
            {
                "@id": "https://openinfra.space/vocab#SensorReading",
                "@type": "owl:Class",
                "rdfs:label": "Sensor Reading",
                "rdfs:comment": "A single observation/reading from a sensor",
                "rdfs:subClassOf": "sosa:Observation"
            },
            {
                "@id": "https://openinfra.space/vocab#sensorCode",
                "@type": "owl:DatatypeProperty",
                "rdfs:label": "Sensor Code",
                "rdfs:comment": "Unique identifier code for the sensor device",
                "rdfs:domain": "https://openinfra.space/vocab#IoTSensor",
                "rdfs:range": "xsd:string"
            },
            {
                "@id": "https://openinfra.space/vocab#assetId",
                "@type": "owl:DatatypeProperty",
                "rdfs:label": "Asset ID",
                "rdfs:comment": "Unique identifier for the infrastructure asset",
                "rdfs:domain": "https://openinfra.space/vocab#InfrastructureAsset",
                "rdfs:range": "xsd:string"
            }
        ]
    }
    
    return JSONResponse(content=vocab, media_type="application/ld+json")
