from __future__ import annotations
import os
from typing import Optional, TypedDict
from openfga_sdk import ClientConfiguration, OpenFgaClient
from openfga_sdk.credentials import CredentialConfiguration, Credentials

class FGAClientParams(TypedDict, total=False):
    api_url: str
    store_id: str
    credentials: Dict[str, object]

def build_openfga_client(fga_client_params: Optional[FGAClientParams] = None) -> OpenFgaClient:
    cfg = ClientConfiguration(
        api_url=(fga_client_params or {}).get("api_url") or os.getenv("FGA_API_URL") or "https://api.us1.fga.dev",
        store_id=(fga_client_params or {}).get("store_id") or os.getenv("FGA_STORE_ID"),
        credentials=Credentials(
            method="client_credentials",
            configuration=CredentialConfiguration(
                api_issuer=os.getenv("FGA_API_TOKEN_ISSUER") or "auth.fga.dev",
                api_audience=os.getenv("FGA_API_AUDIENCE") or "https://api.us1.fga.dev/",
                client_id=os.getenv("FGA_CLIENT_ID"),
                client_secret=os.getenv("FGA_CLIENT_SECRET"),
            ),
        ),
    )
    return OpenFgaClient(cfg)
