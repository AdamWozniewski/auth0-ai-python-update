# Auth0 AI for LangChain

This package integrates [LangChain](https://python.langchain.com/docs/tutorials/) with [Auth0 AI](https://www.auth0.ai/) for enhanced document retrieval capabilities.

## Installation

```bash
pip install langchain-auth0-ai
```

## Running Tests

1. **Install Dependencies**

   Use [Poetry](https://python-poetry.org/) to install the required dependencies:

   ```sh
   $ poetry install
   ```

2. **Run the tests**

   ```sh
   $ poetry run pytest tests
   ```

## Usage

```python
from langchain.vectorstores import VectorStoreIndex
from langchain.schema import Document
from langchain_auth0_ai import FGARetriever
from openfga_sdk.client.models import ClientCheckRequest
from openfga_sdk import ClientConfiguration
from openfga_sdk.credentials import CredentialConfiguration, Credentials

# Define some docs:
documents = [
    Document(page_content="This is a public doc", metadata={"doc_id": "public-doc"}),
    Document(page_content="This is a private doc", metadata={"doc_id": "private-doc"}),
]

# Create a vector store:
vector_store = VectorStoreIndex.from_documents(documents)

# Create a retriever:
base_retriever = vector_store.as_retriever()

# Create the FGA retriever wrapper:
retriever = FGARetriever(
    base_retriever,
    build_query=lambda node: ClientCheckRequest(
        user=f'user:{user}',
        object=f'doc:{node.metadata["doc_id"]}',
        relation="viewer",
    )
)

# Create a query engine:
query_engine = RetrieverQueryEngine.from_args(
    retriever=retriever,
    llm=OpenAI()
)

# Query:
response = query_engine.query("What is the forecast for ZEKO?")

print(response)
```

## License

Apache-2.0
