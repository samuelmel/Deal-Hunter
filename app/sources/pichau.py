from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.models.offer import Offer
from app.scrapers.pichau import scrape_pichau


logger = logging.getLogger(__name__)


def _to_offer(product: dict[str, Any]) -> Offer:
	return Offer(
		title=product["name"],
		price=product.get("price"),
		store=product.get("store", "Pichau"),
		url=product["url"],
		source="pichau",
		old_price=product.get("old_price"),
		discount=product.get("discount"),
		stock=product.get("stock"),
		raw_data=product,
	)


@dataclass(slots=True)
class PichauSource:
	"""Adaptador resiliente para Pichau, tratando bloqueios sem tentar evasão."""

	headless: bool = True
	limit: int | None = 20
	name: str = "pichau"

	def collect(self, query: str) -> list[Offer]:
		# Executa a coleta com captura total de erros para isolar falhas de anti-bot.
		try:
			products = scrape_pichau(query, limit=self.limit, headless=self.headless)
			return [_to_offer(p) for p in products]
		except Exception as exc:
			logger.warning("Fonte Pichau indisponível: %s", exc)
			return []

