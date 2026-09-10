from __future__ import annotations

from dataclasses import dataclass
from statistics import mean


@dataclass(frozen=True, slots=True)
class PriceAnalysis:
	"""Resumo determinístico do preço atual contra o histórico disponível."""

	current_price: float
	average_price: float | None
	lowest_price: float | None
	below_average_percent: float | None


def analyze_price(current_price: float, historical_prices: list[float]) -> PriceAnalysis:
	# Calcula média, menor preço e distância percentual da média.
	prices = [price for price in historical_prices if price > 0]
	if not prices:
		return PriceAnalysis(current_price, None, None, None)

	average_price = mean(prices)
	below_average_percent = max(0.0, (average_price - current_price) / average_price * 100)
	return PriceAnalysis(
		current_price=round(current_price, 2),
		average_price=round(average_price, 2),
		lowest_price=round(min(prices), 2),
		below_average_percent=round(below_average_percent, 2),
	)