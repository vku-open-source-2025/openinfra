from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional
from app.db.mongodb import get_database
from app.models.asset import Asset, AssetCreate
from bson import ObjectId

router = APIRouter()

@router.post("/", response_model=Asset)
async def create_asset(asset: AssetCreate):
    db = await get_database()
    new_asset = await db["assets"].insert_one(asset.dict())
    created_asset = await db["assets"].find_one({"_id": new_asset.inserted_id})
    return Asset(**created_asset)

@router.get("/", response_model=List[Asset])
async def list_assets(
    skip: int = 0, 
    limit: Optional[int] = None, 
    feature_type: Optional[str] = None
):
    db = await get_database()
    query = {}
    if feature_type:
        query["feature_type"] = feature_type
        
    cursor = db["assets"].find(query).skip(skip)
    if limit:
        cursor = cursor.limit(limit)
    
    assets: List[Asset] = []
    async for asset in cursor:
        assets.append(Asset(**asset))
    return assets

@router.get("/{id}", response_model=Asset)
async def get_asset(id: str):
    db = await get_database()
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ID")
        
    asset = await db["assets"].find_one({"_id": ObjectId(id)})
    if asset:
        return Asset(**asset)
    raise HTTPException(status_code=404, detail="Asset not found")

@router.put("/{id}", response_model=Asset)
async def update_asset(id: str, asset_update: AssetCreate):
    db = await get_database()
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ID")
        
    update_result = await db["assets"].update_one(
        {"_id": ObjectId(id)}, {"$set": asset_update.dict()}
    )
    
    if update_result.modified_count == 1:
        updated_asset = await db["assets"].find_one({"_id": ObjectId(id)})
        return Asset(**updated_asset)
        
    existing_asset = await db["assets"].find_one({"_id": ObjectId(id)})
    if existing_asset:
        return Asset(**existing_asset)
        
    raise HTTPException(status_code=404, detail="Asset not found")

@router.delete("/{id}")
async def delete_asset(id: str):
    db = await get_database()
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ID")
        
    delete_result = await db["assets"].delete_one({"_id": ObjectId(id)})
    
    if delete_result.deleted_count == 1:
        return {"message": "Asset deleted successfully"}
        
    raise HTTPException(status_code=404, detail="Asset not found")
