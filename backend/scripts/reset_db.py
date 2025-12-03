#!/usr/bin/env python3
"""Database reset script - drops all collections and reinitializes the database."""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.infrastructure.database.init_db import (
    create_indexes,
    create_time_series_collection,
)
from app.core.logging import setup_logging

logger = setup_logging()


async def drop_all_collections(db, confirm: bool = False):
    """Drop all collections from the database."""
    if not confirm:
        logger.warning("This will delete ALL data in the database!")
        logger.warning("Set confirm=True to proceed")
        return False

    try:
        collections = await db.list_collection_names()
        if not collections:
            logger.info("No collections found in database")
            return True

        # Filter out system collections that cannot be dropped when time-series collections exist
        system_collections = {"system.views", "system.buckets"}
        user_collections = [c for c in collections if c not in system_collections]

        logger.info(
            f"Found {len(collections)} collections total, {len(user_collections)} user collections to drop"
        )
        if system_collections & set(collections):
            logger.info(
                f"Skipping system collections: {', '.join(system_collections & set(collections))}"
            )

        for collection_name in user_collections:
            try:
                await db.drop_collection(collection_name)
                logger.info(f"Dropped collection: {collection_name}")
            except Exception as e:
                logger.warning(f"Could not drop collection {collection_name}: {e}")
                # Try to clear it instead
                try:
                    await db[collection_name].delete_many({})
                    logger.info(f"Cleared collection: {collection_name}")
                except Exception as clear_error:
                    logger.error(
                        f"Could not clear collection {collection_name}: {clear_error}"
                    )

        logger.info("All user collections dropped/cleared successfully")
        return True
    except Exception as e:
        logger.error(f"Error dropping collections: {e}")
        raise


async def drop_database(client, confirm: bool = False):
    """Drop the entire database."""
    if not confirm:
        logger.warning("This will delete the ENTIRE database!")
        logger.warning("Set confirm=True to proceed")
        return False

    try:
        await client.drop_database(settings.DATABASE_NAME)
        logger.info(f"Dropped database: {settings.DATABASE_NAME}")
        return True
    except Exception as e:
        logger.error(f"Error dropping database: {e}")
        raise


async def reset_database(
    drop_db: bool = False, confirm: bool = False, reinit: bool = True
):
    """
    Reset the database by dropping collections/database and optionally reinitializing.

    Args:
        drop_db: If True, drops the entire database. If False, drops all collections.
        confirm: Safety flag - must be True to actually perform the reset.
        reinit: If True, reinitializes the database after dropping.
    """
    if not confirm:
        logger.error("Safety check failed: confirm must be True to reset database")
        logger.error("Usage: reset_database(drop_db=False, confirm=True, reinit=True)")
        return

    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]

    try:
        logger.info("=" * 60)
        logger.info("DATABASE RESET STARTED")
        logger.info("=" * 60)
        logger.info(f"Database: {settings.DATABASE_NAME}")
        logger.info(f"MongoDB URL: {settings.MONGODB_URL}")
        logger.info(f"Drop entire database: {drop_db}")
        logger.info(f"Reinitialize after reset: {reinit}")
        logger.info("=" * 60)

        # Drop database or collections
        if drop_db:
            await drop_database(client, confirm=True)
        else:
            await drop_all_collections(db, confirm=True)

        # Reinitialize if requested
        if reinit:
            logger.info("Reinitializing database...")
            # Reconnect after dropping database
            if drop_db:
                db = client[settings.DATABASE_NAME]

            # Create time-series collection first
            await create_time_series_collection(db)

            # Create all indexes
            await create_indexes(db)

            logger.info("Database reinitialized successfully")

        logger.info("=" * 60)
        logger.info("DATABASE RESET COMPLETED")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        raise
    finally:
        client.close()
        logger.info("Database connection closed")


async def main():
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Reset the database by dropping all collections/database and reinitializing"
    )
    parser.add_argument(
        "--drop-db",
        action="store_true",
        help="Drop the entire database instead of just collections",
    )
    parser.add_argument(
        "--no-reinit",
        action="store_true",
        help="Skip reinitialization after dropping (just drop, don't recreate)",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm that you want to reset the database (required for safety)",
    )

    args = parser.parse_args()

    if not args.confirm:
        print("\n" + "=" * 60)
        print("WARNING: This will DELETE ALL DATA in the database!")
        print("=" * 60)
        print(f"Database: {settings.DATABASE_NAME}")
        print(f"MongoDB URL: {settings.MONGODB_URL}")
        print("\nTo proceed, run with --confirm flag")
        print("Example: python scripts/reset_db.py --confirm")
        print("=" * 60 + "\n")
        sys.exit(1)

    await reset_database(drop_db=args.drop_db, confirm=True, reinit=not args.no_reinit)


if __name__ == "__main__":
    asyncio.run(main())
