"""
Manual trigger for CSV import task
Run this to test the CSV import cronjob manually
"""

from app.celery_app import app
from app.tasks.csv_import import import_csv_data

if __name__ == "__main__":
    print("Triggering CSV import task...")
    result = import_csv_data.delay()
    print(f"Task ID: {result.task_id}")
    print("Task queued. Check celery worker logs for progress.")
    print("Use: docker logs infra-celery-worker-1 -f")
