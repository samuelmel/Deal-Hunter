from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True, slots=True)
class Settings:
	"""Configurações globais do Deal Hunter carregadas via variáveis de ambiente."""

	telegram_bot_token: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
	telegram_chat_id: str | None = os.getenv("TELEGRAM_CHAT_ID")
	default_query: str = os.getenv("DEAL_HUNTER_QUERY", "ssd 1tb")
	database_path: str = os.getenv("DATABASE_PATH", "data/deal_hunter.db")
	minimum_deal_score: int = int(os.getenv("MINIMUM_DEAL_SCORE", "70"))


settings = Settings()

