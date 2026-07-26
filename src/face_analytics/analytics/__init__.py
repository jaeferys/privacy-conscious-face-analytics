"""Aggregate-only analytics models and services."""

from face_analytics.analytics.aggregator import AggregateAnalytics
from face_analytics.analytics.models import AggregateWindow, ZoneAggregate
from face_analytics.analytics.zones import PolygonZone, RectangleZone

__all__ = [
    "AggregateAnalytics",
    "AggregateWindow",
    "PolygonZone",
    "RectangleZone",
    "ZoneAggregate",
]
