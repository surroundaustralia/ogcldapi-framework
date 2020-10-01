from typing import List
from .profiles import *
from config import *
from .link import *
import json
from flask import Response, render_template
from .spatial_object import SpatialExtent, TemporalExtent
from .feature import Feature
import markdown


class Collection(object):
    def __init__(
            self,
            id: str,
            title: str = None,
            description: str = None,
            extent_spatial: SpatialExtent = None,
            extent_temporal: TemporalExtent = None,
            other_links: List[Link] = None,
            features: List[Feature] = None,
            feature_count: int = None
    ):
        self.id = id
        self.uri = LANDING_PAGE_URL + "/collections/" + id
        self.title = title
        self.description = markdown.markdown(description) if description is not None else None
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
        self.features = features
        if feature_count is not None:
            self.feature_count = feature_count
        elif self.features is not None:
            self.feature_count = len(self.features)
        else:
            self.feature_count = None

    def to_dict(self):
        self.links = [x.__dict__ for x in self.links]
        if self.features is not None:
            self.features = [x.to_dict() for x in self.features]

        return self.__dict__


class CollectionRenderer(Renderer):
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
            LANDING_PAGE_URL + "/collection/" + self.collection.id,
            profiles={"oai": profile_openapi},
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

    def _render_oai_json(self):
        page_json = {
            "links": [x.__dict__ for x in self.links],
            "collection": self.collection.to_dict()
        }

        return Response(
            json.dumps(page_json),
            mimetype=str(MediaType.JSON.value),
            headers=self.headers,
        )

    def _render_oai_html(self):
        _template_context = {
            "links": self.links,
            "collection": self.collection
        }

        return Response(
            render_template("collection.html", **_template_context),
            headers=self.headers,
        )
