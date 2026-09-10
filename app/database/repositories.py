from __future__ import annotations

import sqlite3
from typing import Any

from .migrations import create_tables


def save_offer_observations(
	connection: sqlite3.Connection,
	query: str,
	products: list[dict[str, Any]],
) -> tuple[bool, list[dict[str, Any]]]:
	# Persiste ofertas e retorna apenas registros novos ou com preço alterado.
	create_tables(connection)
	first_run = connection.execute(
		"SELECT 1 FROM offer_observations WHERE query = ? LIMIT 1",
		(query,),
	).fetchone() is None
	new_products: list[dict[str, Any]] = []

	for product in products:
		cursor = connection.execute(
			"""
			INSERT OR IGNORE INTO offer_observations
			(query, url, name, price, store, raw_text)
			VALUES (?, ?, ?, ?, ?, ?)
			""",
			(
				query,
				product["url"],
				product["name"],
				product.get("price"),
				product.get("store", "KaBuM!"),
				product.get("raw_text", ""),
			),
		)
		if cursor.rowcount == 1:
			new_products.append(product)

	connection.commit()
	return first_run, new_products
