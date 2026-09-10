from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from app.database.connection import get_connection
from app.database.repositories import (
	migrate_legacy_observations,
	get_latest_price,
	save_classifications,
	save_offer_history,
)
from app.models.offer import Offer
from app.services.classifier import classify_title
from app.services.deal_scorer import calculate_deal_score
from app.services.normalizer import normalize_offer
from app.services.price_analyzer import analyze_price
from app.services.notification_rules import should_notify
from app.sources.base import Source
from app.sources.collection import collect_from_sources


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PipelineResult:
	# Resume uma execução sem expor detalhes da fonte ao chamador.
	query: str
	collected: int
	normalized: int
	saved: int
	classified: int
	opportunities: int
	items: tuple[PipelineItem, ...]


@dataclass(frozen=True, slots=True)
class PipelineItem:
	# Reúne oferta, análise e decisão de notificação.
	offer: Offer
	analysis: object
	deal_score: int
	notify: bool


def run_pipeline(
	sources: Iterable[Source[Offer]],
	query: str,
	database_path: str | Path = "data/deal_hunter.db",
	connection: sqlite3.Connection | None = None,
) -> PipelineResult:
	# Executa coleta, normalização, classificação e persistência histórica.
	logger.info("Iniciando coleta de fontes para: %s", query)
	offers = collect_from_sources(sources, query)
	normalized_offers = [normalize_offer(offer) for offer in offers]
	logger.info("Normalização concluída: %s ofertas", len(normalized_offers))

	managed_connection = connection is None
	database = connection or get_connection(database_path)
	try:
		migrate_legacy_observations(database)
		previous_prices = {
			offer.url: get_latest_price(database, offer.url, offer.source)
			for offer in normalized_offers
		}
		saved = save_offer_history(database, normalized_offers)
		classified = save_classifications(database, normalized_offers)
		opportunities = 0
		items: list[PipelineItem] = []
		for offer in normalized_offers:
			if offer.price is None:
				continue
			history = database.execute(
				"""
				SELECT ph.price
				FROM price_history AS ph
				JOIN products AS p ON p.id = ph.product_id
				WHERE p.normalized_name = ?
				""",
				(normalize_offer(offer).title,),
			).fetchall()
			analysis = analyze_price(offer.price, [row["price"] for row in history])
			deal_score = calculate_deal_score(analysis, has_coupon=bool(offer.coupon))
			if deal_score >= 70:
				opportunities += 1
			items.append(
				PipelineItem(
					offer,
					analysis,
					deal_score,
					should_notify(offer.price, previous_prices[offer.url], deal_score),
				)
			)
		return PipelineResult(query, len(offers), len(normalized_offers), saved, classified, opportunities, tuple(items))
	finally:
		if managed_connection:
			database.close()