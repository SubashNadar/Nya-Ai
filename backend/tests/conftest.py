"""Tests never use the real Azure key or Langfuse from `backend/.env`.

Environment variables win over `.env` in pydantic-settings, so blanking them here (before any settings
are read) keeps the suite offline and identical on every machine. Tests that need Azure or Langfuse
behaviour use fakes.
"""

import os

for _name in ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"):
    os.environ[_name] = ""
