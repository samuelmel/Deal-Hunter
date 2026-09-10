from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from app.models.offer import Offer


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PromobitSource:
	"""Fonte agregadora do Promobit utilizando consulta HTTP simples e transparente."""

	timeout: int = 10
	name: str = "promobit"

	def collect(self, query: str) -> list[Offer]:
		# Consulta ofertas públicas do Promobit com tratamento gracioso de indisponibilidade.
		offers: list[Offer] = []
		if not query.strip():
			return offers

		url = f"https://www.promobit.com.br/api/v2/search/offers?q={urllib.parse.quote(query)}"
		headers = {
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DealHunter/1.0",
			"Accept": "application/json, text/plain, */*",
		}

		try:
			req = urllib.request.Request(url, headers=headers)
			with urllib.request.urlopen(req, timeout=self.timeout) as response:
				if response.status != 200:
					logger.info("Fonte Promobit: API pública indisponível (HTTP %s)", response.status)
					return []
				content_type = response.headers.get("Content-Type", "")
				data = json.loads(response.read().decode("utf-8")) if "json" in content_type else {}
		except urllib.error.HTTPError as err:
			logger.info("Fonte Promobit: API pública não disponível ou alterada (HTTP %s)", err.code)
			return []
		except Exception as exc:
			logger.warning("Fonte Promobit indisponível: %s", exc)
			return []

		items = (data.get("results", []) or data.get("offers", [])) if isinstance(data, dict) else []
		for item in items:
			if not isinstance(item, dict):
				continue
			title = item.get("title") or item.get("name")
			if not title:
				continue
			price = item.get("price") or item.get("offer_price")
			try:
				price_float = float(price) if price is not None else None
			except (ValueError, TypeError):
				price_float = None

			store = item.get("store_name") or (item.get("store", {}).get("name") if isinstance(item.get("store"), dict) else "Promobit")
			deal_url = item.get("url") or item.get("link") or f"https://www.promobit.com.br/oferta/{item.get('id', '')}"
			coupon = item.get("coupon") or item.get("coupon_code")

			offers.append(
				Offer(
					title=str(title),
					price=price_float,
					store=str(store),
					url=str(deal_url),
					source="promobit",
					coupon=str(coupon) if coupon else None,
					raw_data=item,
				)
			)

		return offers
