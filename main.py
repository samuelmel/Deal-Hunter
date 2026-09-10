import os

from dotenv import load_dotenv

from app.services.monitor import monitor_kabum


if __name__ == "__main__":
	load_dotenv()
	result = monitor_kabum(os.getenv("DEAL_HUNTER_QUERY", "ssd 1tb"))
	print(result)
