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

app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)

blueprint = Blueprint('api', __name__)


@app.route("/")
def landing_page():
    # make dummy Landing Page data
    title = "Geofabric OGC API"
    description = "An OGC API and Linked Data API delivering information from the Australian Hydrological Geospatial " \
                  "Fabric (Geofabric) dataset"

    return LandingPageRenderer(request, title=title, description=description).render()


api = Api(app, doc="/doc", version='1.0', title="OGC LD API",
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
# @api.param()
class ConformanceRoute(Resource):
    def get(self):
        # make dummy Conformance Page data
        conformance_classes = [
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/oas30",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/html",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson"
        ]
        return ConformanceRenderer(request, conformance_classes).render()


@api.route("/collections")
class CollectionsRoute(Resource):
    def get(self):
        # make dummy Collections List data
        collections = [
            Collection("catch", title="Catchments", description="Hydrological Catchments"),
            Collection("riv", title="River Regions", description="A collection of Hydrological Catchments for a named river")
        ]
        return CollectionsRenderer(request, collections).render()


@api.route("/collections/<string:collection_id>")
@api.param("collection_id", "The ID of a Collection delivered by this API. See /collections for the list.")
class CollectionRoute(Resource):
    def get(self, collection_id):
        return render_template(
            "collection.html",
            collection_id=collection_id,
            collection_name="Grid " + str(collection_id)
        )


@api.route("/collections/<string:collection_id>/items")
@api.param("collection_id", "The ID of a Collection delivered by this API. See /collections for the list.")
class ItemsRoute(Resource):
    def get(self, collection_id):
        features = []

        return render_template(
            "items.html",
            collection_name="Grid " + str(collection_id),
            items=features,
            headers={"ContentType": "text/html"}
        )


@api.route("/collections/<string:collection_id>/items/<string:item_id>")
@api.param("collection_id", "The ID of a Collection delivered by this API. See /collections for the list.")
@api.param("item_id", "The ID of a Feature in this Collection's list of Items")
class ItemRoute(Resource):
    def get(self, collection_id, item_id):
        return "nothing"


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
