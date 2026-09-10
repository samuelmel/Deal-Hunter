from __future__ import annotations

from typing import Protocol, TypeVar


OfferT = TypeVar("OfferT", covariant=True)


class Source(Protocol[OfferT]):
	"""Contrato mínimo que toda fonte de ofertas deve seguir."""

	name: str

	def collect(self, query: str) -> list[OfferT]:
		# Coleta dados brutos da fonte para posterior normalização.
		...