from __future__ import annotations

import logging
from typing import Iterable

from app.models.offer import Offer

from .base import Source


logger = logging.getLogger(__name__)


def collect_from_sources(
	sources: Iterable[Source[Offer]],
	query: str,
) -> list[Offer]:
	# Coleta fontes independentes e mantém o pipeline vivo após uma falha.
	offers: list[Offer] = []
	for source in sources:
		logger.info("Consultando fonte: %s", source.name)
		try:
			source_offers = source.collect(query)
		except Exception:
			logger.exception("Fonte indisponível: %s", source.name)
			continue

		logger.info("Fonte %s retornou %s ofertas", source.name, len(source_offers))
		offers.extend(source_offers)

	return offers