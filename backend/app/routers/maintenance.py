from fastapi import APIRouter, HTTPException
from typing import List
from app.db.mongodb import get_database
from app.models.maintenance import MaintenanceLog, MaintenanceLogCreate
from bson import ObjectId

router = APIRouter()

@router.post("/", response_model=MaintenanceLog)
async def create_log(log: MaintenanceLogCreate):
    db = await get_database()
    # Verify asset exists
    if not ObjectId.is_valid(log.asset_id):
         raise HTTPException(status_code=400, detail="Invalid Asset ID")
         
    asset = await db["assets"].find_one({"_id": ObjectId(log.asset_id)})
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    new_log = await db["maintenance_logs"].insert_one(log.dict())
    created_log = await db["maintenance_logs"].find_one({"_id": new_log.inserted_id})
    return MaintenanceLog(**created_log)

@router.get("/asset/{asset_id}", response_model=List[MaintenanceLog])
async def get_asset_logs(asset_id: str):
    db = await get_database()
    cursor = db["maintenance_logs"].find({"asset_id": asset_id}).sort("created_at", -1)
    logs = await cursor.to_list(length=1000)
    return [MaintenanceLog(**log) for log in logs]
