"""Segment metrics. Add a new metric by subclassing ``SegmentMetric`` and listing it in ``METRICS``."""
from .base import MetricContext, SegmentMetric
from .context import BuildingAgeMetric, FrontageMetric, GreenAreaMetric, PoiDensityMetric
from .extra import ExtraFeatureJoiner
from .landuse import BuildingFunctionClassifier, LandUseMetric
from .transport import LanesMetric, MaxspeedMetric, TransitMetric

# Order matters only for readability of the output table.
METRICS: list[type[SegmentMetric]] = [
    LanesMetric,
    MaxspeedMetric,
    TransitMetric,
    FrontageMetric,
    PoiDensityMetric,
    GreenAreaMetric,
    BuildingAgeMetric,
    LandUseMetric,
]

__all__ = [
    "METRICS", "MetricContext", "SegmentMetric", "ExtraFeatureJoiner", "BuildingFunctionClassifier",
    "LanesMetric", "MaxspeedMetric", "TransitMetric", "FrontageMetric", "PoiDensityMetric",
    "GreenAreaMetric", "BuildingAgeMetric", "LandUseMetric",
]
