"""API v1 dependencies for dependency injection."""
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.infrastructure.database.mongodb import get_database
from app.infrastructure.database.repositories.mongo_user_repository import MongoUserRepository
from app.infrastructure.database.repositories.mongo_asset_repository import MongoAssetRepository
from app.infrastructure.database.repositories.mongo_audit_repository import MongoAuditRepository
from app.domain.services.user_service import UserService
from app.domain.services.asset_service import AssetService
from app.domain.services.audit_service import AuditService
from app.infrastructure.storage.storage_service import StorageService
from app.infrastructure.storage.local_storage import LocalStorageService


async def get_user_repository():
    """Get user repository instance."""
    db: AsyncIOMotorDatabase = await get_database()
    return MongoUserRepository(db)


async def get_user_service():
    """Get user service instance."""
    repository = await get_user_repository()
    return UserService(repository)


async def get_asset_repository():
    """Get asset repository instance."""
    db: AsyncIOMotorDatabase = await get_database()
    return MongoAssetRepository(db)


async def get_audit_repository():
    """Get audit repository instance."""
    db: AsyncIOMotorDatabase = await get_database()
    return MongoAuditRepository(db)


async def get_audit_service():
    """Get audit service instance."""
    repository = await get_audit_repository()
    return AuditService(repository)


async def get_asset_service():
    """Get asset service instance."""
    repository = await get_asset_repository()
    audit_service = await get_audit_service()
    # Optional: inject maintenance and incident repositories for health score calculation
    try:
        maintenance_repo = await get_maintenance_repository()
    except:
        maintenance_repo = None
    try:
        incident_repo = await get_incident_repository()
    except:
        incident_repo = None
    return AssetService(repository, audit_service, maintenance_repo, incident_repo)


async def get_storage_service():
    """Get storage service instance."""
    return LocalStorageService()


async def get_geospatial_service():
    """Get geospatial service instance."""
    from app.domain.services.geospatial_service import GeospatialService
    repository = await get_asset_repository()
    return GeospatialService(repository)


async def get_osm_service():
    """Get OSM service instance."""
    from app.infrastructure.external.osm_service import OSMService
    return OSMService()


async def get_iot_sensor_repository():
    """Get IoT sensor repository instance."""
    from app.infrastructure.database.repositories.mongo_iot_repository import MongoIoTSensorRepository
    db: AsyncIOMotorDatabase = await get_database()
    return MongoIoTSensorRepository(db)


async def get_sensor_data_repository():
    """Get sensor data repository instance."""
    from app.infrastructure.database.repositories.mongo_sensor_data_repository import MongoSensorDataRepository
    db: AsyncIOMotorDatabase = await get_database()
    return MongoSensorDataRepository(db)


async def get_alert_repository():
    """Get alert repository instance."""
    from app.infrastructure.database.repositories.mongo_alert_repository import MongoAlertRepository
    db: AsyncIOMotorDatabase = await get_database()
    return MongoAlertRepository(db)


async def get_alert_service():
    """Get alert service instance."""
    from app.domain.services.alert_service import AlertService
    repository = await get_alert_repository()
    return AlertService(repository)


async def get_iot_service():
    """Get IoT service instance."""
    from app.domain.services.iot_service import IoTService
    sensor_repo = await get_iot_sensor_repository()
    data_repo = await get_sensor_data_repository()
    alert_service = await get_alert_service()
    return IoTService(sensor_repo, data_repo, alert_service)


async def get_incident_repository():
    """Get incident repository instance."""
    from app.infrastructure.database.repositories.mongo_incident_repository import MongoIncidentRepository
    db: AsyncIOMotorDatabase = await get_database()
    return MongoIncidentRepository(db)


async def get_incident_service():
    """Get incident service instance."""
    from app.domain.services.incident_service import IncidentService
    repository = await get_incident_repository()
    # Maintenance service is optional
    try:
        from app.api.v1.dependencies import get_maintenance_service
        maintenance_service = await get_maintenance_service()
    except:
        maintenance_service = None
        
    # Asset service is optional but recommended for location population
    try:
        from app.api.v1.dependencies import get_asset_service
        asset_service = await get_asset_service()
    except:
        asset_service = None
        
    return IncidentService(repository, maintenance_service, asset_service)


async def get_budget_repository():
    """Get budget repository instance."""
    from app.infrastructure.database.repositories.mongo_budget_repository import MongoBudgetRepository
    db: AsyncIOMotorDatabase = await get_database()
    return MongoBudgetRepository(db)


async def get_budget_transaction_repository():
    """Get budget transaction repository instance."""
    from app.infrastructure.database.repositories.mongo_budget_repository import MongoBudgetTransactionRepository
    db: AsyncIOMotorDatabase = await get_database()
    return MongoBudgetTransactionRepository(db)


async def get_budget_service():
    """Get budget service instance."""
    from app.domain.services.budget_service import BudgetService
    budget_repo = await get_budget_repository()
    transaction_repo = await get_budget_transaction_repository()
    return BudgetService(budget_repo, transaction_repo)


async def get_notification_repository():
    """Get notification repository instance."""
    from app.infrastructure.database.repositories.mongo_notification_repository import MongoNotificationRepository
    db: AsyncIOMotorDatabase = await get_database()
    return MongoNotificationRepository(db)


async def get_notification_service():
    """Get notification service instance."""
    from app.domain.services.notification_service import NotificationService
    from app.infrastructure.notifications.email_service import EmailService
    from app.infrastructure.notifications.sms_service import SMSService
    from app.infrastructure.notifications.push_service import PushService
    notification_repo = await get_notification_repository()
    user_repo = await get_user_repository()
    return NotificationService(
        notification_repo,
        user_repo,
        EmailService(),
        SMSService(),
        PushService()
    )


async def get_report_repository():
    """Get report repository instance."""
    from app.infrastructure.database.repositories.mongo_report_repository import MongoReportRepository
    db: AsyncIOMotorDatabase = await get_database()
    return MongoReportRepository(db)


async def get_report_service():
    """Get report service instance."""
    from app.domain.services.report_service import ReportService
    from app.infrastructure.reports.report_generator import ReportGenerator
    report_repo = await get_report_repository()
    report_generator = ReportGenerator()
    return ReportService(report_repo, report_generator)


async def get_maintenance_repository():
    """Get maintenance repository instance."""
    from app.infrastructure.database.repositories.mongo_maintenance_repository import MongoMaintenanceRepository
    db: AsyncIOMotorDatabase = await get_database()
    return MongoMaintenanceRepository(db)


async def get_maintenance_service():
    """Get maintenance service instance."""
    from app.domain.services.maintenance_service import MaintenanceService
    maintenance_repo = await get_maintenance_repository()
    asset_service = await get_asset_service()
    try:
        budget_service = await get_budget_service()
    except:
        budget_service = None
    return MaintenanceService(maintenance_repo, asset_service, budget_service)
