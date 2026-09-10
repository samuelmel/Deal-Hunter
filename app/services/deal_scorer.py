from __future__ import annotations

from app.services.price_analyzer import PriceAnalysis


def _price_score(analysis: PriceAnalysis) -> int:
	# Converte a queda percentual contra a média em até 40 pontos.
	if analysis.below_average_percent is None:
		return 0
	return min(40, int(analysis.below_average_percent * 2))


def _lowest_price_score(analysis: PriceAnalysis) -> int:
	# Premia ofertas próximas do menor preço histórico conhecido.
	if analysis.lowest_price is None or analysis.lowest_price <= 0:
		return 0
	ratio = analysis.current_price / analysis.lowest_price
	if ratio <= 1:
		return 25
	if ratio <= 1.05:
		return 20
	if ratio <= 1.15:
		return 10
	return 0


def calculate_deal_score(
	analysis: PriceAnalysis,
	* ,
	has_coupon: bool = False,
	source_reliability: float = 1.0,
	store_reliability: float = 1.0,
) -> int:
	# Calcula uma pontuação de 0 a 100 com regras transparentes.
	source_score = max(0.0, min(1.0, source_reliability))
	store_score = max(0.0, min(1.0, store_reliability))
	reliability_points = int(((source_score + store_score) / 2) * 25)
	coupon_points = 10 if has_coupon else 0
	score = _price_score(analysis) + _lowest_price_score(analysis) + coupon_points + reliability_points
	return max(0, min(100, score))