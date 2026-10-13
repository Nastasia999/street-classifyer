"""Context metrics: street wall, organisations, greenery, building age."""
from __future__ import annotations

import logging

import geopandas as gpd
import pandas as pd
import shapely

from ..tags import TagMatcher
from .base import (SegmentMetric, merge_intervals, nearest_assignment, pair_index,
                   pair_intersections)

log = logging.getLogger(__name__)


class FrontageMetric(SegmentMetric):
    """Street-wall continuity: share of the segment length lined by buildings.

    Buildings inside the side strip are projected onto the centreline; the
    covered length (union of projections) is divided by the segment length
    for each side, and the sides are averaged (only the outer side for a
    twinned carriageway).
    """

    name = "frontage"
    requires = ("buildings",)

    def compute(self) -> pd.DataFrame:
        segs = self.ctx.segments
        buffers = self.ctx.side_buffers(self.cfg.metrics.frontage.buffer_m)
        pairs = pair_intersections(buffers, self.ctx.layers.buildings())
        pairs = pairs[~shapely.is_empty(pairs["geometry"].values)]
        side_cover = pd.Series(0.0, index=pd.MultiIndex.from_frame(buffers[["seg_id", "side"]]))
        if not pairs.empty:
            coords, owner = shapely.get_coordinates(pairs["geometry"].values, return_index=True)
            seg_of_pair = buffers["seg_id"].to_numpy()[pairs["i"].to_numpy()]
            lines = segs.geometry.loc[seg_of_pair[owner]].values
            t = shapely.line_locate_point(lines, shapely.points(coords))
            proj = pd.DataFrame({"pair": owner, "t": t}).groupby("pair")["t"].agg(["min", "max"])
            proj["seg_id"] = seg_of_pair[proj.index]
            proj["side"] = buffers["side"].to_numpy()[pairs["i"].to_numpy()[proj.index]]
            covered = proj.groupby(["seg_id", "side"]).apply(
                lambda g: merge_intervals(list(zip(g["min"], g["max"]))), include_groups=False)
            side_cover.loc[covered.index] = covered
        ratio = side_cover / segs["length"].reindex(side_cover.index.get_level_values(0)).to_numpy()
        frontage = ratio.clip(upper=1.0).groupby(level=0).mean()
        return pd.DataFrame({"frontage": frontage.reindex(segs.index).fillna(0.0)})


class PoiDensityMetric(SegmentMetric):
    """Organisations (shops, offices, services, ...) per 100 m of segment."""

    name = "poi_density"
    requires = ("pois",)

    def compute(self) -> pd.DataFrame:
        mcfg = self.cfg.metrics.poi_density
        pois = self.ctx.layers.pois()
        if self.ctx.layers.source("pois").source == "osm":
            pois = pois[TagMatcher(mcfg.tags).mask(pois)].reset_index(drop=True)
        buffers = self.ctx.side_buffers(mcfg.buffer_m)
        pairs = nearest_assignment(pois, buffers, self.ctx.segments, mcfg.assignment)
        counts = pairs.groupby("seg_id").size()
        segs = self.ctx.segments
        return pd.DataFrame({
            "poi_count": counts.reindex(segs.index).fillna(0).astype(int),
            "poi_per_100m": self.ctx.per_100m(counts),
        })


class GreenAreaMetric(SegmentMetric):
    """Green area (m2) inside the segment strips, per 100 m of segment."""

    name = "green_area"
    requires = ("green",)

    def compute(self) -> pd.DataFrame:
        segs = self.ctx.segments
        green = self.ctx.layers.green()
        buffers = self.ctx.side_buffers(self.cfg.metrics.green_area.buffer_m)
        if green.empty:
            area = pd.Series(dtype=float)
        else:  # dissolve first: a lawn inside a park must not be counted twice
            parts = green.geometry.union_all()
            parts = gpd.GeoDataFrame(geometry=list(getattr(parts, "geoms", [parts])), crs=green.crs)
            parts = parts[parts.geom_type.isin(["Polygon", "MultiPolygon"])].reset_index(drop=True)
            pairs = pair_intersections(buffers, parts)
            pairs["area"] = shapely.area(pairs["geometry"].values)
            pairs["seg_id"] = buffers["seg_id"].to_numpy()[pairs["i"].to_numpy()]
            area = pairs.groupby("seg_id")["area"].sum()
        buffer_area = buffers.assign(a=buffers.area).groupby("seg_id")["a"].sum()
        return pd.DataFrame({
            "green_m2_per_100m": self.ctx.per_100m(area),
            "green_share": (area.reindex(segs.index).fillna(0) / buffer_area.reindex(segs.index)).fillna(0),
        })


class BuildingAgeMetric(SegmentMetric):
    """Median construction year / age of buildings within the segment strips.

    Dropped automatically when too few buildings in the study area have a
    known year (``min_coverage``): imputing the rest would invent a pattern.
    """

    name = "building_age"
    requires = ("buildings",)

    def compute(self) -> pd.DataFrame:
        mcfg = self.cfg.metrics.building_age
        segs = self.ctx.segments
        buildings = self.ctx.layers.buildings()
        in_area = buildings[buildings.intersects(self.ctx.area_polygon)] if len(buildings) else buildings
        coverage = float(in_area["year_built"].notna().mean()) if len(in_area) else 0.0
        self.ctx.quality["building_year_coverage"] = round(coverage, 3)
        if coverage < mcfg.min_coverage:
            log.warning("building_age: only %.0f%% of buildings have a construction year "
                        "(min_coverage %.0f%%) - metric dropped. Supply a buildings layer with "
                        "`year_built` to use it.", coverage * 100, mcfg.min_coverage * 100)
            self.ctx.quality["building_age"] = "dropped: low coverage"
            return pd.DataFrame(index=segs.index)
        dated = buildings[buildings["year_built"].notna()].reset_index(drop=True)
        buffers = self.ctx.side_buffers(mcfg.buffer_m)
        i, j = pair_index(buffers, dated)
        pairs = pd.DataFrame({"seg_id": buffers["seg_id"].to_numpy()[i], "b": j}).drop_duplicates()
        pairs["year"] = dated["year_built"].to_numpy()[pairs["b"]]
        year = pairs.groupby("seg_id")["year"].median()
        ref_year = mcfg.reference_year
        return pd.DataFrame({
            "building_year_median": year.reindex(segs.index),
            "building_age_median": (ref_year - year).reindex(segs.index),
        })
