import os


PANDASCORE_TOKEN = os.environ.get("PANDASCORE_TOKEN", "").strip()
PANDASCORE_BASE_URL = os.environ.get("PANDASCORE_BASE_URL", "https://api.pandascore.co").rstrip("/")

SITE_NAME = os.environ.get("SITE_NAME", "Esports Matches")
SITE_URL = os.environ.get("SITE_URL", "http://localhost:8000").rstrip("/")
SITE_LOGO_URL = os.environ.get("SITE_LOGO_URL", "").strip()

TIMEZONE = os.environ.get("TIMEZONE", "Europe/Moscow")

# Where we store cached JSON and generated HTML
DATA_DIR = os.environ.get("DATA_DIR", "data")
GENERATED_DIR = os.environ.get("GENERATED_DIR", "generated")

# Safety limits to avoid runaway pagination
MAX_PAGES = int(os.environ.get("MAX_PAGES", "10"))
PAGE_SIZE = int(os.environ.get("PAGE_SIZE", "50"))
