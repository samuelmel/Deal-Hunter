import sqlite3
from datetime import datetime, timezone

from app.database.migrations import create_tables
from app.database.repositories import save_offer_history
from app.models.offer import Offer
from app.sources.collection import collect_from_sources


def test_collection_continues_when_one_source_fails() -> None:
	# Uma falha individual não deve impedir fontes saudáveis.
	offer = Offer("SSD teste", 100, "store", "https://example.com", "good")

	class GoodSource:
		name = "good"

		def collect(self, query: str) -> list[Offer]:
			return [offer]

	class FailingSource:
		name = "failing"

		def collect(self, query: str) -> list[Offer]:
			raise RuntimeError("falha simulada")

	assert collect_from_sources([GoodSource(), FailingSource()], "ssd") == [offer]


def test_offer_history_keeps_price_changes() -> None:
	# O mesmo produto com preços distintos deve gerar histórico separado.
	connection = sqlite3.connect(":memory:")
	connection.row_factory = sqlite3.Row
	offers = [
		Offer("SSD teste", 450, "store", "https://example.com/ssd", "source", detected_at=datetime(2026, 9, 9, tzinfo=timezone.utc)),
		Offer("SSD teste", 399, "store", "https://example.com/ssd", "source", detected_at=datetime(2026, 9, 10, tzinfo=timezone.utc)),
	]

	assert save_offer_history(connection, offers) == 2
	assert connection.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 1
	assert connection.execute("SELECT COUNT(*) FROM offers").fetchone()[0] == 2
	assert connection.execute("SELECT COUNT(*) FROM price_history").fetchone()[0] == 2