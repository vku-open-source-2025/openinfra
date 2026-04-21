from celery import Celery
from celery.schedules import crontab
import os

# Get configuration from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
app = Celery(
    "openinfra",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.tasks.csv_import",
        "app.tasks.sensor_monitoring",
        "app.tasks.report_generation",
        "app.tasks.content_filter",
        "app.tasks.contribution_etl",
        "app.tasks.hazard_ingest",
        "app.tasks.event_monitoring",
        "app.tasks.dispatch_optimization",
        "app.tasks.vector_corpus_ingest",
    ],
)

# Configure Celery
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Configure Celery Beat schedule
app.conf.beat_schedule = {
    "check-sensor-offline": {
        "task": "check_sensor_offline_status",
        "schedule": crontab(minute="*/15"),  # Run every 15 minutes
    },
    "aggregate-sensor-data-hourly": {
        "task": "aggregate_sensor_data_hourly",
        "schedule": crontab(minute=0),  # Run every hour
    },
    "ai-automated-risk-detection": {
        "task": "ai_automated_risk_detection",
        "schedule": crontab(minute="*/15"),  # Run every 30 minutes
    },
    "generate-scheduled-reports": {
        "task": "generate_scheduled_reports",
        "schedule": crontab(hour=0, minute=0),  # Run daily at midnight
    },
    "content-filter-hourly": {
        "task": "app.tasks.content_filter.filter_inappropriate_content",
        "schedule": crontab(minute=0),  # Run every hour at minute 0
    },
    "sync-contributions": {
        "task": "app.tasks.contribution_etl.sync_contributions",
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
    },
    "crawl-and-update-hazard-feeds": {
        "task": "app.tasks.hazard_ingest.crawl_and_update_hazard_layers",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
    "monitor-active-emergency-events": {
        "task": "app.tasks.event_monitoring.monitor_active_emergency_events",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
    "optimize-dispatch-orders": {
        "task": "app.tasks.dispatch_optimization.optimize_dispatch_orders",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
    },
    "ingest-vector-corpus": {
        "task": "app.tasks.vector_corpus_ingest.ingest_vector_corpus",
        "schedule": crontab(minute=20, hour="*/1"),  # Every hour at minute 20
    },
}

if __name__ == "__main__":
    app.start()
