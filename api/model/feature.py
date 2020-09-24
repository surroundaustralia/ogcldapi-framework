from typing import List
from .profiles import *
from config import *
from .link import *
import json
from flask import Response, render_template
from .spatial_object import SpatialExtent, TemporalExtent
from rdflib import URIRef, Literal
from enum import Enum


class GeometryRole(Enum):
    Boundary = "http://linked.data.gov.au/def/geometry-roles/boundary"
    BoundingBox = "http://linked.data.gov.au/def/geometry-roles/bounding-box"
    BoundingCircle = "http://linked.data.gov.au/def/geometry-roles/bounding-circle"
    Concave = "http://linked.data.gov.au/def/geometry-roles/concave-hull"
    Convex = "http://linked.data.gov.au/def/geometry-roles/convex-hull"
    Centroid = "http://linked.data.gov.au/def/geometry-roles/centroid"
    Detailed = "http://linked.data.gov.au/def/geometry-roles/detailed"


class CRS(Enum):
    WGS84 = "http://www.opengis.net/def/crs/EPSG/0/4326"  # "http://epsg.io/4326"
    TB16PIX = "https://w3id.org/dggs/tb16pix"


class Geometry(object):
    def __init__(self, coordinates: str, role: GeometryRole, label: str, crs: CRS):
        self.coordinates = coordinates
        self.role = role
        self.label = label
        self.crs = crs

    def to_dict(self):
        return {
            "coordinates": self.coordinates,
            "role": self.role.value,
            "label": self.label,
            "crs": self.crs.value,
        }

    def to_geo_json_dict(self):
        """
        {
          "type": "Feature",
          "geometry": {
            "type": "LineString",
            "coordinates": [
              [102.0, 0.0], [103.0, 1.0], [104.0, 0.0], [105.0, 1.0]
            ]
          },
        """
        # this only works for WGS84 coordinates
        if self.crs == CRS.WGS84:
            # TODO: extend this to handle things other than Polygons
            coordinates = []
            for coordinate in self.coordinates.lstrip("MULTIPOLYGON (((").rstrip(")))").split(","):
                coordinates.append([coordinate.strip().split(" ")])
            return {
                "type": "Polygon",
                "coordinates": [
                    coordinates
                ]
            }
        else:
            return TypeError("Only WGS84 geometries can be serialised in GeoJSON")


class Feature(object):
    def __init__(
            self,
            uri: str,
            id: str,
            isPartOf: str,
            title: str = None,
            description: str = None,
            extent_spatial: SpatialExtent = None,
            extent_temporal: TemporalExtent = None,
            other_links: List[Link] = None,
            geometries: List[Geometry] = None
    ):
        self.uri = uri
        self.id = id
        self.isPartOf = isPartOf
        self.uri = LANDING_PAGE_URL + "/collections/" + self.isPartOf + "/item/" + id
        self.title = title
        self.description = description
        self.extent_spatial = extent_spatial
        self.extent_temporal = extent_temporal
        self.links = [
            Link(LANDING_PAGE_URL + "/collections/" + id + "/items",
                 rel=RelType.ITEMS.value,
                 type=MediaType.GEOJSON.value,
                 title=self.title)
        ]
        if other_links is not None:
            self.links.extend(other_links)
        self.geometries = geometries

    def to_dict(self):
        self.links = [x.__dict__ for x in self.links]
        if self.geometries is not None:
            self.geometries = [x.to_dict() for x in self.geometries]
        return self.__dict__

    def to_geo_json_dict(self):
        # this only serialises the Feature properties and WGS84 Geometries
        """
        {
          "type": "Feature",
          "geometry": {
            "type": "LineString",
            "coordinates": [
              [102.0, 0.0], [103.0, 1.0], [104.0, 0.0], [105.0, 1.0]
            ]
          },
        """
        geojson_geometry = [g.to_geo_json_dict() for g in self.geometries if g.crs == CRS.WGS84][0]  # one only

        properties = {
            "title": self.title,
            "isPartOf": self.isPartOf
        }
        if self.description is not None:
            properties["description"] = self.description

        return {
            "type": "Feature",
            "geometry": geojson_geometry,
            "properties": properties
        }


class FeatureRenderer(Renderer):
    def __init__(self, request, feature: Feature, other_links: List[Link] = None):
        self.feature = feature
        self.links = []
        if other_links is not None:
            self.links.extend(other_links)

        super().__init__(
            request,
            LANDING_PAGE_URL + "/collections/" + self.feature.isPartOf + "/item/" + self.feature.id,
            profiles={"oai": profile_openapi, "geosp": profile_geosparql},
            default_profile_token="oai"
        )

        self.ALLOWED_PARAMS = ["_profile", "_view", "_mediatype"]

    def render(self):
        for v in self.request.values.items():
            if v[0] not in self.ALLOWED_PARAMS:
                return Response("The parameter {} you supplied is not allowed".format(v[0]), status=400)

        # try returning alt profile
        response = super().render()
        if response is not None:
            return response
        elif self.profile == "oai":
            if self.mediatype == "application/json":
                return self._render_oai_json()
            else:
                return self._render_oai_html()
        elif self.profile == "geosp":
            return self._render_geosp_rdf()

    def _render_oai_json(self):
        page_json = {
            "links": [x.__dict__ for x in self.links],
            "feature": self.feature.to_geo_json_dict()
        }

        return Response(
            json.dumps(page_json),
            mimetype=str(MediaType.GEOJSON.value),
            headers=self.headers,
        )

    def _render_oai_html(self):
        _template_context = {
            "links": self.links,
            "feature": self.feature
        }

        return Response(
            render_template("feature.html", **_template_context),
            headers=self.headers,
        )

    def _render_geosp_rdf(self):
        g = Graph()
        g.bind("geo", GEO)
        g.bind("geox", GEOX)

        f = URIRef(self.feature.uri)
        g.add((
            f,
            RDF.type,
            GEO.Feature
        ))
        for geom in self.feature.geometries:
            this_geom = BNode()
            g.add((
                f,
                GEO.hasGeometry,
                this_geom
            ))
            g.add((
                this_geom,
                RDFS.label,
                Literal(geom.label)
            ))
            g.add((
                this_geom,
                GEOX.hasRole,
                URIRef(geom.role.value)
            ))
            g.add((
                this_geom,
                GEOX.inCRS,
                URIRef(geom.crs.value)
            ))
            if geom.crs == CRS.TB16PIX:
                g.add((
                    this_geom,
                    GEOX.asDGGS,
                    Literal(geom.coordinates, datatype=GEOX.DggsLiteral)
                ))
            else:  # WGS84
                g.add((
                    this_geom,
                    GEO.asWKT,
                    Literal(geom.coordinates, datatype=GEO.WktLiteral)
                ))

        # serialise in the appropriate RDF format
        if self.mediatype in ["application/rdf+json", "application/json"]:
            return Response(g.serialize(format="json-ld"), mimetype=self.mediatype)
        elif self.mediatype in Renderer.RDF_MEDIA_TYPES:
            return Response(g.serialize(format=self.mediatype), mimetype=self.mediatype)
        else:
            return Response(
                "The Media Type you requested cannot be serialized to",
                status=400,
                mimetype="text/plain"
            )
