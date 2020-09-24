from typing import List
from .profiles import *
from config import *
from .link import *
import json
from flask import Response, render_template
from .spatial_object import SpatialExtent, TemporalExtent


class Feature(object):
    def __init__(
            self,
            id: str,
            isPartOf: str,
            title: str = None,
            description: str = None,
            extent_spatial: SpatialExtent = None,
            extent_temporal: TemporalExtent = None,
            other_links: List[Link] = None,
            geometries: List[tuple] = None
    ):
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
        return self.__dict__


class FeatureRenderer(Renderer):
    def __init__(self, request, feature: Feature, other_links: List[Link] = None):
        self.feature = feature
        self.links = []
        if other_links is not None:
            self.links.extend(other_links)

        super().__init__(
            request,
            LANDING_PAGE_URL + "/collections/" + self.feature.isPartOf + "/item/" + self.feature.id,
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
            "feature": self.feature.to_dict()
        }

        return Response(
            json.dumps(page_json),
            mimetype=str(MediaType.JSON.value),
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
