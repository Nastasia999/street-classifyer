"""Functional mix: residential / commercial / social / industrial shares of floor area.

OSM has no floor-area-by-use data, so it is estimated per building:

1. Floor area (GFA) = footprint area x floors. Floors come from
   ``building:levels``, else ``height / floor_height_m``, else the city median
   for the same building type (if enough samples), else a configured default.
2. Function, first rule that answers wins:
   user ``function`` column -> ``building`` tag (``building:use`` if
   ``building=yes``) -> tags on the footprint itself (``amenity=school``) ->
   majority category of POIs inside the footprint -> land-use polygon around
   the building -> ``unknown``.
3. Mixed use: a residential building with commercial/social POIs inside gets
   its ground floor (1 / floors of its GFA) assigned to that category.

Shares are computed over the floor area with a known function; the unknown
share is reported separately and turns the context block to ``C_null`` when it
exceeds ``max_unknown_share``. These are estimates — see METHODOLOGY.md.
"""
from __future__ import annotations

import logging

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

from ..config import LandUseConfig
from ..tags import TagClassifier, ValueMapClassifier
from .base import SegmentMetric, pair_index, pair_intersections

log = logging.getLogger(__name__)

UNKNOWN = "unknown"
_MIXED_TARGETS = ("commercial", "social")


class BuildingFunctionClassifier:
    """Estimates floors, floor area and function of every building."""

    def __init__(self, cfg: LandUseConfig) -> None:
        self.cfg = cfg
        self.by_building_tag = ValueMapClassifier("building_type", cfg.building_tags)
        self.by_tags = TagClassifier(cfg.poi_tags)
        self.by_landuse = TagClassifier(cfg.landuse_tags)

    def classify(self, buildings: gpd.GeoDataFrame, pois: gpd.GeoDataFrame,
                 landuse: gpd.GeoDataFrame, pois_osm: bool, landuse_osm: bool) -> pd.DataFrame:
        b = pd.DataFrame(index=buildings.index)
        b["footprint"] = buildings.geometry.area
        b["levels"], b["levels_imputed"] = self._levels(buildings)
        b["gfa"] = b["footprint"] * b["levels"]

        poi_cat = self._poi_categories(buildings, pois, pois_osm)
        own_tags = self.by_tags.classify(buildings)
        steps = [
            ("user", buildings["function"].astype("object")),
            ("building_tag", self.by_building_tag.classify(buildings)),
            ("own_tags", own_tags),
            ("poi_inside", poi_cat["majority"]),
            ("landuse", self._landuse_categories(buildings, landuse, landuse_osm)),
        ]
        func = pd.Series(pd.NA, index=b.index, dtype="object")
        source = pd.Series("none", index=b.index, dtype="object")
        for name, cats in steps:
            take = func.isna() & cats.notna()
            func[take] = cats[take]
            source[take] = name
        b["function"] = func.fillna(UNKNOWN)
        b["function_source"] = source

        b["ground_function"] = pd.NA
        if self.cfg.mixed_use_ground_floor:
            ground = poi_cat["mixed"].where(poi_cat["mixed"].notna(),
                                            own_tags.where(own_tags.isin(_MIXED_TARGETS)))
            mixed = (b["function"] == "residential") & ground.notna()
            b.loc[mixed, "ground_function"] = ground[mixed]
        return b

    def parts(self, b: pd.DataFrame) -> pd.DataFrame:
        """Long table (building, category, gfa) with mixed-use ground floors split off."""
        share = np.where(b["ground_function"].notna(), 1.0 / b["levels"], 0.0)
        main = pd.DataFrame({"building": b.index, "category": b["function"],
                             "gfa": b["gfa"] * (1 - share)})
        mixed = b["ground_function"].notna()
        ground = pd.DataFrame({"building": b.index[mixed], "category": b.loc[mixed, "ground_function"],
                               "gfa": (b["gfa"] * share)[mixed]})
        return pd.concat([main, ground], ignore_index=True)

    # ── Steps ────────────────────────────────────────────────────────────────

    def _levels(self, buildings: gpd.GeoDataFrame) -> tuple[pd.Series, pd.Series]:
        levels = buildings["levels"].astype(float)
        from_height = (buildings["height_m"].astype(float) / self.cfg.floor_height_m).round()
        levels = levels.fillna(from_height.where(from_height >= 1))
        imputed = levels.isna()
        btype = buildings["building_type"].astype("object")
        known = pd.DataFrame({"t": btype, "l": levels}).dropna()
        stats = known.groupby("t")["l"].agg(["median", "size"])
        medians = stats.loc[stats["size"] >= self.cfg.min_level_samples, "median"]
        defaults = self.cfg.default_levels
        levels = (levels.fillna(btype.map(medians))
                  .fillna(btype.map(defaults))
                  .fillna(defaults["_default"]))
        return levels.clip(lower=1), imputed

    def _poi_categories(self, buildings: gpd.GeoDataFrame, pois: gpd.GeoDataFrame,
                        pois_osm: bool) -> pd.DataFrame:
        out = pd.DataFrame({"majority": pd.NA, "mixed": pd.NA}, index=buildings.index, dtype="object")
        if pois.empty:
            return out
        if pois_osm:
            cats = self.by_tags.classify(pois)
        elif "category" in pois:
            cats = pois["category"].astype("object").where(pois["category"].isin(self.cfg.categories))
        else:
            return out
        bi, pj = pair_index(buildings, pois, predicate="contains")
        pairs = pd.DataFrame({"b": buildings.index.to_numpy()[bi], "cat": cats.to_numpy()[pj]}).dropna()
        if pairs.empty:
            return out
        counts = pairs.groupby(["b", "cat"]).size().rename("n").reset_index()
        counts = counts.sort_values(["b", "n"], ascending=[True, False])
        out.loc[:, "majority"] = counts.drop_duplicates("b").set_index("b")["cat"].reindex(out.index)
        mixed = counts[counts["cat"].isin(_MIXED_TARGETS)].drop_duplicates("b").set_index("b")["cat"]
        out.loc[:, "mixed"] = mixed.reindex(out.index)
        return out

    def _landuse_categories(self, buildings: gpd.GeoDataFrame, landuse: gpd.GeoDataFrame,
                            landuse_osm: bool) -> pd.Series:
        out = pd.Series(pd.NA, index=buildings.index, dtype="object")
        if landuse.empty:
            return out
        if landuse_osm:
            cats = self.by_landuse.classify(landuse)
        elif "category" in landuse:
            cats = landuse["category"].astype("object").where(landuse["category"].isin(self.cfg.categories))
        else:
            return out
        valid = cats.notna().to_numpy()
        polys = landuse[valid].reset_index(drop=True)
        cats = cats[valid].reset_index(drop=True)
        points = gpd.GeoDataFrame(geometry=buildings.geometry.representative_point(), crs=buildings.crs)
        pi, lj = pair_index(points, polys, predicate="within")
        pairs = pd.DataFrame({"b": buildings.index.to_numpy()[pi], "cat": cats.to_numpy()[lj],
                              "area": polys.geometry.area.to_numpy()[lj]})
        smallest = pairs.sort_values("area").drop_duplicates("b").set_index("b")["cat"]  # most specific
        return smallest.reindex(out.index).astype("object")


class LandUseMetric(SegmentMetric):
    """Floor-area shares of functions within the segment strips."""

    name = "land_use"
    requires = ("buildings",)

    def compute(self) -> pd.DataFrame:
        mcfg = self.cfg.metrics.land_use
        layers = self.ctx.layers
        segs = self.ctx.segments
        buildings = layers.buildings()
        clf = BuildingFunctionClassifier(mcfg)
        b = clf.classify(buildings, layers.pois(), layers.landuse(),
                         pois_osm=layers.source("pois").source == "osm",
                         landuse_osm=layers.source("landuse").source == "osm")
        self._report_quality(b)

        buffers = self.ctx.side_buffers(mcfg.buffer_m)
        pairs = pair_intersections(buffers, buildings)
        pairs["seg_id"] = buffers["seg_id"].to_numpy()[pairs["i"].to_numpy()]
        pairs["building"] = buildings.index.to_numpy()[pairs["j"].to_numpy()]
        pairs["frac"] = shapely.area(pairs["geometry"].values) / b["footprint"].reindex(pairs["building"]).to_numpy()
        parts = clf.parts(b)
        gfa = (pairs[["seg_id", "building", "frac"]]
               .merge(parts, on="building")
               .assign(gfa=lambda d: d["gfa"] * d["frac"].clip(upper=1))
               .pivot_table(index="seg_id", columns="category", values="gfa", aggfunc="sum", fill_value=0)
               .reindex(segs.index, fill_value=0))

        total = gfa.sum(axis=1)
        unknown = gfa[UNKNOWN] if UNKNOWN in gfa else pd.Series(0.0, index=segs.index)
        known = total - unknown
        out = pd.DataFrame(index=segs.index)
        for cat in mcfg.categories:
            col = gfa[cat] if cat in gfa else 0.0
            out[f"fn_{cat}"] = np.where(known > 0, col / known.where(known > 0, 1), 0.0)
        out["fn_unknown"] = np.where(total > 0, unknown / total.where(total > 0, 1), 0.0)
        out["gfa_total_m2"] = total
        out["no_buildings"] = total == 0
        out["context_null"] = out["fn_unknown"] > mcfg.max_unknown_share
        n_null = int(out["context_null"].sum())
        if n_null:
            log.warning("land_use: %d segments have > %.0f%% unknown-function floor area -> C_null",
                        n_null, mcfg.max_unknown_share * 100)
        return out

    def _report_quality(self, b: pd.DataFrame) -> None:
        q = self.ctx.quality
        q["building_levels_imputed_share"] = round(float(b["levels_imputed"].mean()), 3) if len(b) else None
        by_source = b.groupby("function_source")["gfa"].sum()
        q["building_function_source_gfa_share"] = (by_source / by_source.sum()).round(3).to_dict() \
            if len(b) else {}
        by_func = b.groupby("function")["gfa"].sum()
        q["building_function_gfa_share"] = (by_func / by_func.sum()).round(3).to_dict() if len(b) else {}
        q["mixed_use_buildings"] = int(b["ground_function"].notna().sum())
