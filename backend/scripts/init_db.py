#!/usr/bin/env python3
"""Database initialization script."""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.infrastructure.database.init_db import init_database
from app.core.logging import setup_logging

if __name__ == "__main__":
    logger = setup_logging()
    asyncio.run(init_database())
