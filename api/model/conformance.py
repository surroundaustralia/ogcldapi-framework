from .link import *
from flask import Response, render_template
from .profiles import *
from config import *
import json


class ConformanceRenderer(Renderer):
    def __init__(
            self,
            request,
            conformance_classes):

        self.conformance_classes = conformance_classes

        super().__init__(request, LANDING_PAGE_URL + "/conformance", {"oai": profile_openapi}, "oai")

    def render(self):
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
            "links": self.conformance_classes
        }

        return Response(
            json.dumps(page_json),
            mimetype=str(MediaType.JSON.value),
            headers=self.headers,
        )

    def _render_oai_html(self):
        _template_context = {
            "uri": LANDING_PAGE_URL + "/conformance",
        }

        return Response(
            render_template("conformance.html", **_template_context),
            headers=self.headers,
        )

