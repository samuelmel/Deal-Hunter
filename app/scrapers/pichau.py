from __future__ import annotations

import random
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright


PICHAU_URL = "https://www.pichau.com.br"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


def _apply_stealth(page: Page) -> None:
	# Modifica variáveis globais do navegador para remover flags de automação.
	page.add_init_script(
		"""
		Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
		window.chrome = { runtime: {} };
		Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
		Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt', 'en-US', 'en']});
		"""
	)


def _simulate_human_behavior(page: Page) -> None:
	# Simula scrolling leve e pausas comportamentais típicas de usuário humano.
	try:
		for _ in range(random.randint(2, 4)):
			scroll_amount = random.randint(250, 600)
			page.mouse.wheel(0, scroll_amount)
			time.sleep(random.uniform(0.5, 1.2))
	except Exception:
		pass


def _parse_price(text: str) -> float | None:
	# Converte um preço brasileiro encontrado no texto para float.
	match = re.search(r"R\$\s*([\d.]+,\d{2})", text)
	if not match:
		return None

	number = match.group(1).replace(".", "").replace(",", ".")
	try:
		return float(number)
	except ValueError:
		return None


def _extract_products(html: str, limit: int | None = None) -> list[dict[str, Any]]:
	# Extrai os cards de produto identificados no HTML da Pichau.
	soup = BeautifulSoup(html, "html.parser")
	products: list[dict[str, Any]] = []
	seen_urls: set[str] = set()

	for card in soup.select('a[data-cy="list-product"], a[href*="/produto/"]'):
		href = card.get("href")
		name_element = card.select_one("h2") or card.select_one('[class*="title"]')
		if not href or name_element is None:
			continue

		url = urljoin(PICHAU_URL, href)
		if url in seen_urls:
			continue

		text = card.get_text(" ", strip=True)
		price_element = card.select_one('[class*="price_vista"]')
		old_price_element = card.select_one('[class*="strikeThrough"]')
		discount_element = card.select_one('[class*="availability_span_discount"]')
		stock_element = card.select_one('[class*="availability_span_available"]')
		installment_element = card.select_one('[class*="price_parcelado_inline"]')

		product = {
			"name": name_element.get_text(" ", strip=True),
			"price": _parse_price(price_element.get_text(" ", strip=True)) if price_element else None,
			"old_price": _parse_price(old_price_element.get_text(" ", strip=True)) if old_price_element else None,
			"discount": discount_element.get_text(" ", strip=True) if discount_element else None,
			"stock": stock_element.get_text(" ", strip=True) if stock_element else None,
			"installment": installment_element.get_text(" ", strip=True) if installment_element else None,
			"url": url,
			"store": "Pichau",
			"raw_text": text,
		}
		products.append(product)
		seen_urls.add(url)
		if limit is not None and len(products) >= limit:
			break

	return products


def _search(page: Page, query: str) -> None:
	# Abre a Pichau, preenche a busca e aplica atrasos aleatórios anti-throttling.
	_apply_stealth(page)
	page.goto(PICHAU_URL, wait_until="domcontentloaded")
	time.sleep(random.uniform(2.0, 4.0))
	_simulate_human_behavior(page)

	search_input = page.locator('input[placeholder="O que você está procurando? Digite aqui..."]')
	if not search_input.count():
		search_input = page.locator('input[role="combobox"]')
	try:
		search_input.wait_for(state="visible", timeout=10_000)
	except PlaywrightTimeoutError:
		page.goto(f"{PICHAU_URL}/search?q={quote_plus(query)}", wait_until="domcontentloaded")
		_simulate_human_behavior(page)
		return

	search_input.press_sequentially(query, delay=random.randint(90, 160))
	time.sleep(random.uniform(1.0, 2.0))

	try:
		with page.expect_navigation(wait_until="domcontentloaded", timeout=15_000):
			search_input.press("Enter")
	except PlaywrightTimeoutError:
		page.goto(f"{PICHAU_URL}/search?q={quote_plus(query)}", wait_until="domcontentloaded")

	if "/search" not in page.url:
		page.goto(f"{PICHAU_URL}/search?q={quote_plus(query)}", wait_until="domcontentloaded")

	_simulate_human_behavior(page)


def _page_urls(page: Page, max_pages: int) -> list[str]:
	# Obtém URLs de paginação sem ultrapassar o limite configurado.
	urls = [page.url]
	for link in page.locator('a[aria-label^="Go to page"]').all():
		href = link.get_attribute("href")
		if href:
			url = urljoin(PICHAU_URL, href)
			if url not in urls:
				urls.append(url)
		if len(urls) >= max_pages:
			break
	return urls


def scrape_pichau(
	query: str,
	limit: int | None = 36,
	max_pages: int = 1,
	headless: bool = False,
	user_data_dir: str | Path = "data/pichau-profile",
) -> list[dict[str, Any]]:
	# Pesquisa produtos aplicando técnicas stealth e comportamento humano.
	if not query.strip():
		raise ValueError("query must not be empty")
	if limit is not None and limit < 1:
		raise ValueError("limit must be greater than zero")
	if max_pages < 1:
		raise ValueError("max_pages must be greater than zero")

	stealth_args = [
		"--disable-blink-features=AutomationControlled",
		"--no-sandbox",
		"--disable-setuid-sandbox",
		"--disable-infobars",
		"--window-size=1920,1080",
	]

	with sync_playwright() as playwright:
		context = playwright.chromium.launch_persistent_context(
			str(user_data_dir),
			headless=headless,
			user_agent=USER_AGENT,
			viewport={"width": 1920, "height": 1080},
			locale="pt-BR",
			args=stealth_args,
		)
		try:
			page = context.new_page()
			_search(page, query)
			products_by_url: dict[str, dict[str, Any]] = {}
			for page_url in _page_urls(page, max_pages):
				if page.url != page_url:
					time.sleep(random.uniform(2.0, 5.0))
					page.goto(page_url, wait_until="domcontentloaded")
					_simulate_human_behavior(page)
				for product in _extract_products(page.content()):
					products_by_url[product["url"]] = product
				if limit is not None and len(products_by_url) >= limit:
					break

			products = list(products_by_url.values())
			return products if limit is None else products[:limit]
		finally:
			context.close()


if __name__ == "__main__":
	for product in scrape_pichau("ssd 1tb", limit=10):
		print(product)
