from pyldapi import Renderer, ContainerRenderer
from typing import List
from .profiles import *
from config import *
from .link import *
from .collection import Collection
import json
from flask import Response, render_template
from flask_paginate import Pagination


class FeaturesRenderer(ContainerRenderer):
    def __init__(self, request, collection: Collection, other_links: List[Link] = None):
        self.collection = collection
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

        super().__init__(
            request,
            LANDING_PAGE_URL + "/collections/" + self.collection.id + "/items",
            "Features",
            "The Features of Collection {}".format(self.collection.id),
            None,
            None,
            [(LANDING_PAGE_URL + "/collections/" + self.collection.id + "/items/" + x.id, x.title) for x in self.collection.features],
            self.collection.feature_count,
            profiles={"oai": profile_openapi},
            default_profile_token="oai"
        )

        self.ALLOWED_PARAMS = ["_profile", "_view", "_mediatype", "_format", "page", "per_page"]

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
            "collection": self.collection.to_dict(),
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

        pagination = Pagination(page=page, per_page=per_page, total=self.collection.feature_count)

        _template_context = {
            "links": self.links,
            "collection": self.collection,
            "pagination": pagination
        }

        return Response(
            render_template("features.html", **_template_context),
            headers=self.headers,
        )
