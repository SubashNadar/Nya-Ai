"""Vector store, docstore and embedding model, built once from settings."""

from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.storage.docstore.postgres import PostgresDocumentStore
from llama_index.storage.kvstore.postgres import PostgresKVStore
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy.engine import make_url

from app.core.config import get_settings

# PGVectorStore prefixes "data_", so the vectors live in `data_law_sections`.
SECTIONS_TABLE = "law_sections"


def _urls(url: str | None) -> tuple[str, str]:
    """Sync and async URLs for LlamaIndex. The sync side uses psycopg2: PGVectorStore sends
    `SET hnsw.ef_search` with a bound parameter, which psycopg 3's server-side binding rejects."""
    u = make_url(url or get_settings().VECTOR_DATABASE_URL)
    return (
        u.set(drivername="postgresql+psycopg2").render_as_string(hide_password=False),
        u.set(drivername="postgresql+asyncpg").render_as_string(hide_password=False),
    )


def vector_store(url: str | None = None) -> PGVectorStore:
    sync, async_ = _urls(url)
    return PGVectorStore.from_params(
        connection_string=sync,
        async_connection_string=async_,
        table_name=SECTIONS_TABLE,
        embed_dim=get_settings().EMBED_DIM,
        hybrid_search=True,  # adds a tsvector column so BM25-style text search runs in Postgres
        text_search_config="english",
        hnsw_kwargs={
            "hnsw_m": 16,
            "hnsw_ef_construction": 64,
            "hnsw_ef_search": 40,
            "hnsw_dist_method": "vector_cosine_ops",
        },
    )


def docstore(url: str | None = None) -> PostgresDocumentStore:
    sync, _ = _urls(url)
    # Built from the kvstore directly: PostgresDocumentStore.from_uri in docstore-postgres 0.6.0
    # passes an argument that kvstore-postgres 0.4.x does not accept.
    return PostgresDocumentStore(PostgresKVStore.from_uri(sync, table_name="law_docstore"), namespace="law")


def embed_model() -> BaseEmbedding:
    s = get_settings()
    if not (s.AZURE_OPENAI_ENDPOINT and s.AZURE_OPENAI_API_KEY):
        raise RuntimeError(
            "Azure OpenAI is not configured. Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in backend/.env."
        )
    from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding

    return AzureOpenAIEmbedding(
        model="text-embedding-3-large",
        azure_deployment=s.AZURE_EMBED_DEPLOYMENT,
        azure_endpoint=s.AZURE_OPENAI_ENDPOINT,
        api_key=s.AZURE_OPENAI_API_KEY,
        api_version=s.AZURE_OPENAI_API_VERSION,
        dimensions=s.EMBED_DIM,
        embed_batch_size=64,
    )
