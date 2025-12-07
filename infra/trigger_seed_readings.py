#!/usr/bin/env python3
"""
Script to trigger sensor readings seeding task.
Run from infra directory: python trigger_seed_readings.py
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from celery import Celery

# Connect to Redis
redis_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
app = Celery('tasks', broker=redis_url)

def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    readings_per_day = int(sys.argv[2]) if len(sys.argv) > 2 else 96
    
    print(f"🚀 Triggering sensor readings seed task...")
    print(f"   Days: {days}")
    print(f"   Readings per day: {readings_per_day}")
    print(f"   Total readings per sensor: {days * readings_per_day}")
    
    # Send task
    result = app.send_task(
        'seed_sensor_readings',
        args=[days, readings_per_day]
    )
    
    print(f"✅ Task sent! Task ID: {result.id}")
    print(f"   Monitor with: docker-compose logs -f celery-worker")

if __name__ == "__main__":
    main()
