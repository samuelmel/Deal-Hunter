from __future__ import annotations

import sqlite3


def create_tables(connection: sqlite3.Connection) -> None:
	# Cria a tabela de observações e o índice usado nas consultas.
	connection.executescript(
		"""
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
		"""
	)
	connection.commit()
