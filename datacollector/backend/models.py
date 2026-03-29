from pydantic import BaseModel, validator, constr
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
    """Contribution model with input validation to prevent XSS and DoS."""
    contributor_name: constr(min_length=1, max_length=100, strip_whitespace=True)
    msv: constr(min_length=1, max_length=20, strip_whitespace=True)
    unit: Optional[str] = "VKU"
    properties: dict
    geometry: dict
    
    @validator('properties')
    def validate_properties_size(cls, v):
        # Prevent DoS with huge payloads
        if len(str(v)) > 10000:  # Max 10KB
            raise ValueError('Properties payload too large (max 10KB)')
        return v
    
    @validator('contributor_name', 'msv')
    def sanitize_html(cls, v):
        # Prevent XSS by removing HTML tags
        import bleach
        return bleach.clean(v, tags=[], strip=True)
