from typing import TypedDict, Optional, List
from pydantic import BaseModel

class AuthorizationDetails(BaseModel):
    type: str
    class Config:
        extra = 'allow'
        allow_mutation = False

class TokenResponse(TypedDict):
    access_token: str
    expires_in: int
    scope: list[str]
    token_type: Optional[str]
    id_token: Optional[str]
    refresh_token: Optional[str]
    authorization_details: Optional[List[AuthorizationDetails]]
