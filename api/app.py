import logging
import markdown
from flask import (
    Flask,
    request,
    render_template,
    Markup,
    g,
    redirect,
    url_for,
    jsonify,
)
from config import *
from pyldapi import Renderer, ContainerRenderer
from model import *

app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)


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
    )


@app.route("/")
def landing_page():
    # make dummy Landing Page data
    title = "Geofabric OGC API"
    description = "An OGC API and Linked Data API delivering information from the Australian Hydrological Geospatial " \
                  "Fabric (Geofabric) dataset"

    return LandingPageRenderer(request, title=title, description=description).render()


@app.route("/api")
def api_def():
    return "API def dummy"


@app.route("/api.html")
def api_doc():
    return "API doc dummy"


@app.route("/conformance")
def conformance():
    # make dummy Conformance Page data
    conformance_classes = [
        "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
        "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/oas30",
        "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/html",
        "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson"
    ]
    return ConformanceRenderer(request, conformance_classes).render()


@app.route("/collections")
def collections():
    # make dummy Collections List data
    collections = [
        Collection("catch", title="Catchments", description="Hydrological Catchments"),
        Collection("riv", title="River Regions", description="A collection of Hydrological Catchments for a named river")
    ]
    return CollectionsRenderer(request, collections).render()


@app.route("/collections/<string:collection_id>")
def collection(collection_id):
    if int(collection_id[-1]) not in range(10):
        return render_api_error(
            "Invalid Collection ID",
            400,
            "The Collection ID must be one of 'level{}'".format("', 'level".join([str(x) for x in range(10)]))
        )
    return render_template(
        "collection.html",
        collection_id=collection_id,
        collection_name="Grid " + str(collection_id)
    )


@app.route("/collections/<string:collection_id>/items")
def items(collection_id):
    features = []
    for cell in TB16Pix.grid(int(collection_id[-1])):
        if LOCAL_URIS:
            features.append((
                url_for("item", collection_id=collection_id, item_id=str(cell)),
                "Cell {}".format(str(cell))
            ))
        else:
            features.append((
                URI_BASE_CELL[str(cell)],
                "Cell {}".format(str(cell))
            ))

    return render_template(
        "items.html",
        collection_name="Grid " + str(collection_id),
        items=features
    )


@app.route("/collections/<string:collection_id>/items/<string:item_id>")
def item(collection_id, item_id):
    item_id = item_id.split("?")[0]
    if item_id == "Earth":
        return EarthRenderer(request, item_id).render()
    else:
        return CellRenderer(request, item_id).render()


@app.route("/object")
def object():
    return None


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
