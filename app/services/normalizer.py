from __future__ import annotations

import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit

from app.models.offer import Offer


def normalize_text(value: str) -> str:
	# Remove acentos, espaços repetidos e variações de capitalização.
	without_accents = "".join(
		character
		for character in unicodedata.normalize("NFKD", value)
		if not unicodedata.combining(character)
	)
	return re.sub(r"\s+", " ", without_accents).strip().lower()


def normalize_store(store: str) -> str:
	# Padroniza o nome da loja para facilitar agrupamentos no banco.
	return normalize_text(store).replace("kabum!", "kabum")


def normalize_url(url: str) -> str:
	# Remove fragmentos da URL sem alterar o endereço principal do produto.
	parts = urlsplit(url.strip())
	return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), parts.query, ""))


def normalize_offer(offer: Offer) -> Offer:
	# Cria uma cópia normalizada sem perder o título original nos dados brutos.
	raw_data = dict(offer.raw_data)
	raw_data.setdefault("original_title", offer.title)
	return Offer(
		title=normalize_text(offer.title),
		price=round(offer.price, 2) if offer.price is not None else None,
		store=normalize_store(offer.store),
		url=normalize_url(offer.url),
		source=normalize_text(offer.source),
		old_price=round(offer.old_price, 2) if offer.old_price is not None else None,
		discount=normalize_text(offer.discount) if offer.discount else None,
		coupon=normalize_text(offer.coupon) if offer.coupon else None,
		seller=normalize_text(offer.seller) if offer.seller else None,
		stock=normalize_text(offer.stock) if offer.stock else None,
		detected_at=offer.detected_at,
		raw_data=raw_data,
	)