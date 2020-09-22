from typing import List
from .link import *
from config import *


class SpatialExtent:
    def __init__(self):
        self.bbox = ""


class TemporalExtent:
    def __init__(self):
        self.interval = ""


class Collection(object):
    def __init__(
            self,
            id: str,
            title: str = None,
            description: str = None,
            extent_spatial: SpatialExtent = None,
            extent_temporal: TemporalExtent = None,
            other_links: List[Link] = None
    ):
        self.id = id
        self.uri = LANDING_PAGE_URL + "/collections/" + id
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

    def to_dict(self):
        self.links = [x.__dict__ for x in self.links]
        return self.__dict__
