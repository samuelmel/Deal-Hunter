from __future__ import annotations

import random
import re
import time
from typing import Any
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

from app.services.normalizer import normalize_text


TERABYTE_URL = "https://www.terabyteshop.com.br"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


def _apply_stealth(page: Page) -> None:
	# Modifica variáveis do navegador para remover flags de automação.
	page.add_init_script(
		"""
		Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
		window.chrome = { runtime: {} };
		Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
		Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt', 'en-US', 'en']});
		"""
	)


def _simulate_human_behavior(page: Page) -> None:
	# Realiza rolagens suaves e pequenas pausas aleatórias simulando humano.
	try:
		for _ in range(random.randint(2, 4)):
			scroll_amount = random.randint(200, 500)
			page.mouse.wheel(0, scroll_amount)
			time.sleep(random.uniform(0.5, 1.2))
	except Exception:
		pass


def _parse_price(text: str) -> float | None:
	# Converte um preço brasileiro do card para float.
	match = re.search(r"R\$\s*([\d.]+,\d{2})", text)
	if not match:
		return None

	return float(match.group(1).replace(".", "").replace(",", "."))


def _matches_query(name: str, query: str) -> bool:
	# Verifica se os termos da busca estão presentes no título.
	stop_words = {"com", "de", "do", "da", "e", "para"}
	terms = [term for term in normalize_text(query).split() if term not in stop_words]
	normalized_name = normalize_text(name)
	return bool(terms) and all(term in normalized_name for term in terms)


def _extract_products(
	html: str,
	query: str,
	limit: int | None = None,
	promotions_only: bool = False,
	in_stock_only: bool = False,
) -> list[dict[str, Any]]:
	# Extrai cards de produtos da Terabyte com seletores resilientes.
	soup = BeautifulSoup(html, "html.parser")
	products: list[dict[str, Any]] = []
	seen_urls: set[str] = set()

	for card in soup.select(".pbox, .product-item, div[data-tss-price]"):
		name_element = card.select_one(".product-item__name h2, .pbox-title, h2")
		link_element = card.select_one("a[href]")
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
		old_price_el = card.select_one(".product-item__old-price, .pbox-old-price")
		old_price = _parse_price(old_price_el.get_text(" ", strip=True)) if old_price_el else None
		discount = None
		if price and old_price and old_price > price:
			discount = f"{((old_price - price) / old_price) * 100:.2f}%"

		products.append(
			{
				"name": name,
				"price": price,
				"old_price": old_price,
				"discount": discount,
				"stock": card.get("data-tss-estoque", "1"),
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
	# Executa busca com técnicas stealth e pausas anti-throttling.
	_apply_stealth(page)
	page.goto(TERABYTE_URL, wait_until="domcontentloaded")
	time.sleep(random.uniform(2.0, 4.0))
	_simulate_human_behavior(page)

	search_input = page.locator("#isearch")
	try:
		search_input.wait_for(state="visible", timeout=10_000)
		search_input.press_sequentially(query, delay=random.randint(80, 150))
		time.sleep(random.uniform(1.0, 2.0))
		with page.expect_navigation(wait_until="domcontentloaded", timeout=15_000):
			search_input.press("Enter")
	except PlaywrightTimeoutError:
		page.goto(f"{TERABYTE_URL}/busca?str={quote_plus(query)}", wait_until="domcontentloaded")

	if "/busca" not in page.url:
		page.goto(f"{TERABYTE_URL}/busca?str={quote_plus(query)}", wait_until="domcontentloaded")

	_simulate_human_behavior(page)


def scrape_terabyte(
	query: str,
	limit: int | None = 36,
	headless: bool = True,
	promotions_only: bool = False,
	in_stock_only: bool = False,
) -> list[dict[str, Any]]:
	# Pesquisa produtos aplicando técnicas de moderação e comportamentos humanos.
	if not query.strip():
		raise ValueError("query must not be empty")
	if limit is not None and limit < 1:
		raise ValueError("limit must be greater than zero")

	stealth_args = [
		"--disable-blink-features=AutomationControlled",
		"--no-sandbox",
		"--disable-setuid-sandbox",
		"--disable-infobars",
		"--window-size=1920,1080",
	]

	with sync_playwright() as playwright:
		browser = playwright.chromium.launch(headless=headless, args=stealth_args)
		try:
			context = browser.new_context(
				user_agent=USER_AGENT,
				viewport={"width": 1920, "height": 1080},
				locale="pt-BR",
			)
			page = context.new_page()
			_search(page, query)
			time.sleep(random.uniform(2.0, 5.0))
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
