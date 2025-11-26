"""
CSV Import Celery Task
Downloads CSV from API and imports infrastructure data into MongoDB,
skipping duplicate coordinates.
"""

from celery import Task
from app.celery_app import app
from app.services.csv_service import download_csv, parse_csv_to_assets, insert_assets_skip_duplicates
from app.db.mongodb import db
import os


class DatabaseTask(Task):
    """Base task with database connection"""
    _db = None

    @property
    def database(self):
        if self._db is None:
            db.connect()
            self._db = db
        return self._db


@app.task(base=DatabaseTask, bind=True, name="app.tasks.csv_import.import_csv_data")
def import_csv_data(self):
    """
    Download CSV from API and import into database
    Skips assets with duplicate coordinates
    """
    try:
        # Get CSV URL from environment
        csv_url = os.getenv("CSV_IMPORT_URL")
        if not csv_url:
            raise ValueError("CSV_IMPORT_URL environment variable not set")
        
        self.update_state(state="PROGRESS", meta={"step": "downloading"})
        
        # Download CSV
        csv_content = download_csv(csv_url)
        
        self.update_state(state="PROGRESS", meta={"step": "parsing"})
        
        # Parse CSV to assets
        assets = parse_csv_to_assets(csv_content)
        
        self.update_state(state="PROGRESS", meta={"step": "importing"})
        
        # Insert assets, skipping duplicates
        result = insert_assets_skip_duplicates(self.database, assets)
        
        return {
            "status": "success",
            "total": result["total"],
            "inserted": result["inserted"],
            "skipped": result["skipped"],
            "errors": result["errors"]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
