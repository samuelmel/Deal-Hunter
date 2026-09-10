from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def scrape_mercadolivre(query: str, limit: int | None = 20) -> list[dict[str, Any]]:
	"""Scraper stub para Mercado Livre (recomenda-se o uso da API pública do Mercado Livre)."""
	logger.warning("Scraper do Mercado Livre inativo. Recomenda-se utilizar a API pública do Mercado Livre.")
	return []

