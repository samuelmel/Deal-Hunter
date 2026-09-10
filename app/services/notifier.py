from __future__ import annotations

import asyncio
from typing import Any

from telegram import Bot


def format_offer_message(product: dict[str, Any]) -> str:
	# Monta a mensagem curta enviada ao chat do Telegram.
	price = product.get("price")
	formatted_price = f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if price is not None else "Preço indisponível"
	return (
		"🚨 NOVA OFERTA NA KABUM!\n\n"
		f"{product['name']}\n"
		f"💰 {formatted_price}\n"
		f"🔗 {product['url']}"
	)


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
