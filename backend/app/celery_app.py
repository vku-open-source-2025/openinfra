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
    include=["app.tasks.csv_import", "app.tasks.content_filter"]
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
    "import-csv-daily": {
        "task": "app.tasks.csv_import.import_csv_data",
        "schedule": crontab(hour=2, minute=0),  # Run daily at 2 AM UTC
    },
    "content-filter-hourly": {
        "task": "app.tasks.content_filter.filter_inappropriate_content",
        "schedule": crontab(minute=0),  # Run every hour at minute 0
    },
}

if __name__ == "__main__":
    app.start()
