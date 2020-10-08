import os
from rdflib import Graph, Namespace, BNode
from rdflib.namespace import RDF, RDFS
from rdflib.plugins.stores.sparqlstore import SPARQLStore


APP_DIR = os.environ.get("APP_DIR", os.path.dirname(os.path.realpath(__file__)))
TEMPLATES_DIR = os.environ.get("TEMPLATES_DIR", os.path.join(APP_DIR, "view", "templates"))
STATIC_DIR = os.environ.get("STATIC_DIR", os.path.join(APP_DIR, "view", "style"))
LOGFILE = os.environ.get("LOGFILE", os.path.join(APP_DIR, "ogcapild.log"))
DEBUG = os.environ.get("DEBUG", True)
PORT = os.environ.get("PORT", 5000)
CACHE_HOURS = os.environ.get("CACHE_HOURS", 1)
CACHE_FILE = os.environ.get("CACHE_DIR", os.path.join(APP_DIR, "cache", "DATA.pickle"))
LOCAL_URIS = os.environ.get("LOCAL_URIS", True)

GEO = Namespace("http://www.opengis.net/ont/geosparql#")
GEOX = Namespace("https://linked.data.gov.au/def/geox#")
OGCAPI = Namespace("https://data.surroundaustralia.com/def/ogcapi/")
LANDING_PAGE_URL = "http://localhost:5000"
API_TITLE = "OGC LD API"
VERSION = "1.1"

DATASET_URI = "https://w3id.org/dggs/asgs2016"
SPARQL_ENDPOINT = "http://localhost:7200/repositories/asgs2016_dggs"


def get_graph():
    g = Graph("SPARQLStore")
    g.open(SPARQL_ENDPOINT)

    return g
