from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def scrape_amazon(query: str, limit: int | None = 20) -> list[dict[str, Any]]:
	"""Scraper stub para Amazon (recomenda-se o uso da API de Associados para acesso oficial)."""
	logger.warning("Scraper da Amazon inativo. Recomenda-se utilizar a API oficial de Associados.")
	return []

