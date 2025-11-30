"""Data ingestion API router."""
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ingestion import ingest_csv_data

router = APIRouter()


@router.post("/csv")
async def upload_csv(file: UploadFile = File(...)):
    """Upload and ingest CSV file."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV.")

    content = await file.read()
    count = await ingest_csv_data(content)
    return {"message": f"Successfully ingested {count} assets."}
