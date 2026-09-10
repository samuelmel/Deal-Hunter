"""Interfaces e adaptadores das fontes de ofertas."""

from app.sources.base import Source
from app.sources.kabum import KabumSource
from app.sources.pelando import PelandoSource
from app.sources.pichau import PichauSource
from app.sources.promobit import PromobitSource
from app.sources.terabyte import TerabyteSource

__all__ = [
	"Source",
	"KabumSource",
	"PelandoSource",
	"PichauSource",
	"PromobitSource",
	"TerabyteSource",
]