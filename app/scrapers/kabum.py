from __future__ import annotations

import random
import re
import time
from typing import Any
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright


KABUM_URL = "https://www.kabum.com.br"
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
	# Realiza rolagens suaves e pausas aleatórias simulando comportamento humano.
	try:
		for _ in range(random.randint(1, 3)):
			scroll_amount = random.randint(300, 700)
			page.mouse.wheel(0, scroll_amount)
			time.sleep(random.uniform(0.5, 1.2))
	except Exception:
		pass


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

	return name_lower.startswith(query_terms[0]) or query_terms[0] in name_lower


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
	# Abre a KaBuM e executa a pesquisa usando o campo oficial da página com stealth.
	_apply_stealth(page)
	page.goto(f"{KABUM_URL}/", wait_until="domcontentloaded")
	time.sleep(random.uniform(1.5, 3.0))

	search_input = page.locator("#inputBusca")
	try:
		search_input.wait_for(state="visible", timeout=10_000)
		search_input.press_sequentially(query, delay=random.randint(70, 140))
		time.sleep(random.uniform(0.8, 1.5))
		with page.expect_navigation(wait_until="domcontentloaded", timeout=15_000):
			search_input.press("Enter")
	except PlaywrightTimeoutError:
		page.goto(f"{KABUM_URL}/busca?query={quote_plus(query)}", wait_until="domcontentloaded")

	try:
		page.wait_for_load_state("networkidle", timeout=15_000)
	except PlaywrightTimeoutError:
		pass

	_simulate_human_behavior(page)


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

		scroll_step = random.randint(3000, 5000)
		page.mouse.wheel(0, scroll_step)
		time.sleep(random.uniform(1.0, 2.0))
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
	# Pesquisa ofertas na KaBuM aplicando técnicas stealth e comportamento humano.
	if not query.strip():
		raise ValueError("query must not be empty")
	if limit is not None and limit < 1:
		raise ValueError("limit must be greater than zero")
	if max_scrolls < 1:
		raise ValueError("max_scrolls must be greater than zero")

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
			if offers_only:
				_select_offer_filter(page)
			products = _collect_offer_products(page, query, max_scrolls)
			return products if limit is None else products[:limit]
		finally:
			browser.close()


if __name__ == "__main__":
	for product in scrape_kabum("ssd 1tb", limit=5):
		print(product)
