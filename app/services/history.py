from __future__ import annotations

import sqlite3


def get_product_price_history(connection: sqlite3.Connection, normalized_name: str) -> list[float]:
	"""Obtém a lista histórica de preços registrados para um produto normalizado."""
	rows = connection.execute(
		"""
		SELECT ph.price
		FROM price_history AS ph
		JOIN products AS p ON p.id = ph.product_id
		WHERE p.normalized_name = ?
		ORDER BY ph.detected_at ASC
		""",
		(normalized_name,),
	).fetchall()
	return [row["price"] for row in rows]

