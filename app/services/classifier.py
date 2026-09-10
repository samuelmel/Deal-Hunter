from __future__ import annotations

from app.services.normalizer import normalize_text


RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
	("Notebook", ("notebook", "laptop")),
	("PC/Kit", ("pc gamer", "computador gamer", "desktop", "kit pc", "computador")),
	("GPU", ("placa de video", "placa de vídeo", "gpu", "rtx", "gtx", "radeon")),
	("CPU", ("processador", "cpu", "ryzen", "core i3", "core i5", "core i7", "core i9")),
	("RAM", ("memoria ram", "memória ram", "ddr4", "ddr5")),
	("SSD", ("ssd", "nvme")),
	("Monitor", ("monitor", "display")),
	("Smartphone", ("smartphone", "celular", "iphone", "galaxy")),
	("Periféricos", ("teclado", "mouse", "headset", "webcam", "microfone")),
)


def classify_title(title: str) -> str:
	# Classifica o título usando regras ordenadas por prioridade.
	normalized_title = normalize_text(title)
	for category, keywords in RULES:
		if any(keyword in normalized_title for keyword in keywords):
			return category
	return "Outros"