from __future__ import annotations

import sqlite3
from pathlib import Path


def get_connection(database_path: str | Path = "data/deal_hunter.db") -> sqlite3.Connection:
	# Cria a pasta do banco e devolve uma conexão SQLite configurada.
	path = Path(database_path)
	path.parent.mkdir(parents=True, exist_ok=True)
	connection = sqlite3.connect(path)
	connection.row_factory = sqlite3.Row
	return connection
