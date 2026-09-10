from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

from app.services.monitor import monitor_sources
from app.scrapers.kabum import CATEGORY_FILTERS
from app.services.monitor import monitor_kabum


def configure_logging() -> None:
	# Configura mensagens consistentes para execução local e agendada.
	logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


# Consultas padrão: (query, filter_fn ou None)
DEFAULT_SEARCHES: list[tuple[str, str | None]] = [
	("placa de video nvidia", "nvidia_gpu"),
	("ssd 1tb", None),
	("processador amd ryzen", "amd_cpu"),
]


def main() -> None:
	# Executa uma rodada do monitor de fontes usando as variáveis do ambiente.
	# Executa o scraping da KaBuM para as categorias configuradas.
	configure_logging()
	load_dotenv()
	logger = logging.getLogger(__name__)
	query = os.getenv("DEAL_HUNTER_QUERY", "ssd 1tb").strip()

	logger.info("Iniciando Deal Hunter (Pipeline Multi-Fonte)")
	result = monitor_sources(query)
	logger.info(
		"Execução finalizada: %s coletadas, %s normalizadas, %s salvas, %s oportunidades",
		result.collected,
		result.normalized,
		result.saved,
		result.opportunities,
	)
	logger.info("Iniciando Deal Hunter (KaBuM Multi-Categoria)")

	for query, filter_name in DEFAULT_SEARCHES:
		logger.info("--- Buscando: %s ---", query)
		# Resolve o filtro pelo nome
		filter_fn = CATEGORY_FILTERS.get(filter_name) if filter_name else None
		result = monitor_kabum(query, headless=True, filter_fn=filter_fn)
		logger.info(
			"[%s] %s coletadas, %s novas (first_run=%s)",
			query,
			result["total_products"],
			result["new_products"],
			result["first_run"],
		)

	logger.info("Deal Hunter finalizado.")