from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

from app.services.monitor import monitor_sources


def configure_logging() -> None:
	# Configura mensagens consistentes para execução local e agendada.
	logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def main() -> None:
	# Executa uma rodada do monitor de fontes usando as variáveis do ambiente.
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