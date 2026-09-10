from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright


KABUM_URL = "https://www.kabum.com.br"


def _parse_price(text: str) -> float | None:
	# Converte o primeiro preço brasileiro encontrado no texto para float.
	match = re.search(r"R\$\s*([\d.]+,\d{2})", text)
	if not match:
		return None

	number = match.group(1).replace(".", "").replace(",", ".")
	try:
		return float(number)
	except ValueError:
		return None


def _matches_query(name: str, query: str) -> bool:
	# Evita itens que apenas citam o termo pesquisado nas especificações.
	query_terms = [term.lower() for term in re.findall(r"\w+", query) if len(term) > 1]
	name_lower = name.lower()
	if not query_terms or not all(term in name_lower for term in query_terms):
		return False

	return name_lower.startswith(query_terms[0])


def _extract_products(
	html: str,
	query: str,
	limit: int | None = None,
) -> list[dict[str, Any]]:
	# Extrai produtos únicos dos links de produto presentes no HTML.
	soup = BeautifulSoup(html, "html.parser")
	products: list[dict[str, Any]] = []
	seen_urls: set[str] = set()

	for link in soup.select('a[href*="/produto/"]'):
		href = link.get("href")
		if not href:
			continue

		url = urljoin(KABUM_URL, href)
		if url in seen_urls:
			continue

		text = link.get_text(" ", strip=True)
		name_text = re.sub(
			r"^.*?Avaliação\s+[\d.,]+\s+de\s+[\d.,]+",
			"",
			text,
			count=1,
			flags=re.IGNORECASE,
		)
		name = re.split(r"\s+R\$", name_text, maxsplit=1)[0]
		name = re.sub(r"^\W+", "", name, flags=re.UNICODE).strip()
		if not name or not _matches_query(name, query):
			continue

		products.append(
			{
				"name": name,
				"price": _parse_price(text),
				"url": url,
				"store": "KaBuM!",
				"raw_text": text,
			}
		)
		seen_urls.add(url)
		if limit is not None and len(products) >= limit:
			break

	return products


def _search(page: Page, query: str) -> None:
	# Abre a KaBuM e executa a pesquisa usando o campo oficial da página.
	page.goto(f"{KABUM_URL}/", wait_until="domcontentloaded")
	search_input = page.locator("#inputBusca")
	search_input.wait_for(state="visible")
	search_input.fill(query)

	try:
		with page.expect_navigation(wait_until="domcontentloaded", timeout=15_000):
			search_input.press("Enter")
	except PlaywrightTimeoutError:
		page.goto(f"{KABUM_URL}/busca?query={quote_plus(query)}", wait_until="domcontentloaded")

	page.wait_for_load_state("networkidle", timeout=15_000)


def _select_offer_filter(page: Page) -> None:
	# Ativa o filtro Oferta quando ele estiver disponível nos resultados.
	offer_filter = page.locator(
		'[data-testid="Oferta_has_offer"] input[data-testid="checkboxFilter"]'
	)
	if not offer_filter.count():
		return

	offer_filter.first.wait_for(state="visible")
	if not offer_filter.first.is_checked():
		offer_filter.first.check()
		try:
			page.wait_for_load_state("networkidle", timeout=15_000)
		except PlaywrightTimeoutError:
			pass
	else:
		page.wait_for_timeout(500)


def _collect_offer_products(page: Page, query: str, max_scrolls: int) -> list[dict[str, Any]]:
	# Rola a listagem e acumula produtos até não surgirem novos resultados.
	products_by_url: dict[str, dict[str, Any]] = {}
	unchanged_rounds = 0

	for _ in range(max_scrolls):
		before = len(products_by_url)
		for product in _extract_products(page.content(), query):
			products_by_url[product["url"]] = product

		page.mouse.wheel(0, 5_000)
		page.wait_for_timeout(1_000)
		if len(products_by_url) == before:
			unchanged_rounds += 1
			if unchanged_rounds >= 3:
				break
		else:
			unchanged_rounds = 0

	return list(products_by_url.values())


def scrape_kabum(
	query: str,
	limit: int | None = 20,
	headless: bool = True,
	offers_only: bool = True,
	max_scrolls: int = 50,
) -> list[dict[str, Any]]:
	# Pesquisa ofertas na KaBuM e retorna dados normalizados dos produtos.
	if not query.strip():
		raise ValueError("query must not be empty")
	if limit is not None and limit < 1:
		raise ValueError("limit must be greater than zero")
	if max_scrolls < 1:
		raise ValueError("max_scrolls must be greater than zero")

	with sync_playwright() as playwright:
		browser = playwright.chromium.launch(headless=headless)
		try:
			page = browser.new_page()
			_search(page, query)
			if offers_only:
				_select_offer_filter(page)
			products = _collect_offer_products(page, query, max_scrolls)
			return products if limit is None else products[:limit]
		finally:
			browser.close()


if __name__ == "__main__":
	for product in scrape_kabum("ssd 1tb", limit=5):
		print(product)
