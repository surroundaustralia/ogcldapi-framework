from pyldapi import Renderer, ContainerRenderer
from typing import List
from .profiles import *
from config import *
from .link import *
from .collection import Collection
from .feature import Feature
import json
from flask import Response, render_template
from flask_paginate import Pagination
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCAT, DCTERMS, RDF
import re


class FeaturesList:
    def __init__(self, request, collection_id):
        self.request = request
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
        self.collection = Collection(collection_id)
        for s in graph.subjects(predicate=DCTERMS.identifier, object=Literal(collection_id)):
            collection_uri = s
            for p, o in graph.predicate_objects(subject=s):
                if p == DCTERMS.title:
                    self.collection.title = str(o)
                elif p == DCTERMS.description:
                    self.collection.description = str(o)

        # get list of Features within this Collection
        features_uris = []
        # filter if we have a filtering param
        if request.values.get("bbox") is not None:
            # work out what sort of BBOX filter it is and filter by that type
            features_uris = self.get_feature_uris_by_bbox()
        else:
            # all features in list
            for s in graph.subjects(predicate=DCTERMS.isPartOf, object=collection_uri):
                features_uris.append(s)

        self.collection.feature_count = len(features_uris)
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
            features.append(
                Feature(str(s), f["id"], str(collection_uri), title=f["title"], description=f["description"]))

        self.collection.features = features

    def get_feature_uris_by_bbox(self):
        allowed_bbox_formats = {
            "coords": r"([0-9\.\-]+),([0-9\.\-]+),([0-9\.\-]+),([0-9\.\-]+)",  # Lat Longs, e.g. 160.6,-55.95,-170,-25.89
            "cell_id": r"([A-Z][0-9]{0,15})$",  # single DGGS Cell ID, e.g. R1234
            "cell_ids": r"([A-Z][0-9]{0,15}),([A-Z][0-9]{0,15})",  # two DGGS cells, e.g. R123,R456
        }
        self.bbox_type = None
        for k, v in allowed_bbox_formats.items():
            if re.match(v, self.request.values.get("bbox")):
                self.bbox_type = k

        if self.bbox_type is None:
            return None
        elif self.bbox_type == "coords":
            return self._get_filtered_features_list_bbox_wgs84()
        elif self.bbox_type == "cell_id":
            return self._get_filtered_features_list_bbox_dggs()
        elif self.bbox_type == "cell_ids":
            pass

    def _get_filtered_features_list_bbox_wgs84(self):
        parts = self.request.values.get("bbox").split(",")

        demo = """
            149.041411262992398 -35.292795884738389, 
            149.041411262992398 -35.141378579917053, 
            149.314863045854082 -35.141378579917053,
            149.314863045854082 -35.292795884738389,
            149.041411262992398 -35.292795884738389
            """

        q = """
            PREFIX dcterms: <http://purl.org/dc/terms/>
            PREFIX geo: <http://www.opengis.net/ont/geosparql#>
            PREFIX geof: <http://www.opengis.net/def/function/geosparql/>
            PREFIX ogcapi: <https://data.surroundaustralia.com/def/ogcapi/>

            SELECT ?f
            WHERE {{
                ?f a ogcapi:Feature ;
                   dcterms:isPartOf <https://linked.data.gov.au/dataset/asgs2016/statisticalarealevel1/> ;            
                   geo:hasGeometry/geo:asWKT ?wkt .
    
                FILTER (geof:sfWithin(?wkt, 
                    '''
                    <http://www.opengis.net/def/crs/OGC/1.3/CRS84>
                    POLYGON ((
                        {tl_lon} {tl_lat}, 
                        {tl_lon} {br_lat}, 
                        {br_lon} {br_lat},
                        {br_lon} {tl_lat},
                        {tl_lon} {tl_lat}
                    ))
                    '''^^geo:wktLiteral))
            }}
            ORDER BY ?f
            """.format(**{
            "tl_lon": parts[0],
            "tl_lat": parts[1],
            "br_lon": parts[2],
            "br_lat": parts[3]
        })
        print(q)
        # TODO: update as RDFlib updates
        # for r in get_graph().query(q):
        #     features_uris.append((r["f"], r["prefLabel"]))
        from SPARQLWrapper import SPARQLWrapper, JSON
        sparql = SPARQLWrapper(SPARQL_ENDPOINT)
        sparql.setQuery(q)
        sparql.setReturnFormat(JSON)
        ret = sparql.queryAndConvert()["results"]["bindings"]
        return [URIRef(r["f"]["value"]) for r in ret]

    def _get_filtered_features_list_bbox_dggs(self):
        # # geo:sfIntersects - any Cell of the Feature is within the BBox
        # q = """
        #     PREFIX dcterms: <http://purl.org/dc/terms/>
        #     PREFIX geo: <http://www.opengis.net/ont/geosparql#>
        #     PREFIX geox: <http://linked.data.gov.au/def/geox#>
        #     PREFIX ogcapi: <https://data.surroundaustralia.com/def/ogcapi/>
        #
        #     SELECT ?f
        #     WHERE {{
        #         ?f a ogcapi:Feature ;
        #            dcterms:isPartOf <https://linked.data.gov.au/dataset/asgs2016/statisticalarealevel1/> .
        #         ?f geo:hasGeometry/geox:asDGGS ?dggs .
        #
        #         BIND (STRAFTER(STR(?dggs), "> ") AS ?coords)
        #
        #         FILTER CONTAINS(?coords, "{}")
        #     }}
        #     """.format(self.request.values.get("bbox"))
        # # TODO: update as RDFlib updates
        # # for r in get_graph().query(q):
        # #     features_uris.append((r["f"], r["prefLabel"]))
        # from SPARQLWrapper import SPARQLWrapper, JSON
        # sparql = SPARQLWrapper(SPARQL_ENDPOINT)
        # sparql.setQuery(q)
        # sparql.setReturnFormat(JSON)
        # ret = sparql.queryAndConvert()["results"]["bindings"]
        # return [URIRef(r["f"]["value"]) for r in ret]

        # geo:sfWithin - every Cell of the Feature is within the BBox
        q = """
            PREFIX dcterms: <http://purl.org/dc/terms/>
            PREFIX geo: <http://www.opengis.net/ont/geosparql#>
            PREFIX geox: <http://linked.data.gov.au/def/geox#>
            PREFIX ogcapi: <https://data.surroundaustralia.com/def/ogcapi/>            
            
            SELECT ?f ?coords
            WHERE {
                ?f a ogcapi:Feature ;
                   dcterms:isPartOf <https://linked.data.gov.au/dataset/asgs2016/statisticalarealevel1/> .
                ?f geo:hasGeometry/geox:asDGGS ?dggs .
    
                BIND (STRAFTER(STR(?dggs), "> ") AS ?coords)
            }
            """
        from SPARQLWrapper import SPARQLWrapper, JSON
        sparql = SPARQLWrapper(SPARQL_ENDPOINT)
        sparql.setQuery(q)
        sparql.setReturnFormat(JSON)
        ret = sparql.queryAndConvert()["results"]["bindings"]
        feature_ids = []
        for r in ret:
            within = True
            for cell in r["coords"]["value"].split(" "):
                if not str(cell).startswith(self.request.values.get("bbox")):
                    within = False
                    break
            if within:
                feature_ids.append(URIRef(r["f"]["value"]))

        return feature_ids

    def _get_filtered_features_list_bbox_paging(self):
        pass


class FeaturesRenderer(ContainerRenderer):
    def __init__(self, request, collection_id, other_links: List[Link] = None):
        self.request = request
        self.valid = self._valid_parameters()
        if self.valid[0]:
            self.links = [
                Link(
                    LANDING_PAGE_URL + "/collections.json",
                    rel=RelType.SELF.value,
                    type=MediaType.JSON.value,
                    title="This Document"
                ),
                Link(
                    LANDING_PAGE_URL + "/collections.html",
                    rel=RelType.SELF.value,
                    type=MediaType.HTML.value,
                    title="This Document in HTML"
                ),
            ]
            if other_links is not None:
                self.links.extend(other_links)

            self.feature_list = FeaturesList(request, collection_id)

            super().__init__(
                request,
                LANDING_PAGE_URL + "/collections/" + self.feature_list.collection.id + "/items",
                "Features",
                "The Features of Collection {}".format(self.feature_list.collection.id),
                None,
                None,
                [(LANDING_PAGE_URL + "/collections/" + self.feature_list.collection.id + "/items/" + x.id, x.title) for x in self.feature_list.collection.features],
                self.feature_list.collection.feature_count,
                profiles={"oai": profile_openapi},
                default_profile_token="oai"
            )

    def _valid_parameters(self):
        allowed_params = ["_profile", "_view", "_mediatype", "_format", "page", "per_page", "limit", "bbox"]

        allowed_bbox_formats = [
            r"([0-9\.\-]+),([0-9\.\-]+),([0-9\.\-]+),([0-9\.\-]+)",  # Lat Longs, e.g. 160.6,-55.95,-170,-25.89
            r"([A-Z][0-9]{0,15})$",  # single DGGS Cell ID, e.g. R1234
            r"([A-Z][0-9]{0,15}),([A-Z][0-9]{0,15})",  # two DGGS cells, e.g. R123,R456
        ]

        for p in self.request.values.keys():
            if p not in allowed_params:
                return False, \
                       "The parameter {} you supplied is not allowed. " \
                       "For this API endpoint, you may only use one of '{}'".format(p, "', '".join(allowed_params)),

        if self.request.values.get("limit") is not None:
            try:
                int(self.request.values.get("limit"))
            except ValueError:
                return False, "The parameter 'limit' you supplied is invalid. It must be an integer"

        if self.request.values.get("bbox") is not None:
            for p in allowed_bbox_formats:
                if re.match(p, self.request.values.get("bbox")):
                    return True, None
            return False, "The parameter 'bbox' you supplied is invalid. Must be either two pairs of long/lat values, " \
                          "a DGGS Cell ID or a pair of DGGS Cell IDs"

        return True, None

    def render(self):
        # return without rendering anything if there is an error with the parameters
        if not self.valid[0]:
            return Response(
                self.valid[1],
                status=400,
                mimetype="text/plain"
            )

        # try returning alt profile
        response = super().render()
        if response is not None:
            return response

        elif self.profile == "oai":
            if self.mediatype == "application/json":
                return self._render_oai_json()
            else:
                return self._render_oai_html()

    def _render_oai_json(self):
        page_json = {
            "links": [x.__dict__ for x in self.links],
            "collection": self.feature_list.collection.to_dict(),
        }

        return Response(
            json.dumps(page_json),
            mimetype=str(MediaType.JSON.value),
            headers=self.headers,
        )

    def _render_oai_html(self):
        page = (
            int(self.request.values.get("page"))
            if self.request.values.get("page") is not None
            else 1
        )
        per_page = (
            int(self.request.values.get("per_page"))
            if self.request.values.get("per_page") is not None
            else 20
        )
        limit = int(self.request.values.get("limit")) if self.request.values.get("limit") is not None else None

        pagination = Pagination(page=page, per_page=per_page, total=limit if limit is not None else self.feature_list.collection.feature_count)

        _template_context = {
            "links": self.links,
            "collection": self.feature_list.collection,
            "pagination": pagination
        }

        if self.request.values.get("bbox") is not None:  # it it exists at this point, it must be valid
            _template_context["bbox"] = (self.feature_list.bbox_type, self.request.values.get("bbox"))

        return Response(
            render_template("features.html", **_template_context),
            headers=self.headers,
        )
