from __future__ import annotations

import re


def parse_product_specs(text: str) -> dict[str, str]:
	"""Extrai especificações básicas a partir do texto descritivo do produto."""
	specs: dict[str, str] = {}
	capacity_match = re.search(r"(\d+\s*(?:GB|TB))", text, re.IGNORECASE)
	if capacity_match:
		specs["capacity"] = capacity_match.group(1).upper()
	return specs

