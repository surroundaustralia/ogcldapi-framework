from pyldapi import Renderer, ContainerRenderer
from typing import List
from .profiles import *
from config import *
from .link import *
from .collection import Collection
import json
from flask import Response, render_template
from flask_paginate import Pagination
from rdflib import URIRef
from rdflib.namespace import DCTERMS, RDF


class CollectionsList:
    def __init__(self, request):
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

        self.collections = []
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

            self.collections.append(Collection(identifier, title=title, description=description))


class CollectionsRenderer(ContainerRenderer):
    def __init__(self, request, other_links: List[Link] = None):
        self.id = id
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

        self.collections = CollectionsList(request).collections

        super().__init__(
            request,
            LANDING_PAGE_URL + "/collections",
            "Collections",
            "The Collections of Features delivered by this OGC API instance",
            None,
            None,
            [(LANDING_PAGE_URL + "/collections/items/" + x.id, x.title) for x in self.collections],
            len(self.collections),
            profiles={"oai": profile_openapi},
            default_profile_token="oai"
        )

        self.ALLOWED_PARAMS = ["_profile", "_view", "_mediatype", "_format", "page", "per_page", "limit", "bbox"]

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

    def _render_oai_json(self):
        page_json = {
            "links": [x.__dict__ for x in self.links],
            "collections": [x.to_dict() for x in self.collections]
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

        pagination = Pagination(page=page, per_page=per_page, total=limit if limit is not None else len(self.collections))

        _template_context = {
            "links": self.links,
            "collections": self.collections,
            "pagination": pagination
        }

        return Response(
            render_template("collections_oai.html", **_template_context),
            headers=self.headers,
        )
