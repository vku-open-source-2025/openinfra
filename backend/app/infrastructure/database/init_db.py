"""Database initialization script - creates collections and indexes."""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


async def create_indexes(db):
    """Create all database indexes."""

    # Users collection
    await db.users.create_index("username", unique=True)
    await db.users.create_index("email", unique=True)
    await db.users.create_index("role")
    await db.users.create_index("status")
    await db.users.create_index([("created_at", -1)])
    logger.info("Created indexes for users collection")

    # Assets collection
    await db.assets.create_index([("geometry", "2dsphere")])  # Geospatial index
    await db.assets.create_index("asset_code", unique=True, sparse=True)
    await db.assets.create_index("feature_type")
    await db.assets.create_index("category")
    await db.assets.create_index("status")
    await db.assets.create_index([("location.district", 1), ("location.ward", 1)])
    await db.assets.create_index("qr_code", sparse=True)
    await db.assets.create_index("nfc_tag_id", sparse=True)
    await db.assets.create_index([("created_at", -1)])
    await db.assets.create_index([("status", 1), ("feature_type", 1)])
    await db.assets.create_index([("category", 1), ("status", 1)])
    logger.info("Created indexes for assets collection")

    # Maintenance records collection
    await db.maintenance_records.create_index("work_order_number", unique=True)
    await db.maintenance_records.create_index("asset_id")
    await db.maintenance_records.create_index("status")
    await db.maintenance_records.create_index("assigned_to")
    await db.maintenance_records.create_index("scheduled_date")
    await db.maintenance_records.create_index([("created_at", -1)])
    await db.maintenance_records.create_index([("asset_id", 1), ("status", 1)])
    await db.maintenance_records.create_index([("status", 1), ("priority", 1), ("scheduled_date", 1)])
    await db.maintenance_records.create_index([("assigned_to", 1), ("status", 1)])
    logger.info("Created indexes for maintenance_records collection")

    # Incidents collection
    await db.incidents.create_index("incident_number", unique=True)
    await db.incidents.create_index("asset_id")
    await db.incidents.create_index("status")
    await db.incidents.create_index("severity")
    await db.incidents.create_index("reported_by")
    await db.incidents.create_index("assigned_to")
    await db.incidents.create_index([("reported_at", -1)])
    await db.incidents.create_index([("location.geometry", "2dsphere")])  # Geospatial index
    await db.incidents.create_index([("status", 1), ("severity", 1)])
    await db.incidents.create_index([("asset_id", 1), ("status", 1)])
    # Compound index for duplicate detection queries
    await db.incidents.create_index([("asset_id", 1), ("status", 1), ("reported_at", -1)])
    await db.incidents.create_index([("category", 1), ("severity", 1), ("reported_at", -1)])
    logger.info("Created indexes for incidents collection")

    # Merge suggestions collection
    await db.merge_suggestions.create_index("primary_incident_id")
    await db.merge_suggestions.create_index("status")
    await db.merge_suggestions.create_index([("primary_incident_id", 1), ("status", 1)])
    await db.merge_suggestions.create_index([("created_at", -1)])
    await db.merge_suggestions.create_index([("status", 1), ("created_at", -1)])
    logger.info("Created indexes for merge_suggestions collection")

    # IoT Sensors collection
    await db.iot_sensors.create_index("sensor_code", unique=True)
    await db.iot_sensors.create_index("asset_id")
    await db.iot_sensors.create_index("status")
    await db.iot_sensors.create_index("sensor_type")
    await db.iot_sensors.create_index([("last_seen", -1)])
    logger.info("Created indexes for iot_sensors collection")

    # Sensor data (time-series collection)
    # Note: Time-series collection will be created separately
    await db.sensor_data.create_index([("sensor_id", 1), ("timestamp", -1)])
    await db.sensor_data.create_index([("asset_id", 1), ("timestamp", -1)])
    await db.sensor_data.create_index([("status", 1), ("timestamp", -1)])
    logger.info("Created indexes for sensor_data collection")

    # Alerts collection
    await db.alerts.create_index("alert_code", unique=True)
    await db.alerts.create_index("asset_id")
    await db.alerts.create_index("sensor_id")
    await db.alerts.create_index("status")
    await db.alerts.create_index("severity")
    await db.alerts.create_index([("triggered_at", -1)])
    await db.alerts.create_index([("status", 1), ("severity", 1), ("triggered_at", -1)])
    logger.info("Created indexes for alerts collection")

    # Budgets collection
    await db.budgets.create_index("budget_code", unique=True)
    await db.budgets.create_index("fiscal_year")
    await db.budgets.create_index("status")
    await db.budgets.create_index("category")
    await db.budgets.create_index([("start_date", 1), ("end_date", 1)])
    logger.info("Created indexes for budgets collection")

    # Budget transactions collection
    await db.budget_transactions.create_index("transaction_number", unique=True)
    await db.budget_transactions.create_index("budget_id")
    await db.budget_transactions.create_index("maintenance_record_id")
    await db.budget_transactions.create_index("asset_id")
    await db.budget_transactions.create_index("status")
    await db.budget_transactions.create_index([("transaction_date", -1)])
    await db.budget_transactions.create_index([("created_at", -1)])
    await db.budget_transactions.create_index([("budget_id", 1), ("status", 1)])
    logger.info("Created indexes for budget_transactions collection")

    # Notifications collection
    await db.notifications.create_index([("user_id", 1), ("created_at", -1)])
    await db.notifications.create_index([("user_id", 1), ("read", 1)])
    await db.notifications.create_index([("resource_type", 1), ("resource_id", 1)])
    await db.notifications.create_index("expires_at", expireAfterSeconds=0)  # TTL index
    logger.info("Created indexes for notifications collection")

    # Audit logs collection
    await db.audit_logs.create_index([("timestamp", -1)])
    await db.audit_logs.create_index([("user_id", 1), ("timestamp", -1)])
    await db.audit_logs.create_index([("resource_type", 1), ("resource_id", 1)])
    await db.audit_logs.create_index([("action", 1), ("timestamp", -1)])
    await db.audit_logs.create_index("request_id")
    await db.audit_logs.create_index("timestamp", expireAfterSeconds=31536000)  # TTL: 1 year
    logger.info("Created indexes for audit_logs collection")

    # Reports collection
    await db.reports.create_index("report_code", unique=True)
    await db.reports.create_index("type")
    await db.reports.create_index([("created_by", 1), ("created_at", -1)])
    await db.reports.create_index("status")
    await db.reports.create_index("expires_at", expireAfterSeconds=0)  # TTL index
    logger.info("Created indexes for reports collection")

    # System settings collection
    await db.system_settings.create_index("key", unique=True)
    await db.system_settings.create_index("category")
    await db.system_settings.create_index("environment")
    logger.info("Created indexes for system_settings collection")


async def create_time_series_collection(db):
    """Create time-series collection for sensor data."""
    try:
        # Check if collection already exists
        collections = await db.list_collection_names()
        if "sensor_data" not in collections:
            # Create time-series collection
            await db.create_collection(
                "sensor_data",
                timeseries={
                    "timeField": "timestamp",
                    "metaField": "sensor_id",
                    "granularity": "minutes"
                },
                expireAfterSeconds=31536000  # 1 year retention
            )
            logger.info("Created time-series collection sensor_data")
        else:
            logger.info("Time-series collection sensor_data already exists")
    except Exception as e:
        logger.error(f"Error creating time-series collection: {e}")


async def init_database():
    """Initialize database with collections and indexes."""
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]

    try:
        logger.info("Starting database initialization...")

        # Create time-series collection first
        await create_time_series_collection(db)

        # Create all indexes
        await create_indexes(db)

        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(init_database())
