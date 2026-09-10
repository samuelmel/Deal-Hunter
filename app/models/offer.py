from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class Offer:
	"""Representa uma oferta independente da fonte que a forneceu."""

	title: str
	price: float | None
	store: str
	url: str
	source: str
	old_price: float | None = None
	discount: str | None = None
	coupon: str | None = None
	seller: str | None = None
	stock: str | None = None
	detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
	raw_data: dict[str, Any] = field(default_factory=dict)