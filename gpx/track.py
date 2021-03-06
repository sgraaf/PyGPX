"""This module provides a Track object to contain GPX routes - an ordered list of points describing a path."""
from typing import Dict, List, Optional, Tuple

from lxml import etree

from .waypoint import Waypoint
from ._parsers import parse_links


class Track:
    """A track class for the GPX data format.

    Args:
        trk (etree.Element, optional): The track XML element. Defaults to None.
    """

    def __init__(self, trk: Optional[etree._Element] = None) -> None:
        self._trk: etree._Element = trk
        self._nsmap: Optional[Dict[str, str]] = None
        self.name: Optional[str] = None
        self.cmt: Optional[str] = None
        self.desc: Optional[str] = None
        self.src: Optional[str] = None
        self.links: List[Dict[str, str]] = []
        self.number: Optional[int] = None
        self.type: Optional[str] = None
        self.segments: List[List[Waypoint]] = []

        if self._trk is not None:
            self._parse()

    def _parse(self) -> None:
        # namespaces
        self._nsmap = self._trk.nsmap

        # name
        if (name := self._trk.find("name", namespaces=self._nsmap)) is not None:
            self.name = name.text
        # comment
        if (cmt := self._trk.find("cmt", namespaces=self._nsmap)) is not None:
            self.cmt = cmt.text
        # description
        if (desc := self._trk.find("desc", namespaces=self._nsmap)) is not None:
            self.desc = desc.text
        # source of data
        if (src := self._trk.find("src", namespaces=self._nsmap)) is not None:
            self.src = src.text
        # links to additional info
        self.links = parse_links(self._trk)
        # GPS track number
        if (number := self._trk.find("number", namespaces=self._nsmap)) is not None:
            self.number = int(number.text)
        # track type (classification)
        if (_type := self._trk.find("type", namespaces=self._nsmap)) is not None:
            self.type = _type.text

        # segments
        for trkseg in self._trk.iterfind("trkseg", namespaces=self._nsmap):
            self.segments.append(
                [
                    Waypoint(trkpt)
                    for trkpt in trkseg.iterfind("trkpt", namespaces=self._nsmap)
                ]
            )

    def _build(self) -> etree._Element:
        track = etree.Element("trk", nsmap=self._nsmap)

        if self.name is not None:
            name = etree.SubElement(track, "name", nsmap=self._nsmap)
            name.text = self.name

        if self.cmt is not None:
            cmt = etree.SubElement(track, "cmt", nsmap=self._nsmap)
            cmt.text = self.cmt

        if self.desc is not None:
            desc = etree.SubElement(track, "desc", nsmap=self._nsmap)
            desc.text = self.desc

        if self.src is not None:
            src = etree.SubElement(track, "src", nsmap=self._nsmap)
            src.text = self.src

        for _link in self.links:
            link = etree.SubElement(track, "link", nsmap=self._nsmap)
            link.set("href", _link["href"])
            if (tag := "text") in _link:
                text = etree.SubElement(link, tag, nsmap=self._nsmap)
                text.text = _link[tag]
            if (tag := "type") in _link:
                _type = etree.SubElement(link, tag, nsmap=self._nsmap)
                _type.text = _link[tag]

        if self.number is not None:
            number = etree.SubElement(track, "number", nsmap=self._nsmap)
            number.text = self.number

        if self.type is not None:
            _type = etree.SubElement(track, "type", nsmap=self._nsmap)
            _type.text = self.type

        for _segment in self.segments:
            segment = etree.SubElement(track, "trkseg", nsmap=self._nsmap)
            for _trkpt in _segment:
                segment.append(_trkpt._build(tag="trkpt"))

        return track

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        """Returns the bounds of the track."""
        return (
            min(point.lat for segment in self.segments for point in segment),
            min(point.lon for segment in self.segments for point in segment),
            max(point.lat for segment in self.segments for point in segment),
            max(point.lon for segment in self.segments for point in segment),
        )

    @property
    def distance(self) -> float:
        """Returns the distance of the track (in metres)."""
        _distance = 0.0
        for segment in self.segments:
            for i, point in enumerate(segment[:-1]):
                _distance += point.distance_to(segment[i + 1])
        return round(_distance, 2)

    @property
    def duration(self) -> float:
        """Returns the duration of the track (in seconds)."""
        _duration = 0.0
        for segment in self.segments:
            for i, point in enumerate(segment[:-1]):
                _duration += point.duration_to(segment[i + 1])
        return _duration
