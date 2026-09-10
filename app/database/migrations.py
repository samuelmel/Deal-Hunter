from __future__ import annotations

import sqlite3


def create_tables(connection: sqlite3.Connection) -> None:
	# Cria tabelas novas sem remover a tabela legada de observações.
	connection.row_factory = sqlite3.Row
	connection.executescript(
		"""
		PRAGMA foreign_keys = ON;

		CREATE TABLE IF NOT EXISTS offer_observations (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			query TEXT NOT NULL,
			url TEXT NOT NULL,
			name TEXT NOT NULL,
			price REAL,
			store TEXT NOT NULL,
			raw_text TEXT NOT NULL,
			observed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
			UNIQUE(query, url, price)
		);

		CREATE INDEX IF NOT EXISTS idx_offer_observations_query_url
			ON offer_observations(query, url);

		CREATE TABLE IF NOT EXISTS products (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			normalized_name TEXT NOT NULL UNIQUE,
			brand TEXT,
			category TEXT,
			created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
			updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
		);

		CREATE TABLE IF NOT EXISTS offers (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			legacy_observation_id INTEGER UNIQUE,
			product_id INTEGER NOT NULL,
			title TEXT NOT NULL,
			price REAL,
			old_price REAL,
			discount TEXT,
			coupon TEXT,
			store TEXT NOT NULL,
			source TEXT NOT NULL,
			url TEXT NOT NULL,
			detected_at TEXT NOT NULL,
			FOREIGN KEY (product_id) REFERENCES products(id)
		);

		CREATE INDEX IF NOT EXISTS idx_offers_product_detected
			ON offers(product_id, detected_at);
		CREATE INDEX IF NOT EXISTS idx_offers_url_price
			ON offers(url, price);

		CREATE TABLE IF NOT EXISTS price_history (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			product_id INTEGER NOT NULL,
			offer_id INTEGER NOT NULL,
			price REAL NOT NULL,
			source TEXT NOT NULL,
			detected_at TEXT NOT NULL,
			FOREIGN KEY (product_id) REFERENCES products(id),
			FOREIGN KEY (offer_id) REFERENCES offers(id)
		);

		CREATE INDEX IF NOT EXISTS idx_price_history_product_date
			ON price_history(product_id, detected_at);
		CREATE UNIQUE INDEX IF NOT EXISTS idx_price_history_offer
			ON price_history(offer_id);

		CREATE TABLE IF NOT EXISTS classifications (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			product_id INTEGER NOT NULL,
			category TEXT NOT NULL,
			method TEXT NOT NULL,
			created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
			FOREIGN KEY (product_id) REFERENCES products(id)
		);

		CREATE TABLE IF NOT EXISTS notifications (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			offer_id INTEGER NOT NULL,
			channel TEXT NOT NULL,
			status TEXT NOT NULL,
			sent_at TEXT,
			FOREIGN KEY (offer_id) REFERENCES offers(id)
		);
		"""
	)
	columns = {row[1] for row in connection.execute("PRAGMA table_info(offers)")}
	if "legacy_observation_id" not in columns:
		connection.execute("ALTER TABLE offers ADD COLUMN legacy_observation_id INTEGER")
		connection.execute(
			"CREATE UNIQUE INDEX IF NOT EXISTS idx_offers_legacy_observation "
			"ON offers(legacy_observation_id)"
		)
	connection.commit()
