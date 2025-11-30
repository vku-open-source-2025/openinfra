"""MongoDB database connection."""
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager."""

    client: AsyncIOMotorClient = None

    def connect(self):
        """Connect to MongoDB."""
        self.client = AsyncIOMotorClient(settings.MONGODB_URL)
        logger.info("Connected to MongoDB")

    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")

    def get_db(self):
        """Get database instance."""
        return self.client[settings.DATABASE_NAME]


# Global database instance
db = Database()


async def get_database():
    """Dependency to get database instance."""
    return db.get_db()
