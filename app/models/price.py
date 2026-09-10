from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class PriceRecord:
	"""Representa um registro de preço no histórico temporal do produto."""

	product_id: int
	offer_id: int
	price: float
	source: str
	detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
	id: int | None = None

