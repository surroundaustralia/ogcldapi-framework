import os

APP_DIR = os.environ.get("APP_DIR", os.path.dirname(os.path.realpath(__file__)))
TEMPLATES_DIR = os.environ.get("TEMPLATES_DIR", os.path.join(APP_DIR, "view", "templates"))
STATIC_DIR = os.environ.get("STATIC_DIR", os.path.join(APP_DIR, "view", "style"))
LOGFILE = os.environ.get("LOGFILE", os.path.join(APP_DIR, "catprez.log"))
DEBUG = os.environ.get("DEBUG", True)
PORT = os.environ.get("PORT", 5000)
CACHE_HOURS = os.environ.get("CACHE_HOURS", 1)
CACHE_FILE = os.environ.get("CACHE_DIR", os.path.join(APP_DIR, "cache", "DATA.pickle"))
LOCAL_URIS = os.environ.get("LOCAL_URIS", True)

LANDING_PAGE_URL = "http://localhost:5000"
API_TITLE = "Geofabric OGC LD API"
VERSION = "1.1"
