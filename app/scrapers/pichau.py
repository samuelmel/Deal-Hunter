from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright


PICHAU_URL = "https://www.pichau.com.br"


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
	# Extrai os cards de produto identificados pelo data-cy da Pichau.
	soup = BeautifulSoup(html, "html.parser")
	products: list[dict[str, Any]] = []
	seen_urls: set[str] = set()

	for card in soup.select('a[data-cy="list-product"]'):
		href = card.get("href")
		name_element = card.select_one("h2")
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
	# Abre a Pichau, preenche o campo de busca e carrega os resultados.
	page.goto(PICHAU_URL, wait_until="domcontentloaded")
	search_input = page.locator('input[placeholder="O que você está procurando? Digite aqui..."]')
	if not search_input.count():
		search_input = page.locator('input[role="combobox"]')
	try:
		search_input.wait_for(state="visible", timeout=10_000)
	except PlaywrightTimeoutError:
		page.goto(f"{PICHAU_URL}/search?q={quote_plus(query)}", wait_until="domcontentloaded")
		return
	# Digita como uma pessoa para permitir que o autocomplete seja atualizado.
	search_input.press_sequentially(query, delay=120)
	page.wait_for_timeout(1_500)

	try:
		with page.expect_navigation(wait_until="domcontentloaded", timeout=15_000):
			search_input.press("Enter")
	except PlaywrightTimeoutError:
		page.goto(f"{PICHAU_URL}/search?q={quote_plus(query)}", wait_until="domcontentloaded")
	if "/search" not in page.url:
		page.goto(f"{PICHAU_URL}/search?q={quote_plus(query)}", wait_until="domcontentloaded")

	try:
		page.wait_for_load_state("networkidle", timeout=15_000)
	except PlaywrightTimeoutError:
		pass


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
	# Pesquisa produtos usando um perfil persistente e retorna cards normalizados.
	if not query.strip():
		raise ValueError("query must not be empty")
	if limit is not None and limit < 1:
		raise ValueError("limit must be greater than zero")
	if max_pages < 1:
		raise ValueError("max_pages must be greater than zero")

	with sync_playwright() as playwright:
		# Mantém cookies e sessões para reduzir bloqueios entre execuções.
		context = playwright.chromium.launch_persistent_context(
			str(user_data_dir),
			headless=headless,
		)
		try:
			page = context.new_page()
			_search(page, query)
			products_by_url: dict[str, dict[str, Any]] = {}
			for page_url in _page_urls(page, max_pages):
				if page.url != page_url:
					page.goto(page_url, wait_until="domcontentloaded")
					try:
						page.wait_for_load_state("networkidle", timeout=15_000)
					except PlaywrightTimeoutError:
						pass
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
