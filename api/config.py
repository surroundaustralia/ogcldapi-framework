import os
from rdflib import Graph, Namespace
__version__ = "1.2"
GEO = Namespace("http://www.opengis.net/ont/geosparql#")
GEOX = Namespace("https://linked.data.gov.au/def/geox#")
OGCAPI = Namespace("https://data.surroundaustralia.com/def/ogcapi/")

APP_DIR = os.getenv("APP_DIR", os.path.dirname(os.path.realpath(__file__)))
TEMPLATES_DIR = os.getenv("TEMPLATES_DIR", os.path.join(APP_DIR, "view", "templates"))
STATIC_DIR = os.getenv("STATIC_DIR", os.path.join(APP_DIR, "view", "style"))
LOGFILE = os.getenv("LOGFILE", os.path.join(APP_DIR, "ogcapild.log"))
DEBUG = os.getenv("DEBUG", True)
PORT = os.getenv("PORT", 5000)
CACHE_HOURS = os.getenv("CACHE_HOURS", 1)
CACHE_FILE = os.getenv("CACHE_DIR", os.path.join(APP_DIR, "cache", "DATA.pickle"))
LOCAL_URIS = os.getenv("LOCAL_URIS", True)

LANDING_PAGE_URL = os.getenv("LANDING_PAGE_URL", "http://localhost:5000")
API_TITLE = os.getenv("API_TITLE", "OGC LD API")
VERSION = os.getenv("VERSION", __version__)
DATASET_URI = os.getenv("DATASET_URI", "https://example.org/dataset/x")
SPARQL_ENDPOINT = os.getenv("SPARQL_ENDPOINT", "http://example.org/service/sparql")


def get_graph():
    g = Graph("SPARQLStore")
    g.open(SPARQL_ENDPOINT)

    return g
