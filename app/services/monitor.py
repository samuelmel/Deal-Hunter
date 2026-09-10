from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Iterable

from dotenv import load_dotenv

from app.database.connection import get_connection
from app.database.repositories import save_offer_observations
from app.models.offer import Offer
from app.pipeline.runner import PipelineResult, run_pipeline
from app.scrapers.kabum import scrape_kabum
from app.sources.base import Source
from app.sources.kabum import KabumSource
from app.sources.pelando import PelandoSource
from app.sources.pichau import PichauSource
from app.sources.promobit import PromobitSource
from app.sources.terabyte import TerabyteSource

from .notifier import send_pipeline_notifications, send_telegram_notifications


logger = logging.getLogger(__name__)


def get_default_sources(headless: bool = True) -> list[Source[Offer]]:
	# Retorna todas as fontes ativas desacopladas.
	return [
		PelandoSource(),
		PromobitSource(),
		KabumSource(headless=headless),
		PichauSource(headless=headless),
		TerabyteSource(headless=headless),
	]


def monitor_sources(
	query: str,
	database_path: str | Path = "data/deal_hunter.db",
	headless: bool = True,
	sources: Iterable[Source[Offer]] | None = None,
) -> PipelineResult:
	# Executa a coleta pelas abstrações de Source e grava no histórico normalizado.
	active_sources = list(sources) if sources is not None else get_default_sources(headless=headless)
	result = run_pipeline(
		active_sources,
		query,
		database_path=database_path,
	)
	load_dotenv()
	token = os.getenv("TELEGRAM_BOT_TOKEN")
	chat_id = os.getenv("TELEGRAM_CHAT_ID")
	if token and chat_id:
		sent = send_pipeline_notifications(token, chat_id, list(result.items))
		logger.info("Telegram enviou %s oportunidades", sent)
	else:
		logger.warning("Telegram não configurado; oportunidades não enviadas")
	return result


def monitor_kabum(
	query: str,
	database_path: str | Path = "data/deal_hunter.db",
	headless: bool = True,
	filter_fn: Any | None = None,
) -> dict[str, Any]:
	# Mantém compatibilidade com a função legada de monitoramento exclusivo da KaBuM.
	logger.info("Consultando KaBuM (legado): %s", query)
	products = scrape_kabum(query, limit=None, headless=headless, offers_only=True)
	logger.info("KaBuM retornou %s ofertas", len(products))
	# Coleta ofertas da KaBuM para uma única consulta com filtro opcional por categoria.
	logger.info("Consultando KaBuM: %s", query)
	products = scrape_kabum(query, limit=None, headless=headless, offers_only=True, filter_fn=filter_fn)
	logger.info("KaBuM retornou %s ofertas para '%s'", len(products), query)
	with get_connection(database_path) as connection:
		first_run, new_products = save_offer_observations(connection, query, products)

	load_dotenv()
	telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
	telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
	products_to_notify = products if first_run else new_products
	if telegram_token and telegram_chat_id:
		logger.info("Enviando %s notificações para o Telegram", len(products_to_notify))
		logger.info("Enviando %s notificações ao Telegram", len(products_to_notify))
		send_telegram_notifications(telegram_token, telegram_chat_id, products_to_notify)
	else:
		logger.warning("Telegram não configurado; notificações não enviadas")

	return {
		"query": query,
		"total_products": len(products),
		"new_products": len(products_to_notify),
		"first_run": first_run,
	}


def monitor_kabum_multiple(
	queries: list[str],
	database_path: str | Path = "data/deal_hunter.db",
	headless: bool = True,
) -> dict[str, dict[str, Any]]:
	# Executa monitor_kabum para várias consultas e retorna os resultados agrupados.
	results: dict[str, dict[str, Any]] = {}
	for q in queries:
		results[q] = monitor_kabum(q, database_path=database_path, headless=headless)
	return results