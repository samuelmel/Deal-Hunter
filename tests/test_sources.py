import json
from unittest.mock import MagicMock, patch

from app.sources.pelando import PelandoSource
from app.sources.pichau import PichauSource
from app.sources.promobit import PromobitSource
from app.sources.terabyte import TerabyteSource


def test_pelando_source_success() -> None:
	sample_data = {
		"deals": [
			{
				"title": "SSD Kingston NV2 1TB",
				"price": 399.90,
				"store": {"name": "Pichau"},
				"url": "https://www.pelando.com.br/ofertas/123",
				"couponCode": "CUPOM10",
			}
		]
	}
	response_bytes = json.dumps(sample_data).encode("utf-8")
	mock_response = MagicMock()
	mock_response.status = 200
	mock_response.headers = {"Content-Type": "application/json"}
	mock_response.read.return_value = response_bytes
	mock_response.__enter__.return_value = mock_response

	with patch("urllib.request.urlopen", return_value=mock_response):
		source = PelandoSource()
		offers = source.collect("ssd")
		assert len(offers) == 1
		assert offers[0].title == "SSD Kingston NV2 1TB"
		assert offers[0].price == 399.90
		assert offers[0].source == "pelando"
		assert offers[0].coupon == "CUPOM10"


def test_pelando_source_handles_network_error_gracefully() -> None:
	with patch("urllib.request.urlopen", side_effect=OSError("Sem conexão")):
		source = PelandoSource()
		offers = source.collect("ssd")
		assert offers == []


def test_promobit_source_success() -> None:
	sample_data = {
		"results": [
			{
				"title": "SSD NVMe 1TB",
				"price": 350.00,
				"store_name": "KaBuM!",
				"url": "https://www.promobit.com.br/oferta/456",
			}
		]
	}
	response_bytes = json.dumps(sample_data).encode("utf-8")
	mock_response = MagicMock()
	mock_response.status = 200
	mock_response.headers = {"Content-Type": "application/json"}
	mock_response.read.return_value = response_bytes
	mock_response.__enter__.return_value = mock_response

	with patch("urllib.request.urlopen", return_value=mock_response):
		source = PromobitSource()
		offers = source.collect("ssd")
		assert len(offers) == 1
		assert offers[0].title == "SSD NVMe 1TB"
		assert offers[0].source == "promobit"


def test_promobit_source_handles_error_gracefully() -> None:
	with patch("urllib.request.urlopen", side_effect=Exception("Bloqueado")):
		source = PromobitSource()
		offers = source.collect("ssd")
		assert offers == []


def test_pichau_source_handles_scraper_block_gracefully() -> None:
	with patch("app.sources.pichau.scrape_pichau", side_effect=RuntimeError("Cloudflare WAF Block")):
		source = PichauSource()
		offers = source.collect("ssd")
		assert offers == []


def test_terabyte_source_handles_scraper_block_gracefully() -> None:
	with patch("app.sources.terabyte.scrape_terabyte", side_effect=TimeoutError("Timeout de rede")):
		source = TerabyteSource()
		offers = source.collect("ssd")
		assert offers == []

