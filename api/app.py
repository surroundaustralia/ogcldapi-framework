import logging
from flask import (
    Flask,
    request,
    render_template,
    url_for,
    jsonify,
    Blueprint,
    Response
)
from flask_restx import Namespace, reqparse, Api, Resource
from config import *
from pyldapi import Renderer
from model import *
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCAT, DCTERMS, RDF

app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)

blueprint = Blueprint('api', __name__)


@app.route("/")
def landing_page():
    # make dummy Landing Page data
    title = "Geofabric OGC API"
    description = "An OGC API and Linked Data API delivering information from the Australian Hydrological Geospatial " \
                  "Fabric (Geofabric) dataset"
    q = """
        # Get Dataset
        PREFIX ogcapi: <https://data.surroundaustralia.com/def/ogcapi/>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        
        SELECT ?uri ?title ?description
        WHERE {
            ?uri a ogcapi:OgcApi ;
                 dcterms:title ?title ;
                 dcterms:description ?description
        }
        """
    graph = get_graph()

    for s in graph.subjects(predicate=RDF.type, object=DCAT.Dataset):
        for p, o in graph.predicate_objects(subject=s):
            if p == DCTERMS.title:
                title = str(o)
            elif p == DCTERMS.description:
                description = str(o)

    return LandingPageRenderer(request, title=title, description=description).render()


api = Api(app, doc="/doc/", version='1.0', title="OGC LD API",
          description="Open API Documentation for this {}".format(API_TITLE))
# sapi = Namespace('oai', description="Search from DGGS Engine", version="1.0")
# api.add_namespace(sapi)
app.register_blueprint(blueprint)


@app.context_processor
def context_processor():
    """
    A set of variables available globally for all Jinja templates.
    :return: A dictionary of variables
    :rtype: dict
    """
    MEDIATYPE_NAMES = {
        "text/html": "HTML",
        "application/json": "JSON",
        "application/geo+json": "GeoJSON",
        "text/turtle": "Turtle",
        "application/rdf+xml": "RDX/XML",
        "application/ld+json": "JSON-LD",
        "text/n3": "Notation-3",
        "application/n-triples": "N-Triples",
    }

    return dict(
        LOCAL_URIS=LOCAL_URIS,
        MEDIATYPE_NAMES=MEDIATYPE_NAMES,
        API_TITLE=API_TITLE,
    )


@api.route("/spec")
class Spec(Resource):
    def get(self):
        return api.__schema__


@api.route("/conformance")
class ConformanceRoute(Resource):
    def get(self):
        q = """
            PREFIX dcterms: <http://purl.org/dc/terms/>
            PREFIX ogcapi: <https://data.surroundaustralia.com/def/ogcapi/>
            
            SELECT *
            WHERE {
                ?uri a ogcapi:ConformanceTarget ;
                   dcterms:title ?title
            }
            """
        graph = get_graph()
        conformance_classes = []
        for s in graph.subjects(predicate=RDF.type, object=OGCAPI.ConformanceTarget):
            uri = str(s)
            for o in graph.objects(subject=s, predicate=DCTERMS.title):
                title = str(o)
            conformance_classes.append((uri, title))
        return ConformanceRenderer(request, conformance_classes).render()


@api.route("/collections")
class CollectionsRoute(Resource):
    def get(self):
        collections = []
        q = """
            PREFIX ogcapi: <https://data.surroundaustralia.com/def/ogcapi/>
            PREFIX dcterms: <http://purl.org/dc/terms/>
            
            SELECT ?uri ?identifier ?title ?description
            WHERE {{
                ?uri a ogcapi:Collection ;
                     dcterms:isPartOf <{}> ;
                     dcterms:identifier ?identifier ;
                     dcterms:title ?title ;
                     dcterms:description ?description .
            }}
            ORDER BY ?identifier 
            """.format(DATASET_URI)
        graph = get_graph()
        candidates = []
        for s in graph.subjects(predicate=RDF.type, object=OGCAPI.Collection):
            candidates.append(s)
        for candidate in candidates:
            if not (candidate, DCTERMS.isPartOf, URIRef(DATASET_URI)) in graph:
                candidates.remove(candidate)
        for candidate in candidates:
            for p, o in graph.predicate_objects(subject=candidate):
                if p == DCTERMS.identifier:
                    identifier = str(o)
                elif p == DCTERMS.title:
                    title = str(o)
                elif p == DCTERMS.description:
                    description = str(o)

            collections.append(Collection(identifier, title=title, description=description))

        return CollectionsRenderer(request, collections).render()


@api.route("/collections/<string:collection_id>")
@api.param("collection_id", "The ID of a Collection delivered by this API. See /collections for the list.")
class CollectionRoute(Resource):
    def get(self, collection_id):
        c = Collection(collection_id)
        q = """
            # Get Collection
            PREFIX ogcapi: <https://data.surroundaustralia.com/def/ogcapi/>
            PREFIX dcterms: <http://purl.org/dc/terms/>
            
            SELECT ?uri ?title ?description
            WHERE {{
                ?uri a ogcapi:Collection ;
                     dcterms:identifier "{}" ;
                     dcterms:title ?title ;
                     dcterms:description ?description .
            }}
            """.format(collection_id)

        graph = get_graph()
        for s in graph.subjects(predicate=DCTERMS.identifier, object=Literal(collection_id)):
            for p, o in graph.predicate_objects(subject=s):
                if p == DCTERMS.title:
                    c.title = str(o)
                elif p == DCTERMS.description:
                    c.description = str(o)

            return CollectionRenderer(request, c).render()


@api.route("/collections/<string:collection_id>/items")
@api.param("collection_id", "The ID of a Collection delivered by this API. See /collections for the list.")
class FeaturesRoute(Resource):
    def get(self, collection_id):
        page = (
            int(request.values.get("page")) if request.values.get("page") is not None else 1
        )
        per_page = (
            int(request.values.get("per_page"))
            if request.values.get("per_page") is not None
            else 20
        )
        # limit
        limit = int(request.values.get("limit")) if request.values.get("limit") is not None else None

        # if limit is set, ignore page & per_page
        if limit is not None:
            start = 0
            end = limit
        else:
            # generate list for requested page and per_page
            start = (page - 1) * per_page
            end = start + per_page

        print("start / end")
        print("{} / {}".format(start, end))

        q = """
            PREFIX ogcapi: <https://data.surroundaustralia.com/def/ogcapi/>
            PREFIX dcterms: <http://purl.org/dc/terms/>

            SELECT ?uri ?identifier ?title ?description ?id
            WHERE {{
                ?uri a ogcapi:Feature ;
                      dcterms:isPartOf <{}> ;
                      dcterms:identifier ?identifier .
                BIND (STR(?identifier) AS ?id)
                OPTIONAL {{?uri dcterms:title ?title}}
                OPTIONAL {{?uri dcterms:description ?description}}
            }}
            ORDER BY ?identifier
            """.format(collection_id)
        graph = get_graph()

        # get Collection info
        collection = Collection(collection_id)
        for s in graph.subjects(predicate=DCTERMS.identifier, object=Literal(collection_id)):
            collection_uri = s
            for p, o in graph.predicate_objects(subject=s):
                if p == DCTERMS.title:
                    collection.title = str(o)
                elif p == DCTERMS.description:
                    collection.description = str(o)

        # get list of Features within this Collection
        features_uris = []
        for s in graph.subjects(predicate=DCTERMS.isPartOf, object=collection_uri):
            features_uris.append(s)

        collection.feature_count = len(features_uris)
        # truncate the list of Features to this page
        page = features_uris[start:end]

        # Features - only this page's
        features = []
        for s in page:
            f = {
                "id": None,
                "title": None,
                "description": None,
            }
            for p, o in graph.predicate_objects(subject=s):
                if p == DCTERMS.identifier:
                    f["id"] = str(o)
                elif p == DCTERMS.title:
                    f["title"] = str(o)
                elif p == DCTERMS.description:
                    f["description"] = str(o)
            features.append(Feature(str(s), f["id"], str(collection_uri), title=f["title"], description=f["description"]))

        collection.features = features

        return FeaturesRenderer(request, collection).render()


@api.route("/collections/<string:collection_id>/items/<string:item_id>")
@api.param("collection_id", "The ID of a Collection delivered by this API. See /collections for the list.")
@api.param("item_id", "The ID of a Feature in this Collection's list of Items")
class FeatureRoute(Resource):
    def get(self, collection_id, item_id):
        q = """
            PREFIX dcterms: <http://purl.org/dc/terms/>
            PREFIX ogcapi: <https://data.surroundaustralia.com/def/ogcapi/>
            
            SELECT ?identifier ?title ?description
            WHERE {{
                ?uri a ogcapi:Feature ;
                   dcterms:isPartOf <{}> ;
                   dcterms:identifier ?identifier ;
                   OPTIONAL {{?uri dcterms:title ?title}}
                   OPTIONAL {{?uri dcterms:description ?description}}
            }}
            """.format(collection_id)

        graph = get_graph()
        for s in graph.subjects(predicate=DCTERMS.identifier, object=Literal(item_id)):
            feature = Feature(str(s), item_id, collection_id)
            for p, o in graph.predicate_objects(subject=s):
                if p == DCTERMS.title:
                    feature.title = str(o)
                elif p == DCTERMS.description:
                    feature.description = str(o)
            # out of band call for Geometries as BNodes not supported by SPARQLStore
            q = """
                PREFIX geo: <http://www.opengis.net/ont/geosparql#>
                PREFIX geox: <http://linked.data.gov.au/def/geox#>
                SELECT * 
                WHERE {{
                    <https://linked.data.gov.au/dataset/geofabric/contractedcatchment/{}>
                        geo:hasGeometry/geo:asWKT ?g1 ;
                        geo:hasGeometry/geox:asDGGS ?g2 .
                }}
                """.format(item_id)
            from SPARQLWrapper import SPARQLWrapper, JSON
            sparql = SPARQLWrapper(SPARQL_ENDPOINT)
            sparql.setQuery(q)
            sparql.setReturnFormat(JSON)
            ret = sparql.queryAndConvert()["results"]["bindings"]
            feature.geometries = [
                Geometry(ret[0]["g1"]["value"], GeometryRole.Boundary, "WGS84 Geometry", CRS.WGS84),
                Geometry(ret[0]["g2"]["value"], GeometryRole.Boundary, "TB16Pix Geometry", CRS.TB16PIX),
            ]

            return FeatureRenderer(request, feature).render()


@api.route("/object")
class ObjectRoute(Resource):
    def get(self):
        return "nothing"


def render_api_error(title, status, message, mediatype="text/html"):
    if mediatype == "application/json":
        return jsonify({
            "title": title,
            "status": status,
            "message": message
        }), status
    elif mediatype in Renderer.RDF_MEDIA_TYPES:
        pass
    else:  # mediatype == "text/html":
        return render_template(
            "error.html",
            title=title,
            status=status,
            message=message
        ), status


if __name__ == "__main__":
    logging.basicConfig(
        filename=LOGFILE,
        level=logging.DEBUG,
        datefmt="%Y-%m-%d %H:%M:%S",
        format="%(asctime)s %(levelname)s %(filename)s:%(lineno)s %(message)s",
    )

    app.run(debug=DEBUG, threaded=True, port=PORT)
