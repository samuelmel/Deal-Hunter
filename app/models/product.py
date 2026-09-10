from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class Product:
	"""Representa um produto único normalizado no catálogo."""

	normalized_name: str
	brand: str | None = None
	category: str | None = None
	id: int | None = None
	created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
	updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

