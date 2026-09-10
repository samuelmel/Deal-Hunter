from __future__ import annotations


def should_notify(
	current_price: float | None,
	previous_price: float | None,
	deal_score: int,
	*,
	minimum_score: int = 70,
) -> bool:
	# Permite oferta nova ou queda de preço, evitando repetição do mesmo valor.
	if deal_score < minimum_score or current_price is None:
		return False
	if previous_price is None:
		return True
	return current_price < previous_price