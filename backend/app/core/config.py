"""Backend settings for the API and the agent, read from the environment or `backend/.env`.

Keys are never committed.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "sqlite:///./nya_ai.db"

    # Dev-only default; override in production. Any value is fine since this is a
    # demo/hackathon-grade JWT secret, not a production credential store.
    JWT_SECRET: str = "dev-only-nya-ai-jwt-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    # 24 hours: shortened from the original 7-day default per the user's resolution
    # pass (docs/DECISIONS.md, "Resolution pass with user, 2026-07-18",
    # #9) — paired with real server-side logout invalidation (RevokedToken) since a
    # shorter expiry alone doesn't make logout take effect immediately.
    JWT_EXPIRE_MINUTES: int = 60 * 24

    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_MODEL: str = "claude-sonnet-5"

    # Razorpay test-mode credentials. When unset, payment endpoints return 503 at
    # request time — the rest of the app (free chat, lawyers, dashboard) still boots
    # and works with zero config. See docs/DECISIONS.md "Real Razorpay
    # integration" entry.
    RAZORPAY_KEY_ID: str | None = None
    RAZORPAY_KEY_SECRET: str | None = None
    RAZORPAY_WEBHOOK_SECRET: str | None = None

    CORS_ORIGINS: str = "http://localhost:5173"

    # Law library: Postgres with pgvector, from docker-compose.yml.
    VECTOR_DATABASE_URL: str = "postgresql+psycopg://nya:nya@localhost:5433/nya"

    # Azure OpenAI (personal subscription). Embeddings use text-embedding-3-large cut to 1536 dims.
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-10-21"
    AZURE_EMBED_DEPLOYMENT: str = "text-embedding-3-large"
    AZURE_SMALL_DEPLOYMENT: str = "gpt-5.4-nano"  # router, safety classifier
    AZURE_STRONG_DEPLOYMENT: str = "gpt-5.4"  # answers, critic, LLM judge, Ragas
    EMBED_DIM: int = 1536
    # Prices in USD per 1M tokens, for cost tracking in Langfuse. 0 means "not set": usage is still
    # recorded, cost shows 0. Copy the numbers from your Azure OpenAI pricing page for your region.
    PRICE_STRONG_INPUT_PER_1M: float = 0.0
    PRICE_STRONG_OUTPUT_PER_1M: float = 0.0
    PRICE_SMALL_INPUT_PER_1M: float = 0.0
    PRICE_SMALL_OUTPUT_PER_1M: float = 0.0
    PRICE_EMBED_INPUT_PER_1M: float = 0.0

    # R1 agent graph. When disabled, or when the law library is not reachable, chat falls back to the
    # rule engine ("basic mode"). Checkpoints let an answer held for advocate review resume later.
    AGENT_ENABLED: bool = True
    CHECKPOINT_DB: str = "./nya_graph.db"  # SQLite fallback when CHECKPOINT_DATABASE_URL is empty or down
    # Postgres for checkpoints (docs/MEMORY.md), e.g. the law library database. Empty means SQLite.
    CHECKPOINT_DATABASE_URL: str = ""
    # Law tools through the MCP server (app/agents/mcp_server.py) instead of direct calls. Off by default:
    # same results, extra latency. MCP_SERVER_URL = streamable HTTP endpoint; empty = stdio subprocess.
    TOOLS_VIA_MCP: bool = False
    MCP_SERVER_URL: str = ""

    # Self-hosted Langfuse from docker-compose.yml (http://localhost:3000).
    LANGFUSE_HOST: str = "http://localhost:3000"
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def razorpay_configured(self) -> bool:
        return bool(self.RAZORPAY_KEY_ID and self.RAZORPAY_KEY_SECRET)


@lru_cache
def get_settings() -> Settings:
    return Settings()
