"""
Content Filter Task
Scans MongoDB documents for inappropriate keywords and removes them.
Keywords are loaded from filter_text.txt file.

Usage:
    # Trigger manually
    from app.tasks.content_filter import filter_inappropriate_content
    filter_inappropriate_content.delay()
    
    # Or schedule in celery_app.py
"""
import os
import logging
from celery import shared_task
from pymongo import MongoClient

logger = logging.getLogger(__name__)

# Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "openinfra")

# Path to filter keywords file
FILTER_FILE_PATH = os.path.join(os.path.dirname(__file__), "filter_text.txt")


def load_filter_keywords() -> set:
    """Load filter keywords from file"""
    keywords = set()
    
    try:
        with open(FILTER_FILE_PATH, "r", encoding="utf-8") as f:
            content = f.read()
            # Split by comma and clean up
            for keyword in content.split(","):
                keyword = keyword.strip().lower()
                if keyword:
                    keywords.add(keyword)
        logger.info(f"Loaded {len(keywords)} filter keywords")
    except FileNotFoundError:
        logger.error(f"Filter file not found: {FILTER_FILE_PATH}")
        # Default keywords
        keywords = {"hacker", "test", "spam", "cặc", "lồn"}
    
    return keywords


def check_value_contains_keyword(value, keywords: set) -> bool:
    """Check if a value contains any keyword"""
    if value is None:
        return False
    
    if isinstance(value, str):
        value_lower = value.lower()
        for keyword in keywords:
            if keyword in value_lower:
                return True
    elif isinstance(value, list):
        for item in value:
            if check_value_contains_keyword(item, keywords):
                return True
    elif isinstance(value, dict):
        for k, v in value.items():
            # Check key
            if k.lower() in keywords:
                return True
            # Check value
            if check_value_contains_keyword(v, keywords):
                return True
    
    return False


def check_document_for_keywords(doc: dict, keywords: set) -> bool:
    """Check if document contains any inappropriate keyword in keys or values"""
    for key, value in doc.items():
        # Skip internal MongoDB fields
        if key.startswith("_"):
            continue
        
        # Check key name
        if key.lower() in keywords:
            return True
        
        # Check value
        if check_value_contains_keyword(value, keywords):
            return True
    
    return False


@shared_task(name="app.tasks.content_filter.filter_inappropriate_content")
def filter_inappropriate_content():
    """
    Scan all collections for inappropriate content and remove matching documents.
    
    Returns:
        dict: Summary of filtered documents per collection
    """
    logger.info("Starting content filter task...")
    
    # Load keywords
    keywords = load_filter_keywords()
    logger.info(f"Filter keywords: {keywords}")
    
    # Connect to MongoDB
    client = MongoClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    logger.info(f"Connected to MongoDB: {DATABASE_NAME}")
    
    # Collections to scan
    collections_to_scan = ["assets", "maintenance_logs", "sensors", "alerts"]
    
    results = {
        "status": "success",
        "scanned_collections": [],
        "total_deleted": 0,
        "details": {}
    }
    
    for collection_name in collections_to_scan:
        if collection_name not in db.list_collection_names():
            logger.info(f"Collection {collection_name} not found, skipping...")
            continue
        
        collection = db[collection_name]
        deleted_count = 0
        deleted_ids = []
        
        logger.info(f"Scanning collection: {collection_name}")
        
        # Scan all documents
        cursor = collection.find({})
        
        for doc in cursor:
            if check_document_for_keywords(doc, keywords):
                doc_id = doc.get("_id")
                logger.warning(f"Found inappropriate content in {collection_name}, doc_id: {doc_id}")
                
                # Delete the document
                collection.delete_one({"_id": doc_id})
                deleted_count += 1
                deleted_ids.append(str(doc_id))
        
        results["scanned_collections"].append(collection_name)
        results["total_deleted"] += deleted_count
        results["details"][collection_name] = {
            "deleted": deleted_count,
            "deleted_ids": deleted_ids[:10]  # Only keep first 10 IDs for logging
        }
        
        logger.info(f"Collection {collection_name}: deleted {deleted_count} documents")
    
    client.close()
    logger.info(f"Content filter completed. Total deleted: {results['total_deleted']}")
    
    return results


@shared_task(name="app.tasks.content_filter.filter_single_collection")
def filter_single_collection(collection_name: str):
    """
    Filter a single collection for inappropriate content.
    
    Args:
        collection_name: Name of the collection to scan
        
    Returns:
        dict: Summary of filtered documents
    """
    logger.info(f"Starting content filter for collection: {collection_name}")
    
    keywords = load_filter_keywords()
    
    client = MongoClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    if collection_name not in db.list_collection_names():
        return {"status": "error", "message": f"Collection {collection_name} not found"}
    
    collection = db[collection_name]
    deleted_count = 0
    deleted_ids = []
    
    cursor = collection.find({})
    
    for doc in cursor:
        if check_document_for_keywords(doc, keywords):
            doc_id = doc.get("_id")
            collection.delete_one({"_id": doc_id})
            deleted_count += 1
            deleted_ids.append(str(doc_id))
    
    client.close()
    
    return {
        "status": "success",
        "collection": collection_name,
        "deleted": deleted_count,
        "deleted_ids": deleted_ids[:10]
    }
