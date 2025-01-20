import os
from typing import Callable, Optional, List
from llama_index.core.retrievers import BaseRetriever
from pydantic import PrivateAttr
from openfga_sdk import ClientConfiguration, OpenFgaClient
from openfga_sdk.client.client import ClientBatchCheckRequest
from openfga_sdk.client.models import ClientBatchCheckItem
from openfga_sdk.sync import OpenFgaClient as OpenFgaClientSync
from openfga_sdk.credentials import CredentialConfiguration, Credentials

from llama_index.core.schema import (
    BaseNode,
    NodeWithScore,
    QueryBundle,
)


class FGARetriever(BaseRetriever):
    """
    FGARetriever integrates with OpenFGA to filter nodes based on fine-grained authorization (FGA).
    """

    _retriever: BaseRetriever = PrivateAttr()
    _fga_configuration: ClientConfiguration = PrivateAttr()
    _query_builder: Callable[[BaseNode], ClientBatchCheckItem] = PrivateAttr()

    def __init__(
        self,
        retriever: BaseRetriever,
        build_query: Callable[[BaseNode], ClientBatchCheckItem],
        fga_configuration: Optional[ClientConfiguration] = None,
    ):
        """
        Initialize the FGARetriever with the specified retriever, query builder, and configuration.

        Args:
            retriever (BaseRetriever): The retriever used to fetch nodes.
            build_query (Callable[[BaseNode], ClientBatchCheckItem]): Function to convert nodes into FGA queries.
            fga_configuration (Optional[ClientConfiguration]): Configuration for the OpenFGA client. If not provided, defaults to environment variables.
        """
        super().__init__()
        self._retriever = retriever
        self._fga_configuration = fga_configuration or ClientConfiguration(
            api_url=os.getenv("FGA_API_URL") or "https://api.us1.fga.dev",
            store_id=os.getenv("FGA_STORE_ID"),
            credentials=Credentials(
                method="client_credentials",
                configuration=CredentialConfiguration(
                    api_issuer=os.getenv("FGA_API_TOKEN_ISSUER") or "auth.fga.dev",
                    api_audience=os.getenv("FGA_API_AUDIENCE")
                    or "https://api.us1.fga.dev/",
                    client_id=os.getenv("FGA_CLIENT_ID"),
                    client_secret=os.getenv("FGA_CLIENT_SECRET"),
                ),
            ),
        )
        self._query_builder = build_query

    def _filter_FGA(self, nodes: list[NodeWithScore]) -> List[NodeWithScore]:
        """
        Synchronously filter nodes using OpenFGA.

        Args:
            nodes (List[NodeWithScore]): List of nodes to filter.

        Returns:
            List[NodeWithScore]: Filtered list of nodes authorized by FGA.
        """
        with OpenFgaClientSync(self._fga_configuration) as fga_client:
            checks = [
                self._query_builder(nodeWithScore.node) for nodeWithScore in nodes
            ]
            obj_to_node = {
                check.object: nodeWithScore
                for check, nodeWithScore in zip(checks, nodes)
            }
            fga_response = fga_client.batch_check(
                ClientBatchCheckRequest(checks=checks)
            )

            return [
                obj_to_node[result.request.object]
                for result in fga_response.result
                if result.allowed
            ]

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Retrieve nodes given query and filtered by FGA access."""
        nodes = self._retriever._retrieve(query_bundle)
        nodes = self._filter_FGA(nodes)
        return nodes

    async def _async_filter_FGA(
        self, nodes: list[NodeWithScore]
    ) -> List[NodeWithScore]:
        async with OpenFgaClient(self._fga_configuration) as fga_client:
            checks = [
                self._query_builder(nodeWithScore.node) for nodeWithScore in nodes
            ]
            obj_to_node = {
                check.object: nodeWithScore
                for check, nodeWithScore in zip(checks, nodes)
            }
            fga_response = await fga_client.batch_check(
                ClientBatchCheckRequest(checks=checks)
            )
            await fga_client.close()

            return [
                obj_to_node[result.request.object]
                for result in fga_response.result
                if result.allowed
            ]

    async def _aretrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Retrieve nodes given query and filtered by FGA access."""
        nodes = await self._retriever._aretrieve(query_bundle)
        nodes = await self._async_filter_FGA(nodes)
        return nodes
