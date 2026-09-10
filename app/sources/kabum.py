from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models.offer import Offer
from app.scrapers.kabum import scrape_kabum


def _to_offer(product: dict[str, Any]) -> Offer:
	# Converte o dicionário legado do scraper para o modelo comum.
	return Offer(
		title=product["name"],
		price=product.get("price"),
		store=product.get("store", "KaBuM!"),
		url=product["url"],
		source="kabum",
		raw_data=product,
	)


@dataclass(slots=True)
class KabumSource:
	"""Adaptador da implementação atual da KaBuM para o contrato Source."""

	headless: bool = True
	max_scrolls: int = 50
	name: str = "kabum"

	def collect(self, query: str) -> list[Offer]:
		# Executa o scraper atual e entrega ofertas no formato compartilhado.
		products = scrape_kabum(
			query,
			limit=None,
			headless=self.headless,
			offers_only=True,
			max_scrolls=self.max_scrolls,
		)
		return [_to_offer(product) for product in products]