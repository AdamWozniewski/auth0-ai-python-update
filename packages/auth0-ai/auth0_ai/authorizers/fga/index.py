from __future__ import annotations
from typing import Any, Awaitable, Callable, Optional, Protocol
from openfga_sdk.client.client import ClientCheckRequest
from openfga_sdk import OpenFgaClient
from .client import build_openfga_client, FGAClientParams

class FGABuildQuery(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> Awaitable[ClientCheckRequest]: ...

class FGAAuthorizerBase:
    def __init__(self, fga_client_params: Optional[FGAClientParams], build_query: FGABuildQuery, on_unauthorized: Optional[Callable[..., Any]] = None):
        self._client: OpenFgaClient = build_openfga_client(fga_client_params)
        self._build_query = build_query
        self._on_unauthorized = on_unauthorized

    def protect(self, execute: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        async def wrapped(*args: Any, **kwargs: Any) -> Any:
            check_req = await self._build_query(*args, **kwargs)
            res = await self._client.check(check_req)
            if not res.allowed:
                if callable(self._on_unauthorized):
                    return self._on_unauthorized(*args, **kwargs)
                return "The user is not allowed to perform the action."
            return await execute(*args, **kwargs)
        return wrapped
