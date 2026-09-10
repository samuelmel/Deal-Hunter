from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

from app.services.normalizer import normalize_text


TERABYTE_URL = "https://www.terabyteshop.com.br"


def _parse_price(text: str) -> float | None:
	# Converte um preço brasileiro do card para float.
	match = re.search(r"R\$\s*([\d.]+,\d{2})", text)
	if not match:
		return None

	return float(match.group(1).replace(".", "").replace(",", "."))


def _matches_query(name: str, query: str) -> bool:
	# Mantém a categoria principal e evita PCs em buscas específicas de SSD.
	stop_words = {"com", "de", "do", "da", "e", "para"}
	terms = [term for term in normalize_text(query).split() if term not in stop_words]
	normalized_name = normalize_text(name)
	return bool(terms) and all(term in normalized_name for term in terms) and normalized_name.startswith(terms[0])


def _extract_products(
	html: str,
	query: str,
	limit: int | None = None,
	promotions_only: bool = True,
	in_stock_only: bool = True,
) -> list[dict[str, Any]]:
	# Extrai cards da grade de resultados da Terabyte.
	soup = BeautifulSoup(html, "html.parser")
	products: list[dict[str, Any]] = []
	seen_urls: set[str] = set()

	for card in soup.select(".tss-results-grid .product-item"):
		name_element = card.select_one(".product-item__name h2")
		link_element = card.select_one(".product-item__name[href]")
		if name_element is None or link_element is None:
			continue

		name = name_element.get_text(" ", strip=True)
		if not _matches_query(name, query):
			continue

		if promotions_only and card.get("data-tss-promo") != "1":
			continue
		if in_stock_only and card.get("data-tss-estoque") != "1":
			continue

		url = urljoin(TERABYTE_URL, link_element.get("href", ""))
		if not url or url in seen_urls:
			continue

		price_value = card.get("data-tss-price")
		price = float(price_value) if price_value else _parse_price(card.get_text(" ", strip=True))
		old_price = _parse_price(
			card.select_one(".product-item__old-price").get_text(" ", strip=True)
		) if card.select_one(".product-item__old-price") else None
		discount = None
		if price and old_price and old_price > price:
			discount = f"{((old_price - price) / old_price) * 100:.2f}%"

		products.append(
			{
				"name": name,
				"price": price,
				"old_price": old_price,
				"discount": discount,
				"stock": card.get("data-tss-estoque"),
				"url": url,
				"store": "Terabyte Shop",
				"source": "terabyte",
				"raw_text": card.get_text(" ", strip=True),
			}
		)
		seen_urls.add(url)
		if limit is not None and len(products) >= limit:
			break

	return products


def _search(page: Page, query: str) -> None:
	# Pesquisa pela caixa oficial e garante a rota de resultados.
	page.goto(TERABYTE_URL, wait_until="domcontentloaded")
	search_input = page.locator("#isearch")
	search_input.wait_for(state="visible")
	search_input.press_sequentially(query, delay=80)
	try:
		with page.expect_navigation(wait_until="domcontentloaded", timeout=15_000):
			search_input.press("Enter")
	except PlaywrightTimeoutError:
		page.goto(f"{TERABYTE_URL}/busca?str={quote_plus(query)}", wait_until="domcontentloaded")

	if "/busca" not in page.url:
		page.goto(f"{TERABYTE_URL}/busca?str={quote_plus(query)}", wait_until="domcontentloaded")
	try:
		page.wait_for_load_state("networkidle", timeout=15_000)
	except PlaywrightTimeoutError:
		pass


def scrape_terabyte(
	query: str,
	limit: int | None = 36,
	headless: bool = True,
	promotions_only: bool = True,
	in_stock_only: bool = True,
) -> list[dict[str, Any]]:
	# Pesquisa ofertas na Terabyte e retorna produtos normalizados em dicionários.
	if not query.strip():
		raise ValueError("query must not be empty")
	if limit is not None and limit < 1:
		raise ValueError("limit must be greater than zero")

	with sync_playwright() as playwright:
		browser = playwright.chromium.launch(headless=headless)
		try:
			page = browser.new_page()
			_search(page, query)
			return _extract_products(
				page.content(),
				query,
				limit,
				promotions_only,
				in_stock_only,
			)
		finally:
			browser.close()


if __name__ == "__main__":
	for product in scrape_terabyte("ssd 1tb", limit=10):
		print(product)
