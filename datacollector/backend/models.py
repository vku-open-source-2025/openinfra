from pydantic import BaseModel, root_validator, validator, constr
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserInDB(BaseModel):
    username: str
    hashed_password: str


class ContributionInput(BaseModel):
    """Contribution model with input validation to prevent XSS and DoS.

    Identity fields are optional so a contributor can submit anonymously. When
    both are absent (or ``anonymous`` is true) the record is stored with a
    non-identifying placeholder and is excluded from the leaderboard.
    """
    contributor_name: Optional[constr(min_length=1, max_length=100, strip_whitespace=True)] = None
    msv: Optional[constr(min_length=1, max_length=20, strip_whitespace=True)] = None
    unit: Optional[str] = "VKU"
    anonymous: bool = False
    properties: dict
    geometry: dict

    @root_validator(skip_on_failure=True)
    def normalize_identity(cls, values):
        anonymous = bool(values.get('anonymous'))
        name = (values.get('contributor_name') or '').strip()
        msv = (values.get('msv') or '').strip()
        if not name and not msv:
            anonymous = True
        if anonymous:
            values['anonymous'] = True
            values['contributor_name'] = 'Ẩn danh'
            values['msv'] = 'ANON'
            values['unit'] = 'Ẩn danh'
        else:
            if not name or not msv:
                raise ValueError('contributor_name and msv are required unless anonymous')
            values['anonymous'] = False
        return values
    
    @validator('properties')
    def validate_properties_size(cls, v):
        # Prevent DoS with huge payloads
        if len(str(v)) > 10000:  # Max 10KB
            raise ValueError('Properties payload too large (max 10KB)')
        return v
    
    @validator('contributor_name', 'msv', pre=True)
    def empty_identity_to_none(cls, v):
        # An empty input means "no identity supplied", not a validation error;
        # the root validator then marks the contribution anonymous.
        return v or None

    @validator('contributor_name', 'msv')
    def sanitize_html(cls, v):
        # Prevent XSS by removing HTML tags
        if not v:
            return v
        import bleach
        return bleach.clean(v, tags=[], strip=True)


class SOSReportInput(BaseModel):
    """SOS report payload for emergency intake in datacollector."""

    contributor_name: constr(min_length=1, max_length=100, strip_whitespace=True)
    msv: constr(min_length=1, max_length=20, strip_whitespace=True)
    unit: Optional[str] = "VKU"
    emergency_type: constr(min_length=2, max_length=50, strip_whitespace=True)
    severity: constr(min_length=3, max_length=20, strip_whitespace=True)
    message: constr(min_length=5, max_length=2000, strip_whitespace=True)
    district: Optional[constr(max_length=120, strip_whitespace=True)] = None
    ward: Optional[constr(max_length=120, strip_whitespace=True)] = None
    contact_phone: Optional[constr(max_length=30, strip_whitespace=True)] = None
    geometry: Optional[dict] = None

    @validator("severity")
    def validate_severity(cls, v):
        allowed = {"low", "medium", "high", "critical"}
        normalized = v.lower()
        if normalized not in allowed:
            raise ValueError("Severity must be one of: low, medium, high, critical")
        return normalized

    @validator("contributor_name", "msv", "unit", "emergency_type", "message", pre=True)
    def sanitize_text_fields(cls, v):
        if v is None:
            return v
        import bleach

        return bleach.clean(str(v), tags=[], strip=True)

    @validator("geometry")
    def validate_geometry_size(cls, v):
        if v and len(str(v)) > 5000:
            raise ValueError("Geometry payload too large (max 5KB)")
        return v
