from __future__ import annotations
from typing import Any, Callable, Dict, Generic, List, Mapping, TypeVar, Optional
from openfga_sdk.client.client import ClientBatchCheckRequest
from openfga_sdk.client.models import ClientBatchCheckItem
from .client import build_openfga_client, FGAClientParams

T = TypeVar("T", bound=Mapping[str, Any])

FGAFilterCheckerFn = Callable[[T], ClientBatchCheckItem]

class FGAFilter(Generic[T]):
    def __init__(self, build_query: FGAFilterCheckerFn, fga_client_params: Optional[FGAClientParams] = None):
        self._build_query = build_query
        self._client_params = fga_client_params

    @staticmethod
    def create(build_query: FGAFilterCheckerFn, fga_client_params: Optional[FGAClientParams] = None) -> "FGAFilter":
        return FGAFilter(build_query, fga_client_params)

    async def filter(self, documents: List[T]) -> List[T]:
        checks: List[ClientBatchCheckItem] = []
        seen: set[str] = set()
        doc_to_key: Dict[int, str] = {}

        for doc in documents:
            check = self._build_query(doc)
            key = self._check_key(check)
            doc_to_key[id(doc)] = key
            if key not in seen:
                seen.add(key)
                checks.append(check)

        if not checks:
            return []

        async with build_openfga_client(self._client_params) as client:
            resp = await client.batch_check(ClientBatchCheckRequest(checks=checks))
            await client.close()

        permissions: Dict[str, bool] = {r.request.object: bool(r.allowed) for r in resp.result}
        allowed_by_key: Dict[str, bool] = {}
        for r in resp.result:
            allowed_by_key[self._check_key(r.request)] = bool(r.allowed)

        return [d for d in documents if allowed_by_key.get(doc_to_key[id(d)], False)]

    @staticmethod
    def _check_key(check: ClientBatchCheckItem) -> str:
        return f"{check.user}|{check.object}|{check.relation}"
