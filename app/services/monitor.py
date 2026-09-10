from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from app.database.connection import get_connection
from app.database.repositories import save_offer_observations
from app.scrapers.kabum import scrape_kabum

from .notifier import send_telegram_notifications


logger = logging.getLogger(__name__)


def monitor_kabum(
	query: str,
	database_path: str | Path = "data/deal_hunter.db",
	headless: bool = True,
) -> dict[str, Any]:
	# Coleta, salva e notifica apenas as mudanças encontradas na execução.
	logger.info("Consultando KaBuM: %s", query)
	products = scrape_kabum(query, limit=None, headless=headless, offers_only=True)
	logger.info("KaBuM retornou %s ofertas", len(products))
	with get_connection(database_path) as connection:
		first_run, new_products = save_offer_observations(connection, query, products)

	load_dotenv()
	telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
	telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
	# A primeira execução envia o inventário inicial; depois envia só novidades.
	products_to_notify = products if first_run else new_products
	if telegram_token and telegram_chat_id:
		logger.info("Enviando %s notificações para o Telegram", len(products_to_notify))
		send_telegram_notifications(telegram_token, telegram_chat_id, products_to_notify)
	else:
		logger.warning("Telegram não configurado; notificações não enviadas")

	return {
		"query": query,
		"total_products": len(products),
		"new_products": len(products_to_notify),
		"first_run": first_run,
	}