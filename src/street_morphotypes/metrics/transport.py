"""Transport metrics from OSM attributes: lanes, speed limit, public transport."""
from __future__ import annotations

import logging

import geopandas as gpd
import pandas as pd

from ..tags import TagMatcher, parse_maxspeed
from .base import SegmentMetric, corridor_overlaps, nearest_assignment

log = logging.getLogger(__name__)


def _with_twin(values: pd.Series, segs: pd.DataFrame) -> pd.Series:
    """Add the twin carriageway's value (divided roads count as one cross-section)."""
    twin_vals = segs["twin_id"].map(values).astype(float).fillna(0.0)
    return values.reindex(segs.index) + twin_vals


class LanesMetric(SegmentMetric):
    """Total lanes across the street (both carriageways of a divided road).

    Missing ``lanes`` tags are filled from ``defaults_by_highway``
    (``lanes_imputed`` marks them).
    """

    name = "lanes"

    def compute(self) -> pd.DataFrame:
        segs = self.ctx.segments
        own = self.ctx.carriageway_lanes
        lanes = _with_twin(own["lanes_own"], segs)
        self.ctx.quality["lanes_imputed_share"] = round(float(own.loc[segs.index, "lanes_imputed"].mean()), 3)
        return pd.DataFrame({"lanes": lanes, "lanes_imputed": own.loc[segs.index, "lanes_imputed"]})


class MaxspeedMetric(SegmentMetric):
    """Speed limit, km/h (zone codes and mph converted; gaps filled by highway class)."""

    name = "maxspeed"

    def compute(self) -> pd.DataFrame:
        mcfg = self.cfg.metrics.maxspeed
        segs = self.ctx.segments
        parsed = segs["maxspeed_raw"].map(lambda v: parse_maxspeed(v, mcfg.zone_values))
        default = segs["highway"].map(mcfg.defaults_by_highway).astype(float)
        self.ctx.quality["maxspeed_imputed_share"] = round(float(parsed.isna().mean()), 3)
        return pd.DataFrame({"maxspeed": parsed.fillna(default), "maxspeed_imputed": parsed.isna()})


class TransitMetric(SegmentMetric):
    """Public transport routes along the segment and stops per 100 m.

    Routes are matched by OSM way id (exact) or, for networks from a file,
    geometrically. Route variants and directions sharing a ``ref`` count once;
    the two carriageways of a divided road share their routes.
    """

    name = "transit"
    requires = ("transit_routes",)

    def compute(self) -> pd.DataFrame:
        segs = self.ctx.segments
        out = pd.DataFrame(index=segs.index)
        out["pt_routes"] = self._route_counts(self.ctx.layers.transit_routes())
        if self.ctx.layers.available("transit_stops"):
            stops = self._merged_stops(self.ctx.layers.transit_stops())
            buffers = self.ctx.side_buffers(self.cfg.metrics.transit.stops_buffer_m)
            pairs = nearest_assignment(stops, buffers, segs, "nearest")
            counts = pairs.groupby("seg_id").size()
            out["pt_stops"] = counts.reindex(segs.index).fillna(0).astype(int)
            out["pt_stops_per_100m"] = self.ctx.per_100m(counts)
        return out

    def _route_counts(self, routes: gpd.GeoDataFrame) -> pd.Series:
        all_segs = self.ctx.network.segments
        segs = self.ctx.segments
        if routes.empty:
            return pd.Series(0, index=segs.index)
        has_way_ids = routes["way_id"].notna().all() and all_segs["osm_ways"].map(len).gt(0).any()
        keys = self._keys_by_way(routes) if has_way_ids else self._keys_by_geometry(routes)
        keys = keys.reindex(all_segs.index)
        twin = segs["twin_id"]
        counts = []
        for sid in segs.index:
            own = keys.at[sid] if isinstance(keys.at[sid], set) else set()
            tid = twin.at[sid]
            if tid >= 0 and isinstance(keys.at[tid], set):
                own = own | keys.at[tid]
            counts.append(len(own))
        return pd.Series(counts, index=segs.index)

    def _keys_by_way(self, routes: gpd.GeoDataFrame) -> pd.Series:
        way_keys = routes.groupby(routes["way_id"].astype("int64"))["route_key"].agg(set)
        ways = self.ctx.network.segments["osm_ways"].explode().dropna().astype("int64")
        matched = ways.map(way_keys).dropna()
        return matched.groupby(level=0).agg(lambda s: set().union(*s))

    def _keys_by_geometry(self, routes: gpd.GeoDataFrame) -> pd.Series:
        lines = routes.dissolve("route_key").reset_index()
        pairs = corridor_overlaps(self.ctx.segments, lines, self.cfg.metrics.transit.geometric_match_m)
        pairs["key"] = lines["route_key"].to_numpy()[pairs["j"].to_numpy()]
        return pairs.groupby("seg_id")["key"].agg(set)

    def _merged_stops(self, stops: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        tcfg = self.cfg.metrics.transit
        if self.ctx.layers.source("transit_stops").source == "osm":
            stops = stops[TagMatcher(tcfg.stop_tags).mask(stops)]
        if stops.empty or tcfg.stop_merge_distance_m == 0:
            return stops.reset_index(drop=True)
        merged = stops.buffer(tcfg.stop_merge_distance_m / 2).union_all()
        parts = list(getattr(merged, "geoms", [merged]))
        return gpd.GeoDataFrame(geometry=[p.centroid for p in parts], crs=stops.crs)
