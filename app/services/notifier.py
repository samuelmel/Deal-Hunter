from __future__ import annotations

import asyncio
from typing import Any

from telegram import Bot

from app.pipeline.runner import PipelineItem


def _format_brl(price: float | None) -> str:
	# Formata valores numéricos como moeda brasileira.
	return f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if price is not None else "Preço indisponível"


def format_offer_message(
	product: dict[str, Any],
	analysis: Any | None = None,
	deal_score: int | None = None,
) -> str:
	# Monta uma mensagem detalhada sem quebrar o formato legado.
	price = product.get("price")
	lines = [
		"🔥 POSSÍVEL OPORTUNIDADE",
		"",
		f"{product['name']}\n"
		f"💰 Preço: {_format_brl(price)}",
	]
	if analysis is not None:
		if analysis.average_price is not None:
			lines.append(f"📊 Média histórica: {_format_brl(analysis.average_price)}")
		if analysis.lowest_price is not None:
			lines.append(f"📉 Menor preço: {_format_brl(analysis.lowest_price)}")
		if analysis.below_average_percent is not None:
			lines.append(f"↓ {analysis.below_average_percent:.2f}% abaixo da média")
	if deal_score is not None:
		lines.append(f"⭐ Deal Score: {deal_score}/100")
	lines.extend(
		[
			f"🏪 Loja: {product.get('store', 'desconhecida')}",
			f"🔗 {product['url']}",
		]
	)
	return "\n".join(lines)


async def _send_messages(token: str, chat_id: str, products: list[dict[str, Any]]) -> None:
	# Envia as ofertas uma a uma usando o Bot assíncrono.
	async with Bot(token=token) as bot:
		for product in products:
			await bot.send_message(chat_id=chat_id, text=format_offer_message(product))


def send_telegram_notifications(
	token: str,
	chat_id: str,
	products: list[dict[str, Any]],
) -> None:
	# Inicia o envio assíncrono somente quando há ofertas para notificar.
	if products:
		asyncio.run(_send_messages(token, chat_id, products))


def send_pipeline_notifications(
	token: str,
	chat_id: str,
	items: list[PipelineItem],
) -> int:
	# Envia somente itens aprovados pelo histórico e pelo Deal Score.
	products: list[dict[str, Any]] = []
	for item in items:
		if not item.notify:
			continue
		products.append(
			{
				"name": item.offer.title,
				"price": item.offer.price,
				"store": item.offer.store,
				"url": item.offer.url,
				"source": item.offer.source,
			}
		)
	if products:
		asyncio.run(_send_messages(token, chat_id, products))
	return len(products)
