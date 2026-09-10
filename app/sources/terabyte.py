from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.models.offer import Offer
from app.scrapers.terabyte import scrape_terabyte


logger = logging.getLogger(__name__)


def _to_offer(product: dict[str, Any]) -> Offer:
	return Offer(
		title=product["name"],
		price=product.get("price"),
		store=product.get("store", "Terabyte Shop"),
		url=product["url"],
		source="terabyte",
		old_price=product.get("old_price"),
		discount=product.get("discount"),
		stock=str(product.get("stock")) if product.get("stock") is not None else None,
		raw_data=product,
	)


@dataclass(slots=True)
class TerabyteSource:
	"""Adaptador resiliente para Terabyte Shop, tratando bloqueios com fallback limpo."""

	headless: bool = True
	limit: int | None = 20
	name: str = "terabyte"

	def collect(self, query: str) -> list[Offer]:
		# Executa a coleta com tratamento de erro gracioso e busca flexível.
		try:
			products = scrape_terabyte(
				query,
				limit=self.limit,
				headless=self.headless,
				promotions_only=False,
				in_stock_only=False,
			)
			return [_to_offer(p) for p in products]
		except Exception as exc:
			logger.warning("Fonte Terabyte indisponível: %s", exc)
			return []

