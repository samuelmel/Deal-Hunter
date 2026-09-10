from app.models.offer import Offer
from app.services.classifier import classify_title
from app.services.deal_scorer import calculate_deal_score
from app.services.notification_rules import should_notify
from app.services.normalizer import normalize_offer
from app.services.price_analyzer import analyze_price


def test_normalize_offer_preserves_original_title() -> None:
	# A normalização deve facilitar agrupamentos sem perder o dado original.
	offer = Offer(
		title="SSD Kingston NV2 1TB",
		price=399.901,
		store="KaBuM!",
		url="HTTPS://EXAMPLE.COM/ssd/#details",
		source="KaBuM",
	)
	normalized = normalize_offer(offer)

	assert normalized.title == "ssd kingston nv2 1tb"
	assert normalized.store == "kabum"
	assert normalized.url == "https://example.com/ssd"
	assert normalized.raw_data["original_title"] == offer.title


def test_classifier_prioritizes_notebook_and_pc_over_ssd() -> None:
	# Componentes no título não devem vencer a categoria do produto principal.
	assert classify_title("SSD Kingston NV2 1TB") == "SSD"
	assert classify_title("Notebook Lenovo com SSD 512GB") == "Notebook"
	assert classify_title("PC Gamer com SSD Kingston 1TB") == "PC/Kit"
	assert classify_title("produto sem categoria") == "Outros"


def test_price_analysis_and_score_are_deterministic() -> None:
	# O mesmo histórico sempre deve produzir os mesmos indicadores e score.
	analysis = analyze_price(399, [470, 460, 450])

	assert analysis.average_price == 460
	assert analysis.lowest_price == 450
	assert analysis.below_average_percent == 13.26
	assert 0 <= calculate_deal_score(analysis, has_coupon=True) <= 100


def test_notification_rule_avoids_same_price_spam() -> None:
	# Oferta repetida sem queda não deve gerar nova notificação.
	assert should_notify(399, None, 80)
	assert should_notify(399, 450, 80)
	assert not should_notify(399, 399, 80)
	assert not should_notify(399, 450, 60)