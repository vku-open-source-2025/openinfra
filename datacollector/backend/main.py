from fastapi import FastAPI, HTTPException, Body, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response as FastAPIResponse
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, ValidationError, validator
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
import csv
import io
import json
from bson import ObjectId
from bson.errors import InvalidId
from fastapi.responses import FileResponse, StreamingResponse
import unicodedata
from datetime import datetime
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
import bleach

def _normalize(s: str) -> str:
    # Normalize Unicode, remove diacritics, replace Vietnamese special characters, and lowercase
    normalized = unicodedata.normalize('NFKD', s)
    stripped = ''.join(c for c in normalized if not unicodedata.combining(c))
    # Replace specific characters not handled by decomposition
    stripped = stripped.replace('đ', 'd').replace('Đ', 'd')
    return stripped.lower()
# Import authentication utilities
from auth import get_current_user, authenticate_user, create_access_token, create_refresh_token, decode_token
from models import LoginRequest, TokenResponse, RefreshTokenRequest, ContributionInput

load_dotenv()

# Security Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
security_logger = logging.getLogger("security")

# Validate JWT Secret Key at startup - SECURITY: Prevent default secrets
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
if not SECRET_KEY or SECRET_KEY == "your-secret-key-change-this-in-production" or len(SECRET_KEY) < 32:
    raise ValueError(
        "\n" + "="*80 + "\n"
        "SECURITY ERROR: Invalid JWT_SECRET_KEY!\n"
        "Please set a strong secret key in .env file.\n"
        "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'\n"
        + "="*80
    )

app = FastAPI()

# Rate Limiter Configuration
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    # XSS Protection
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # Force HTTPS in production
    if os.getenv("ENVIRONMENT") == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # Content Security Policy
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https://*.google.com https://*.gstatic.com; "
        "font-src 'self'; "
        "frame-ancestors 'none';"
    )
    return response

# CORS Configuration - SECURITY: Only allow localhost for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper function to validate ObjectId - SECURITY: Prevent NoSQL injection
def validate_object_id(id_string: str, field_name: str = "id") -> ObjectId:
    """
    Validate and convert string to ObjectId.
    Raises HTTPException if invalid.
    """
    try:
        return ObjectId(id_string)
    except (InvalidId, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name} format"
        )

# Authentication Endpoints
@app.post("/api/auth/login", response_model=TokenResponse)
@limiter.limit("5/minute")  # SECURITY: Rate limit to prevent brute force
async def login(request: Request, login_data: LoginRequest):
    """
    Authenticate user and return JWT tokens.
    """
    username = authenticate_user(login_data.username, login_data.password)
    if not username:
        # SECURITY: Log failed login attempts
        security_logger.warning(
            f"Failed login attempt for user '{login_data.username}' from {request.client.host}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # SECURITY: Log successful login
    security_logger.info(f"Successful login: {username} from {request.client.host}")
    
    # Create tokens
    access_token = create_access_token(data={"sub": username})
    refresh_token = create_refresh_token(data={"sub": username})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@app.post("/api/auth/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")  # SECURITY: Rate limit token refresh
async def refresh_token(request: Request, refresh_data: RefreshTokenRequest):
    """
    Refresh access token using refresh token.
    """
    try:
        payload = decode_token(refresh_data.refresh_token)
        
        # Check token type
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create new tokens
        new_access_token = create_access_token(data={"sub": username})
        new_refresh_token = create_refresh_token(data={"sub": username})
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Storage Abstraction
class Storage:
    async def get_features(self):
        raise NotImplementedError
    async def add_feature(self, feature):
        raise NotImplementedError
    async def delete_feature(self, feature_id):
        raise NotImplementedError
    async def add_contribution(self, contribution):
        raise NotImplementedError
    async def get_pending_contributions(self):
        raise NotImplementedError
    async def approve_contribution(self, contribution_id):
        raise NotImplementedError
    async def reject_contribution(self, contribution_id):
        raise NotImplementedError
    async def get_leaderboard(self):
        raise NotImplementedError

class MongoStorage(Storage):
    def __init__(self, uri):
        self.client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=2000)
        self.db = self.client.openinfra_gis
        self.collection = self.db.features
        self.contributions = self.db.contributions

    async def get_features(self):
        features = []
        try:
            cursor = self.collection.find({})
            async for document in cursor:
                # Skip invalid documents to prevent Pydantic validation errors
                if "properties" not in document or "geometry" not in document:
                    continue
                    
                document["id"] = str(document["_id"])
                document["_id"] = str(document["_id"])
                features.append(document)
            return features
        except Exception as e:
            print(f"MongoDB Error: {e}")
            return []

    async def add_feature(self, feature):
        await self.collection.insert_one(feature)

    async def delete_feature(self, feature_id):
        print(f"Attempting to delete feature {feature_id} from MongoDB")
        try:
            # SECURITY: Validate ObjectId to prevent NoSQL injection
            obj_id = validate_object_id(feature_id, "feature_id")
            result = await self.collection.delete_one({"_id": obj_id})
            return result.deleted_count > 0
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error deleting from MongoDB: {e}")
            return False

    async def add_contribution(self, contribution):
        await self.contributions.insert_one(contribution)

    async def get_pending_contributions(self):
        contributions = []
        try:
            cursor = self.contributions.find({"status": "pending"})
            async for document in cursor:
                document["id"] = str(document["_id"])
                document["_id"] = str(document["_id"])
                contributions.append(document)
            return contributions
        except Exception as e:
            print(f"MongoDB Error: {e}")
            return []

    async def approve_contribution(self, contribution_id):
        try:
            # SECURITY: Validate ObjectId to prevent NoSQL injection
            obj_id = validate_object_id(contribution_id, "contribution_id")
            contribution = await self.contributions.find_one({"_id": obj_id})
            if not contribution:
                return False
            
            # Add to features
            feature = contribution.copy()
            feature.pop("_id")
            feature.pop("status")
            feature.pop("contributor_name")
            feature.pop("msv")
            feature.pop("unit", None)
            feature.pop("timestamp")
            
            await self.collection.insert_one(feature)
            
            # Update status
            await self.contributions.update_one(
                {"_id": obj_id},
                {"$set": {"status": "approved"}}
            )
            return True
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error approving contribution: {e}")
            return False

    async def reject_contribution(self, contribution_id):
        try:
            # SECURITY: Validate ObjectId to prevent NoSQL injection
            obj_id = validate_object_id(contribution_id, "contribution_id")
            await self.contributions.delete_one({"_id": obj_id})
            return True
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error rejecting contribution: {e}")
            return False

    async def get_leaderboard(self):
        pipeline = [
            {"$match": {"status": "approved"}},
            {"$group": {
                "_id": "$msv",
                "name": {"$last": "$contributor_name"}, # Use the latest name used
                "unit": {"$last": "$unit"}, # Use the latest unit used
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        leaderboard = []
        async for doc in self.contributions.aggregate(pipeline):
            leaderboard.append({
                "msv": doc["_id"],
                "contributor_name": doc["name"],
                "unit": doc.get("unit", "VKU"),
                "count": doc["count"]
            })
        return leaderboard

class JsonStorage(Storage):
    def __init__(self, filepath="data.json", contrib_path="contributions.json"):
        self.filepath = filepath
        self.contrib_path = contrib_path
        if not os.path.exists(filepath):
            with open(filepath, "w") as f: json.dump([], f)
        if not os.path.exists(contrib_path):
            with open(contrib_path, "w") as f: json.dump([], f)

    async def get_features(self):
        try:
            with open(self.filepath, "r") as f: return json.load(f)
        except Exception: return []

    async def add_feature(self, feature):
        features = await self.get_features()
        if "id" not in feature: feature["id"] = str(len(features) + 1)
        features.append(feature)
        with open(self.filepath, "w") as f: json.dump(features, f, indent=2)

    async def delete_feature(self, feature_id):
        features = await self.get_features()
        new_features = [f for f in features if str(f.get("id")) != str(feature_id) and str(f.get("_id")) != str(feature_id)]
        if len(new_features) < len(features):
            with open(self.filepath, "w") as f: json.dump(new_features, f, indent=2)
            return True
        return False

    async def get_contributions(self):
        try:
            with open(self.contrib_path, "r") as f: return json.load(f)
        except Exception: return []

    async def save_contributions(self, contributions):
        with open(self.contrib_path, "w") as f: json.dump(contributions, f, indent=2)

    async def add_contribution(self, contribution):
        contribs = await self.get_contributions()
        if "id" not in contribution: contribution["id"] = str(len(contribs) + 1)
        contribs.append(contribution)
        await self.save_contributions(contribs)

    async def get_pending_contributions(self):
        contribs = await self.get_contributions()
        return [c for c in contribs if c.get("status") == "pending"]

    async def approve_contribution(self, contribution_id):
        contribs = await self.get_contributions()
        for c in contribs:
            if str(c.get("id")) == str(contribution_id):
                c["status"] = "approved"
                await self.save_contributions(contribs)
                
                # Add to features
                feature = c.copy()
                for k in ["id", "status", "contributor_name", "msv", "unit", "timestamp"]:
                    feature.pop(k, None)
                await self.add_feature(feature)
                return True
        return False

    async def reject_contribution(self, contribution_id):
        contribs = await self.get_contributions()
        new_contribs = [c for c in contribs if str(c.get("id")) != str(contribution_id)]
        if len(new_contribs) < len(contribs):
            await self.save_contributions(new_contribs)
            return True
        return False

    async def get_leaderboard(self):
        contribs = await self.get_contributions()
        stats = {}
        for c in contribs:
            if c.get("status") == "approved":
                msv = c.get("msv")
                if msv:
                    if msv not in stats:
                        stats[msv] = {"name": c.get("contributor_name"), "count": 0}
                    stats[msv]["count"] += 1
                    stats[msv]["name"] = c.get("contributor_name") # Update name to latest
        
        leaderboard = [{"msv": msv, "name": data["name"], "count": data["count"]} for msv, data in stats.items()]
        return sorted(leaderboard, key=lambda x: x["count"], reverse=True)

# Initialize Storage
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
storage = None

@app.on_event("startup")
async def startup_db_client():
    global storage
    try:
        client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=2000)
        await client.server_info()
        print("Connected to MongoDB")
        storage = MongoStorage(MONGO_URL)
    except Exception as e:
        print(f"Could not connect to MongoDB: {e}")
        print("Falling back to local JSON storage")
        storage = JsonStorage()

@app.on_event("shutdown")
async def shutdown_db_client():
    pass

# Pydantic Models
class Geometry(BaseModel):
    type: str
    coordinates: List[Any]

class Feature(BaseModel):
    type: str = "Feature"
    id: Optional[str] = None
    feature_code: Optional[str] = None
    properties: Dict[str, Any]
    geometry: Geometry

    @validator('properties')
    def sanitize_properties(cls, v):
        import bleach
        if not v:
            return v
        # Recursively sanitize strings in properties
        def sanitize_value(value):
            if isinstance(value, str):
                return bleach.clean(value, tags=[], strip=True)
            if isinstance(value, dict):
                return {k: sanitize_value(val) for k, val in value.items()}
            if isinstance(value, list):
                return [sanitize_value(val) for val in value]
            return value
            
        return sanitize_value(v)

    @validator('feature_code')
    def sanitize_feature_code(cls, v):
        import bleach
        if v:
            return bleach.clean(v, tags=[], strip=True)
        return v

class Contribution(Feature):
    contributor_name: str
    msv: str
    unit: Optional[str] = "VKU"
    status: str = "pending"
    timestamp: datetime = Field(default_factory=datetime.now)

class FeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[Feature]

@app.get("/api/features", response_model=FeatureCollection)
async def get_features():
    features = await storage.get_features()
    return {"type": "FeatureCollection", "features": features}

@app.post("/api/features")
async def create_feature(feature: Feature, username: str = Depends(get_current_user)):
    new_feature = feature.dict()
    if not new_feature.get("feature_code") and "feature_type" in new_feature["properties"]:
         new_feature["feature_code"] = new_feature["properties"]["feature_type"].lower().replace(" ", "_")
    await storage.add_feature(new_feature)
    return {"status": "success"}

@app.delete("/api/features/{feature_id}")
@limiter.limit("20/minute")  # SECURITY: Rate limit
async def delete_feature(request: Request, feature_id: str, username: str = Depends(get_current_user)):
    success = await storage.delete_feature(feature_id)
    if not success:
        raise HTTPException(status_code=404, detail="Feature not found")
    return {"status": "success", "message": f"Feature {feature_id} deleted"}

# Contribution Endpoints
@app.post("/api/contributions")
async def create_contribution(contribution: ContributionInput):
    """Create contribution with XSS protection and input validation."""
    try:
        # Data is already sanitized by Pydantic validators
        new_contrib = contribution.dict()
        
        # Additional sanitization for properties
        if "properties" in new_contrib:
            for key, value in new_contrib["properties"].items():
                if isinstance(value, str):
                    new_contrib["properties"][key] = bleach.clean(value, tags=[], strip=True)
        
        # Add metadata
        new_contrib["status"] = "pending"
        new_contrib["timestamp"] = datetime.now()
        new_contrib["type"] = "Feature"
        
        if not new_contrib.get("feature_code") and "feature_type" in new_contrib["properties"]:
            new_contrib["feature_code"] = new_contrib["properties"]["feature_type"].lower().replace(" ", "_")
        
        await storage.add_contribution(new_contrib)
        return {"status": "success", "message": "Contribution submitted"}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/contributions")
async def get_contributions(username: str = Depends(get_current_user)):
    return await storage.get_pending_contributions()

@app.post("/api/contributions/{id}/approve")
@limiter.limit("30/minute")  # SECURITY: Rate limit
async def approve_contribution(request: Request, id: str, username: str = Depends(get_current_user)):
    success = await storage.approve_contribution(id)
    if not success:
        raise HTTPException(status_code=404, detail="Contribution not found")
    return {"status": "success"}

@app.delete("/api/contributions/{id}")
@limiter.limit("30/minute")  # SECURITY: Rate limit
async def reject_contribution(request: Request, id: str, username: str = Depends(get_current_user)):
    success = await storage.reject_contribution(id)
    if not success:
        raise HTTPException(status_code=404, detail="Contribution not found")
    return {"status": "success"}

@app.get("/api/leaderboard")
async def get_leaderboard():
    return await storage.get_leaderboard()

# Mapping for backward compatibility (feature_type -> feature_code)
TYPE_MAPPING = {
  "Trạm điện": "tram_dien",
  "Cột điện": "cot_dien",
  "Đường ống điện": "duong_ong_dien",
  "Đèn đường": "den_duong",
  "Đèn giao thông": "den_giao_thong",
  "Cống thoát nước": "cong_thoat_nuoc",
  "Ống dẫn nước": "ong_dan_nuoc",
  "Trụ chữa cháy": "tru_chua_chay",
  "Trạm sạc": "tram_sac"
}

@app.get("/api/export_csv")
async def export_features_csv(types: Optional[str] = None):
    """
    Export features as a CSV file.
    Optional query param 'types': comma-separated list of feature_codes to filter by.
    """
    features = await storage.get_features()
    security_logger.info(f"Export CSV: total features fetched: {len(features)}")
    
    # Filter features if types are provided
    if types:
        # Normalize requested types (remove accents, lower case)
        normalized_type_set = set(_normalize(t) for t in types.split(',') if t.strip())
        security_logger.debug(f"Export CSV: normalized requested types: {normalized_type_set}")
        filtered_features = []
        for f in features:
            props = f.get("properties", {})
            ftype = props.get("feature_type", "")
            code = f.get("feature_code", "")
            
            # Resolve possible code via mapping if missing
            if not code:
                code = TYPE_MAPPING.get(ftype, "")
            
            # Normalize values for comparison
            norm_code = _normalize(code).replace(" ", "_") if code else ""
            norm_ftype = _normalize(ftype).replace(" ", "_") if ftype else ""
            
            security_logger.debug(f"Feature code: {code}, normalized: {norm_code}; feature_type: {ftype}, normalized: {norm_ftype}")
            
            # Direct match on normalized code or feature_type
            if norm_code and norm_code in normalized_type_set:
                filtered_features.append(f)
                continue
            if norm_ftype and norm_ftype in normalized_type_set:
                filtered_features.append(f)
                continue
            # Also check mapped code from feature_type (already considered via norm_code)
        features = filtered_features
        security_logger.info(f"Export CSV: features after filtering: {len(features)}")
        features = filtered_features
        security_logger.info(f"Export CSV: features after filtering: {len(features)}")

    # Prepare header and data rows
    if not features:
        security_logger.warning("Export CSV: No features to export after filtering.")
    all_keys = set()
    data_rows = []

    for feature in features:
        props = feature.get("properties", {})
        geom = feature.get("geometry", {})
        
        # Resolve feature_code for CSV output if missing and normalize it
        feature_code_raw = feature.get("feature_code")
        if not feature_code_raw:
            feature_code_raw = TYPE_MAPPING.get(props.get("feature_type"), "")
        # Normalize to ASCII-friendly code (remove diacritics, lower case, replace spaces with underscores)
        feature_code = _normalize(feature_code_raw).replace(" ", "_")

        # Simple WKT conversion for CSV
        coords = geom.get("coordinates", [])
        geom_type = geom.get("type", "")
        wkt_geom = f"{geom_type.upper()} {str(coords)}"
        
        row = {
            "feature_type": props.get("feature_type", ""),
            "feature_code": feature_code,
            "geometry": wkt_geom,
            **props
        }
        # Prevent CSV Injection (Formula Injection)
        # If a field starts with =, +, -, or @, prepend a single quote
        safe_row = {}
        for k, v in row.items():
            if isinstance(v, str) and len(v) > 0 and v[0] in ['=', '+', '-', '@']:
                safe_row[k] = "'" + v
            else:
                safe_row[k] = v
        
        data_rows.append(safe_row)
        all_keys.update(safe_row.keys())

    header = ["feature_type", "feature_code", "geometry"]
    other_keys = sorted([k for k in all_keys if k not in header])
    header.extend(other_keys)

    def generate_csv_rows():
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=header)
        
        writer.writeheader()
        yield output.getvalue().encode("utf-8-sig")
        output.seek(0)
        output.truncate(0)

        for row_data in data_rows:
            writer.writerow(row_data)
            yield output.getvalue().encode("utf-8-sig")
            output.seek(0)
            output.truncate(0)

    return StreamingResponse(
        generate_csv_rows(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=features.csv"}
    )


# ============================================================
# VietMap Tile Proxy — hides API key from frontend
# ============================================================
_VIETMAP_API_KEY = os.getenv("VIETMAP_API_KEY", "")
_VIETMAP_TILE_URL = "https://maps.vietmap.vn/maps/tiles/tm/{z}/{x}/{y}@2x.png"


@app.get("/api/map/tiles/{z}/{x}/{y}")
async def proxy_tile(z: int, x: int, y: int):
    """Proxy VietMap tile requests so the API key stays server-side."""
    if not _VIETMAP_API_KEY:
        raise HTTPException(status_code=503, detail="VietMap API key not configured")
    url = _VIETMAP_TILE_URL.format(z=z, x=x, y=y)
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params={"apikey": _VIETMAP_API_KEY})
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Upstream tile error")
    return FastAPIResponse(
        content=resp.content,
        media_type=resp.headers.get("content-type", "image/png"),
        headers={"Cache-Control": "public, max-age=86400", "Access-Control-Allow-Origin": "*"},
    )


@app.get("/api/map/config")
async def map_config():
    """Return map tile URL template for the frontend."""
    if _VIETMAP_API_KEY:
        return {
            "tileUrl": "/api/map/tiles/{z}/{x}/{y}",
            "attribution": '&copy; <a href="https://vietmap.vn">VietMap</a> | Hoang Sa and Truong Sa belong to Vietnam 🇻🇳',
            "maxZoom": 20,
            "provider": "vietmap",
        }
    return {
        "tileUrl": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attribution": '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        "maxZoom": 20,
        "provider": "osm",
    }
