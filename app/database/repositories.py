from __future__ import annotations

import sqlite3
from typing import Any, Iterable

from app.models.offer import Offer
from app.services.classifier import classify_title
from app.services.normalizer import normalize_text

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


def migrate_legacy_observations(connection: sqlite3.Connection) -> int:
	# Converte observações antigas sem duplicá-las em execuções posteriores.
	create_tables(connection)
	legacy_rows = connection.execute(
		"SELECT id, name, price, store, url, raw_text, observed_at FROM offer_observations"
	).fetchall()
	migrated = 0

	for row in legacy_rows:
		normalized_name = normalize_text(row["name"])
		connection.execute(
			"INSERT OR IGNORE INTO products (normalized_name) VALUES (?)",
			(normalized_name,),
		)
		product = connection.execute(
			"SELECT id FROM products WHERE normalized_name = ?",
			(normalized_name,),
		).fetchone()
		offer_cursor = connection.execute(
			"""
			INSERT OR IGNORE INTO offers
			(legacy_observation_id, product_id, title, price, store, source, url, detected_at)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?)
			""",
			(row["id"], product["id"], row["name"], row["price"], row["store"], "kabum", row["url"], row["observed_at"]),
		)
		offer = connection.execute(
			"SELECT id, price, source, detected_at FROM offers WHERE legacy_observation_id = ?",
			(row["id"],),
		).fetchone()
		connection.execute(
			"""
			INSERT OR IGNORE INTO price_history
			(product_id, offer_id, price, source, detected_at)
			VALUES (?, ?, ?, ?, ?)
			""",
			(product["id"], offer["id"], offer["price"] or 0, offer["source"], offer["detected_at"]),
		)
		if offer_cursor.rowcount == 1:
			migrated += 1

	connection.commit()
	return migrated


def save_offer_history(connection: sqlite3.Connection, offers: Iterable[Offer]) -> int:
	# Salva cada observação e registra seu preço no histórico do produto.
	create_tables(connection)
	saved = 0
	for offer in offers:
		normalized_name = normalize_text(offer.title)
		connection.execute(
			"""
			INSERT INTO products (normalized_name)
			VALUES (?)
			ON CONFLICT(normalized_name) DO UPDATE SET updated_at = CURRENT_TIMESTAMP
			""",
			(normalized_name,),
		)
		product = connection.execute(
			"SELECT id FROM products WHERE normalized_name = ?",
			(normalized_name,),
		).fetchone()
		cursor = connection.execute(
			"""
			INSERT INTO offers
			(product_id, title, price, old_price, discount, coupon, store, source, url, detected_at)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
			""",
			(
				product["id"],
				offer.title,
				offer.price,
				offer.old_price,
				offer.discount,
				offer.coupon,
				offer.store,
				offer.source,
				offer.url,
				offer.detected_at.isoformat(),
			),
		)
		if offer.price is not None:
			connection.execute(
				"""
				INSERT INTO price_history
				(product_id, offer_id, price, source, detected_at)
				VALUES (?, ?, ?, ?, ?)
				""",
				(product["id"], cursor.lastrowid, offer.price, offer.source, offer.detected_at.isoformat()),
			)
		saved += 1

	connection.commit()
	return saved


def save_classifications(connection: sqlite3.Connection, offers: Iterable[Offer]) -> int:
	# Persiste a categoria atual para preservar rótulos úteis para ML futuro.
	create_tables(connection)
	saved = 0
	for offer in offers:
		normalized_name = normalize_text(offer.title)
		product = connection.execute(
			"SELECT id FROM products WHERE normalized_name = ?",
			(normalized_name,),
		).fetchone()
		if product is None:
			continue
		connection.execute(
			"INSERT INTO classifications (product_id, category, method) VALUES (?, ?, ?)",
			(product["id"], classify_title(offer.title), "rules"),
		)
		saved += 1
	connection.commit()
	return saved


def get_latest_price(
	connection: sqlite3.Connection,
	url: str,
	source: str,
) -> float | None:
	# Busca o último preço antes da observação atual para aplicar anti-spam.
	row = connection.execute(
		"""
		SELECT price FROM offers
		WHERE url = ? AND source = ?
		ORDER BY detected_at DESC, id DESC
		LIMIT 1
		""",
		(url, source),
	).fetchone()
	return row["price"] if row else None


def record_notification(
	connection: sqlite3.Connection,
	offer_id: int,
	channel: str,
	status: str,
	sent_at: str | None = None,
) -> None:
	# Registra o resultado de uma tentativa de notificação.
	create_tables(connection)
	connection.execute(
		"""
		INSERT INTO notifications (offer_id, channel, status, sent_at)
		VALUES (?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP))
		""",
		(offer_id, channel, status, sent_at),
	)
	connection.commit()
