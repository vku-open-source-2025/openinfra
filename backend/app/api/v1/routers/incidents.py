"""Incidents API router."""
import json
import logging
from datetime import datetime
from fastapi import APIRouter, Query, Depends, HTTPException, status, UploadFile, File, Form, Header, Request, BackgroundTasks, Body
from typing import List, Optional
from app.domain.models.incident import (
    Incident, IncidentCreate, IncidentUpdate, IncidentCommentRequest
)
from app.domain.models.merge_suggestion import MergeSuggestion, MergeSuggestionStatus, MergeRequest
from app.domain.services.incident_service import IncidentService
from app.api.v1.dependencies import get_incident_service, get_storage_service
from app.api.v1.middleware import get_current_user, get_optional_current_user
from app.domain.models.user import User, UserRole
from app.domain.models.incident import ResolutionType
from app.infrastructure.storage.storage_service import StorageService
from app.infrastructure.services.turnstile_service import turnstile_service
from app.core.config import settings
from app.services.ai_verification_service import get_verification_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=List[Incident])
async def list_incidents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    asset_id: Optional[str] = None,
    verification_status: Optional[str] = Query(None, description="Filter by AI verification status: pending, verified, to_be_verified, failed"),
    incident_service: IncidentService = Depends(get_incident_service)
):
    """List incidents with filtering, including asset information."""
    return await incident_service.list_incidents(
        skip, limit, status, severity, asset_id, None, 
        populate_asset=True, verification_status=verification_status
    )


@router.post("", response_model=Incident, status_code=status.HTTP_201_CREATED)
async def create_incident(
    request: Request,
    background_tasks: BackgroundTasks,
    data: str = Form(...),
    image: Optional[UploadFile] = File(None),
    cf_turnstile_response: Optional[str] = Header(None, alias="CF-Turnstile-Response"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    incident_service: IncidentService = Depends(get_incident_service),
    storage_service: StorageService = Depends(get_storage_service)
):
    """Create a new incident (can be anonymous) with REQUIRED image upload."""
    # Image is required for anonymous users (public reports)
    if not current_user and not image:
        raise HTTPException(
            status_code=400,
            detail="Image upload is required for incident reports"
        )
    
    # Verify Cloudflare Turnstile captcha for anonymous users
    if not current_user and settings.TURNSTILE_SECRET_KEY:
        if not cf_turnstile_response:
            raise HTTPException(
                status_code=400,
                detail="Captcha verification required"
            )
        
        # Get client IP from request
        client_ip = request.client.host if request.client else None
        
        # Verify token
        is_valid = await turnstile_service.verify_token(cf_turnstile_response, client_ip)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail="Captcha verification failed"
            )
    
    try:
        incident_dict = json.loads(data)
        
        # Map contact_info to reporter_contact if provided
        if "contact_info" in incident_dict:
            contact_info = incident_dict.pop("contact_info")
            incident_dict["reporter_contact"] = {
                "name": contact_info.get("name"),
                "phone": contact_info.get("phone_number"),
                "id_card_number": contact_info.get("id_card_number")
            }
        
        incident_data = IncidentCreate(**incident_dict)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid incident data: {str(e)}")
    
    # Handle image upload
    photos = list(incident_data.photos)
    image_url = None
    if image:
        try:
            image_url = await storage_service.upload_file(
                file=image,
                bucket="incidents"
            )
            photos.append(image_url)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")
    
    # Update photos in incident data
    incident_data = IncidentCreate(
        **{**incident_data.model_dump(), "photos": photos}
    )
    
    reported_by = str(current_user.id) if current_user else None
    reporter_type = current_user.role.value if current_user else "citizen"
    incident = await incident_service.create_incident(incident_data, reported_by, reporter_type)
    
    # Run AI verification in background
    if image_url or photos:
        background_tasks.add_task(
            run_ai_verification,
            incident_id=str(incident.id),
            title=incident.title,
            description=incident.description,
            category=incident.category.value,
            severity=incident.severity.value,
            asset_type=incident.asset.feature_type if incident.asset else None,
            asset_name=incident.asset.name if incident.asset else None,
            image_url=image_url or (photos[0] if photos else None),
            incident_service=incident_service
        )
    
    return incident


async def run_ai_verification(
    incident_id: str,
    title: str,
    description: str,
    category: str,
    severity: str,
    asset_type: Optional[str],
    asset_name: Optional[str],
    image_url: Optional[str],
    incident_service: IncidentService
) -> None:
    """Background task to run AI verification on an incident."""
    try:
        verification_service = get_verification_service()
        result = await verification_service.verify_incident_report(
            incident_title=title,
            incident_description=description,
            incident_category=category,
            incident_severity=severity,
            asset_type=asset_type,
            asset_name=asset_name,
            image_url=image_url
        )
        
        # Update incident with verification result
        await incident_service.update_verification(
            incident_id,
            verification_status=result["verification_status"],
            confidence_score=result["confidence_score"],
            verification_reason=result["reason"]
        )
        
        logger.info(f"AI verification completed for incident {incident_id}: {result['verification_status']}")
        
    except Exception as e:
        logger.error(f"AI verification failed for incident {incident_id}: {e}")
        # Update with failed status
        try:
            await incident_service.update_verification(
                incident_id,
                verification_status="failed",
                confidence_score=None,
                verification_reason=f"Verification error: {str(e)}"
            )
        except Exception as update_error:
            logger.error(f"Failed to update verification status: {update_error}")


@router.get("/{incident_id}", response_model=Incident)
async def get_incident(
    incident_id: str,
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Get incident details."""
    return await incident_service.get_incident_by_id(incident_id)


@router.put("/{incident_id}", response_model=Incident)
async def update_incident(
    incident_id: str,
    updates: IncidentUpdate,
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Update incident."""
    return await incident_service.update_incident(incident_id, updates)


@router.post("/{incident_id}/acknowledge", response_model=Incident)
async def acknowledge_incident(
    incident_id: str,
    current_user: User = Depends(get_current_user),
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Acknowledge an incident."""
    return await incident_service.acknowledge_incident(incident_id, str(current_user.id))


@router.post("/{incident_id}/assign", response_model=Incident)
async def assign_incident(
    incident_id: str,
    assigned_to: str = Query(..., description="User ID to assign to"),
    current_user: User = Depends(get_current_user),
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Assign incident to a technician."""
    return await incident_service.assign_incident(incident_id, assigned_to, str(current_user.id))


@router.post("/{incident_id}/resolve", response_model=Incident)
async def resolve_incident(
    incident_id: str,
    resolution_notes: str = Query(..., description="Resolution notes"),
    resolution_type: ResolutionType = Query(..., description="Resolution type"),
    current_user: User = Depends(get_current_user),
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Resolve an incident."""
    return await incident_service.resolve_incident(
        incident_id,
        str(current_user.id),
        resolution_notes,
        resolution_type
    )


@router.post("/{incident_id}/comments", response_model=Incident)
async def add_comment(
    incident_id: str,
    comment: IncidentCommentRequest,
    current_user: Optional[User] = Depends(get_current_user),
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Add comment to incident."""
    user_id = str(current_user.id) if current_user else None
    return await incident_service.add_comment(
        incident_id,
        comment.comment,
        user_id,
        comment.is_internal
    )


@router.post("/{incident_id}/upvote", response_model=Incident)
async def upvote_incident(
    incident_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Upvote or remove upvote from incident."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return await incident_service.upvote_incident(incident_id, str(current_user.id))


@router.post("/{incident_id}/create-maintenance", response_model=dict)
async def create_maintenance_from_incident(
    incident_id: str,
    current_user: User = Depends(get_current_user),
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Create a maintenance work order from incident."""
    maintenance_id = await incident_service.create_maintenance_from_incident(
        incident_id,
        str(current_user.id)
    )
    return {
        "incident_id": incident_id,
        "maintenance_id": maintenance_id,
        "message": "Maintenance work order created successfully"
    }


@router.post("/{incident_id}/approve-cost", response_model=Incident)
async def approve_incident_cost(
    incident_id: str,
    current_user: User = Depends(get_current_user),
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Approve maintenance cost and resolve incident."""
    # In a real app, check for ADMIN role here
    return await incident_service.approve_incident_resolution(
        incident_id,
        str(current_user.id)
    )


@router.post("/{incident_id}/close", response_model=Incident)
async def close_incident(
    incident_id: str,
    notes: str = Query(None, description="Optional closing notes"),
    current_user: User = Depends(get_current_user),
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Close a resolved incident."""
    return await incident_service.close_incident(
        incident_id,
        str(current_user.id),
        notes
    )


@router.post("/{incident_id}/reject", response_model=Incident)
async def reject_incident(
    incident_id: str,
    reason: str = Query(..., description="Reason for rejection"),
    current_user: User = Depends(get_current_user),
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Reject an incident as invalid or spam."""
    return await incident_service.reject_incident(
        incident_id,
        str(current_user.id),
        reason
    )


@router.post("/{incident_id}/verify", response_model=Incident)
async def verify_incident(
    incident_id: str,
    current_user: User = Depends(get_current_user),
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Manually verify an incident (human verification)."""
    return await incident_service.manual_verify_incident(
        incident_id,
        str(current_user.id)
    )


@router.post("/{incident_id}/check-duplicates", response_model=List[dict])
async def check_duplicates(
    incident_id: str,
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Manually trigger duplicate detection for an incident."""
    duplicates = await incident_service.check_duplicates(incident_id)
    return [dup.dict() for dup in duplicates]


@router.get("/{incident_id}/merge-suggestions", response_model=List[MergeSuggestion])
async def get_merge_suggestions(
    incident_id: str,
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected"),
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Get merge suggestions for an incident."""
    suggestion_status = None
    if status:
        try:
            suggestion_status = MergeSuggestionStatus(status.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    suggestions = await incident_service.get_merge_suggestions(incident_id, suggestion_status)
    return suggestions


@router.post("/{incident_id}/merge", response_model=Incident)
async def merge_incidents(
    incident_id: str,
    merge_request: MergeRequest = Body(...),
    current_user: User = Depends(get_current_user),
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Merge incidents (requires admin/technician role)."""
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.TECHNICIAN]:
        raise HTTPException(
            status_code=403,
            detail="Only admins and technicians can merge incidents"
        )
    
    # Input validation
    if not merge_request.duplicate_ids:
        raise HTTPException(status_code=400, detail="At least one duplicate ID is required")
    if len(merge_request.duplicate_ids) > 10:
        raise HTTPException(status_code=400, detail="Cannot merge more than 10 incidents at once")
    if incident_id in merge_request.duplicate_ids:
        raise HTTPException(status_code=400, detail="Primary incident cannot be in duplicate list")
    
    try:
        return await incident_service.merge_incidents(
            primary_id=incident_id,
            duplicate_ids=merge_request.duplicate_ids,
            merged_by=str(current_user.id),
            merge_notes=merge_request.merge_notes
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error merging incidents: {str(e)}")


@router.post("/merge-suggestions/{suggestion_id}/approve", response_model=Incident)
async def approve_merge_suggestion(
    suggestion_id: str,
    current_user: User = Depends(get_current_user),
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Approve a merge suggestion (requires admin/technician role)."""
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.TECHNICIAN]:
        raise HTTPException(
            status_code=403,
            detail="Only admins and technicians can approve merge suggestions"
        )
    
    return await incident_service.approve_merge(suggestion_id, str(current_user.id))


@router.post("/merge-suggestions/{suggestion_id}/reject", response_model=dict)
async def reject_merge_suggestion(
    suggestion_id: str,
    review_notes: Optional[str] = Body(None, embed=True),
    current_user: User = Depends(get_current_user),
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Reject a merge suggestion (requires admin/technician role)."""
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.TECHNICIAN]:
        raise HTTPException(
            status_code=403,
            detail="Only admins and technicians can reject merge suggestions"
        )
    
    success = await incident_service.reject_merge(suggestion_id, str(current_user.id), review_notes)
    if not success:
        raise HTTPException(status_code=404, detail="Merge suggestion not found")
    
    return {"message": "Merge suggestion rejected successfully"}
