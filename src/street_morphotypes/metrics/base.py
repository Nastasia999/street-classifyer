"""Shared machinery for segment metrics: context, side buffers, spatial pairing."""
from __future__ import annotations

import logging
import math
from abc import ABC, abstractmethod
from functools import cached_property
from typing import ClassVar

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

from ..config import CityConfig
from ..data.layers import LayerRepository
from ..network.segments import SegmentNetwork
from ..tags import parse_number

log = logging.getLogger(__name__)


class MetricContext:
    """Everything a metric may need; heavy intermediate results are computed once."""

    def __init__(self, cfg: CityConfig, network: SegmentNetwork, layers: LayerRepository) -> None:
        self.cfg = cfg
        self.network = network
        self.layers = layers
        self.quality: dict[str, object] = {}  # data-quality notes, exported with the results
        self._buffers: dict[float, gpd.GeoDataFrame] = {}

    @property
    def area_polygon(self):
        return self.layers.area.polygon

    @property
    def segments(self) -> gpd.GeoDataFrame:
        """Segments the metrics are computed for (the study area)."""
        return self.network.segments[self.network.segments["in_area"]]

    @cached_property
    def carriageway_lanes(self) -> pd.DataFrame:
        """Lanes of each segment's own carriageway: ``lanes_own``, ``lanes_imputed``."""
        segs = self.network.segments
        defaults = self.cfg.metrics.lanes.defaults_by_highway
        parsed = segs["lanes_raw"].map(parse_number)
        default = segs["highway"].map(defaults).astype(float)
        default = default.fillna(float(np.nanmedian(list(defaults.values()))))
        default = np.where(segs["oneway"], np.ceil(default / 2), default)
        lanes = parsed.fillna(pd.Series(default, index=segs.index)).clip(lower=1)
        return pd.DataFrame({"lanes_own": lanes, "lanes_imputed": parsed.isna()})

    def side_buffers(self, width: float) -> gpd.GeoDataFrame:
        """One-sided strips of ``width`` metres beyond the carriageway edge.

        Two strips (left, right) per segment; twinned carriageways of a divided
        road get only their outer strip. Columns: ``seg_id, side, geometry``.
        """
        if width not in self._buffers:
            segs = self.segments
            half_cw = self.carriageway_lanes.loc[segs.index, "lanes_own"].to_numpy() \
                * self.cfg.metrics.carriageway.lane_width_m / 2
            dist = half_cw + width
            geoms = segs.geometry.values
            frames = []
            for side, sign in (("left", 1.0), ("right", -1.0)):
                use = (segs["outer_side"].isna() | (segs["outer_side"] == side)).to_numpy()
                strips = shapely.buffer(geoms[use], sign * dist[use], single_sided=True)
                frames.append(gpd.GeoDataFrame(
                    {"seg_id": segs.index[use], "side": side}, geometry=strips, crs=segs.crs))
            buf = pd.concat(frames, ignore_index=True)
            self._buffers[width] = buf[~buf.geometry.is_empty].reset_index(drop=True)
        return self._buffers[width]

    def per_100m(self, values: pd.Series) -> pd.Series:
        length = self.segments["length"]
        return values.reindex(length.index).fillna(0) / (length / 100.0)


def pair_index(left: gpd.GeoDataFrame, right: gpd.GeoDataFrame,
               predicate: str = "intersects") -> tuple[np.ndarray, np.ndarray]:
    """Positional index pairs (i in left, j in right) satisfying ``predicate``."""
    if left.empty or right.empty:
        return np.empty(0, dtype=int), np.empty(0, dtype=int)
    i, j = right.sindex.query(left.geometry.values, predicate=predicate)  # (input, tree) positions
    return i, j


def pair_intersections(left: gpd.GeoDataFrame, right: gpd.GeoDataFrame) -> pd.DataFrame:
    """All intersecting pairs with their intersection geometry (columns ``i, j, geometry``)."""
    i, j = pair_index(left, right)
    inter = shapely.intersection(left.geometry.values[i], right.geometry.values[j])
    return pd.DataFrame({"i": i, "j": j, "geometry": inter})


def corridor_overlaps(segments: gpd.GeoDataFrame, lines: gpd.GeoDataFrame, tol: float,
                      min_share: float = 0.5) -> pd.DataFrame:
    """Segments running along lines: pairs (``seg_id``, line position ``j``, overlap ``length``)
    where at least ``min_share`` of the segment lies within ``tol`` metres of the line."""
    corridors = gpd.GeoDataFrame(geometry=lines.buffer(tol), crs=lines.crs)
    si, lj = pair_index(segments, corridors)
    inside = shapely.length(shapely.intersection(segments.geometry.values[si], corridors.geometry.values[lj]))
    pairs = pd.DataFrame({"seg_id": segments.index.to_numpy()[si], "j": lj, "length": inside})
    return pairs[inside >= min_share * segments["length"].to_numpy()[si]]


def nearest_assignment(points: gpd.GeoDataFrame, buffers: gpd.GeoDataFrame,
                       segments: gpd.GeoDataFrame, mode: str) -> pd.DataFrame:
    """Point-to-segment pairs (``point, seg_id``) for points inside the segment buffers.

    ``mode='nearest'`` keeps one segment per point (the closest centreline),
    ``mode='all'`` keeps every segment whose buffer contains the point.
    """
    bi, pj = pair_index(buffers, points, predicate="contains")
    pairs = pd.DataFrame({"point": pj, "seg_id": buffers["seg_id"].to_numpy()[bi]}).drop_duplicates()
    if mode == "nearest" and not pairs.empty:
        lines = segments.geometry.loc[pairs["seg_id"]].values
        pairs["dist"] = shapely.distance(points.geometry.values[pairs["point"]], lines)
        pairs = pairs.sort_values("dist").drop_duplicates("point")
    return pairs[["point", "seg_id"]]


class SegmentMetric(ABC):
    """A group of per-segment columns computed from one or more layers."""

    name: ClassVar[str]
    requires: ClassVar[tuple[str, ...]] = ()  # layer names

    def __init__(self, ctx: MetricContext) -> None:
        self.ctx = ctx
        self.cfg = ctx.cfg

    @property
    def enabled(self) -> bool:
        return getattr(self.cfg.metrics, self.name).enabled

    def missing_layers(self) -> list[str]:
        return [layer for layer in self.requires if not self.ctx.layers.available(layer)]

    @abstractmethod
    def compute(self) -> pd.DataFrame:
        """Return a frame indexed by ``seg_id`` (study-area segments)."""


def merge_intervals(intervals: list[tuple[float, float]]) -> float:
    """Total length covered by a set of 1-D intervals."""
    total, cur_start, cur_end = 0.0, -math.inf, -math.inf
    for a, b in sorted(intervals):
        if a > cur_end:
            if cur_end > cur_start:
                total += cur_end - cur_start
            cur_start, cur_end = a, b
        else:
            cur_end = max(cur_end, b)
    if cur_end > cur_start:
        total += cur_end - cur_start
    return total
