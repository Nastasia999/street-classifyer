"""Input layers: OSM downloads or user files, cached and standardised.

Every layer leaves this module in the study area's projected CRS and with a
standard schema, so the metrics never care where the data came from.

Standard schemas (columns besides geometry):

- buildings      ``building_type, levels, height_m, year_built, function`` + raw tag columns
- pois           raw tag columns (+ ``category`` for user files)
- landuse        raw tag columns (+ ``category`` for user files)
- green          (geometry only is used)
- transit_routes ``route_key, way_id`` (``way_id`` is empty for user files)
- transit_stops  (geometry only is used)
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import LineString, box

from ..area import StudyArea
from ..config import CityConfig, LayerSource
from ..tags import merge_tag_specs, parse_number, parse_year
from .overpass import EmptyResponse, OverpassClient

log = logging.getLogger(__name__)

_POLYGONS = ("Polygon", "MultiPolygon")
_STOP_ROLES = {"stop", "platform", "stop_entry_only", "stop_exit_only",
               "platform_entry_only", "platform_exit_only"}


class LayerRepository:
    """Single access point to all input layers of one city (download -> cache -> standardise)."""

    def __init__(self, cfg: CityConfig, area: StudyArea) -> None:
        self.cfg = cfg
        self.area = area
        self.cache_dir = cfg.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.overpass = OverpassClient(cfg.overpass, http_cache_dir=str(self.cache_dir / "http"))
        self._memo: dict[str, gpd.GeoDataFrame] = {}

    # ── Tag sets per layer ───────────────────────────────────────────────────

    @property
    def _poi_tags(self) -> dict:
        m = self.cfg.metrics
        return merge_tag_specs(m.poi_density.tags, *m.land_use.poi_tags.values())

    @property
    def _landuse_tags(self) -> dict:
        return merge_tag_specs(*self.cfg.metrics.land_use.landuse_tags.values())

    @property
    def _building_keys(self) -> list[str]:
        m = self.cfg.metrics
        keys = ["building", "building:use", "building:levels", "height", "building:height", "name"]
        return list(dict.fromkeys(keys + m.building_age.osm_tags + list(self._poi_tags)))

    # ── Public API ───────────────────────────────────────────────────────────

    def source(self, layer: str) -> LayerSource:
        return getattr(self.cfg.layers, layer)

    def available(self, layer: str) -> bool:
        return self.source(layer).source != "none"

    def buildings(self) -> gpd.GeoDataFrame:
        return self._get("buildings", self._load_buildings)

    def pois(self) -> gpd.GeoDataFrame:
        return self._get("pois", lambda: self._load_features(
            "pois", self._poi_tags, ["name"], geom="point"))

    def landuse(self) -> gpd.GeoDataFrame:
        return self._get("landuse", lambda: self._load_features(
            "landuse", self._landuse_tags, [], geom="polygon"))

    def green(self) -> gpd.GeoDataFrame:
        return self._get("green", lambda: self._load_features(
            "green", self.cfg.metrics.green_area.tags, [], geom="polygon"))

    def transit_stops(self) -> gpd.GeoDataFrame:
        return self._get("transit_stops", lambda: self._load_features(
            "transit_stops", self.cfg.metrics.transit.stop_tags, ["name"], geom="point"))

    def transit_routes(self) -> gpd.GeoDataFrame:
        return self._get("transit_routes", self._load_transit_routes)

    def network_lines(self) -> gpd.GeoDataFrame:
        """User-supplied network lines (``layers.network.source == 'file'``)."""
        src = self.source("network")
        gdf = self._read_file(src, extent=self.area.network_polygon)
        return gdf[gdf.geometry.geom_type.isin(["LineString", "MultiLineString"])]

    def osm_network_graph(self):
        """OSM drive network (unprojected, simplified) for the network extent.

        The cache keeps the unsimplified graph. Simplification joins ways only
        where nothing else meets and the street name stays the same: the graph
        holds the drivable classes only, so a node that looks like a pass-through
        may be where a driveway or footway joins, and a change of name marks it
        as the end of a street. One-way/two-way changes always stay nodes.
        """
        import osmnx as ox

        G = self._osm_network_raw()
        return ox.simplify_graph(G, edge_attrs_differ=["name"])

    def _osm_network_raw(self):
        import osmnx as ox

        path = self.cache_dir / "network_raw.graphml"
        net = self.cfg.network
        filt = '["highway"~"^({})$"]'.format("|".join(net.highway_types))
        filt += '["area"!~"yes"]'
        if net.exclude_access:
            filt += '["access"!~"^({})$"]'.format("|".join(net.exclude_access))
        polygon = self._wgs84_extent(self.area.network_polygon)
        if self._cache_is_current(path, {"extent": self._bounds(polygon), "filter": filt}):
            log.info("Network: cache %s", path)
            return ox.load_graphml(path)
        log.info("Network: downloading from OSM ...")
        G = self.overpass.call(
            ox.graph_from_polygon, polygon, custom_filter=filt,
            simplify=False, retain_all=False, truncate_by_edge=True,
        )
        ox.save_graphml(G, path)
        return G

    def prefetch(self) -> None:
        """Download every OSM layer used by the config (for the `fetch` command)."""
        if self.source("network").source == "osm":
            self.osm_network_graph()
        for layer in ("buildings", "pois", "landuse", "green", "transit_stops", "transit_routes"):
            if self.available(layer):
                getattr(self, layer)()

    # ── Loading helpers ──────────────────────────────────────────────────────

    def _get(self, layer: str, loader) -> gpd.GeoDataFrame:
        if layer not in self._memo:
            if not self.available(layer):
                self._memo[layer] = gpd.GeoDataFrame(geometry=[], crs=self.area.crs)
            else:
                gdf = loader()
                log.info("%s: %d features", layer, len(gdf))
                self._memo[layer] = gdf
        return self._memo[layer]

    def _wgs84_extent(self, geom):
        """Bounding box of an extent in WGS84: Overpass answers bbox queries much faster than
        polygon queries; features are clipped to the real extent afterwards."""
        return box(*self.area.to_wgs84(geom).bounds)

    @staticmethod
    def _bounds(geom) -> list[float]:
        return [round(v, 6) for v in geom.bounds]

    @staticmethod
    def _cache_is_current(path: Path, fingerprint: dict) -> bool:
        """True if ``path`` was downloaded with the same extent and filters.

        The fingerprint (extent, tags, kept columns, network filter) is stored next
        to the cached file; when the config changes, the layer is downloaded again
        instead of silently reusing data for another extent or tag set.
        """
        meta = path.with_name(path.name + ".source.json")
        current = json.loads(json.dumps(fingerprint, sort_keys=True, default=str))
        if not path.exists():
            meta.write_text(json.dumps(current, indent=1, sort_keys=True), encoding="utf-8")
            return False
        if not meta.exists():  # cache from an older version: adopt it once
            log.info("%s has no download fingerprint; assuming it matches the current settings", path.name)
            meta.write_text(json.dumps(current, indent=1, sort_keys=True), encoding="utf-8")
            return True
        if json.loads(meta.read_text(encoding="utf-8")) == current:
            return True
        log.warning("%s was downloaded with other settings (extent, tags or filters changed): "
                    "downloading again", path.name)
        path.unlink()
        meta.write_text(json.dumps(current, indent=1, sort_keys=True), encoding="utf-8")
        return False

    def _cached_osm(self, layer: str, download, fingerprint: dict) -> gpd.GeoDataFrame:
        """Load ``<cache>/<layer>.gpkg`` or download, keep it, return in WGS84."""
        path = self.cache_dir / f"{layer}.gpkg"
        if self._cache_is_current(path, fingerprint):
            log.info("%s: cache %s", layer, path)
            return gpd.read_file(path)
        log.info("%s: downloading from OSM ...", layer)
        gdf = download()
        gdf.to_file(path, driver="GPKG")
        return gdf

    def _download_features(self, tags: dict, keep: list[str], extent) -> gpd.GeoDataFrame:
        import osmnx as ox
        try:
            gdf = self.overpass.call(ox.features_from_polygon, self._wgs84_extent(extent), tags)
        except EmptyResponse:
            return gpd.GeoDataFrame({k: pd.Series(dtype="string") for k in keep},
                                    geometry=[], crs=4326)
        gdf = gdf.reset_index()
        gdf["osm_id"] = gdf["element"].str[0] + gdf["id"].astype(str)
        cols = ["osm_id"] + [c for c in keep if c in gdf.columns]
        return gdf[cols + ["geometry"]]

    def _load_features(self, layer: str, tags: dict, extra_keys: list[str],
                       geom: str) -> gpd.GeoDataFrame:
        src = self.source(layer)
        if src.source == "file":
            gdf = self._read_file(src, extent=self.area.context_polygon)
        else:
            keep = list(dict.fromkeys(list(tags) + extra_keys))
            extent = self._bounds(self._wgs84_extent(self.area.context_polygon))
            gdf = self._cached_osm(
                layer, lambda: self._download_features(tags, keep, self.area.context_polygon),
                {"extent": extent, "tags": tags, "keep": keep})
            gdf = gdf.to_crs(self.area.crs)
            gdf = gdf[gdf.intersects(self.area.context_polygon)]
        if geom == "polygon":
            gdf = gdf[gdf.geometry.geom_type.isin(_POLYGONS)].copy()
            gdf["geometry"] = gdf.geometry.make_valid()
            gdf = gdf[gdf.geometry.geom_type.isin(_POLYGONS + ("GeometryCollection",))]
        elif geom == "point":
            gdf = gdf[~gdf.geometry.is_empty].copy()
            gdf["geometry"] = gdf.geometry.representative_point()
        return gdf.reset_index(drop=True)

    def _load_buildings(self) -> gpd.GeoDataFrame:
        src = self.source("buildings")
        if src.source == "file":
            gdf = self._read_file(src, extent=self.area.context_polygon)
            gdf = gdf[gdf.geometry.geom_type.isin(_POLYGONS)].copy()
            return self._standardise_user_buildings(gdf)
        extent = self._bounds(self._wgs84_extent(self.area.context_polygon))
        gdf = self._cached_osm("buildings", lambda: self._download_features(
            {"building": True}, self._building_keys, self.area.context_polygon),
            {"extent": extent, "tags": {"building": True}, "keep": self._building_keys})
        gdf = gdf.to_crs(self.area.crs)
        gdf = gdf[gdf.geometry.geom_type.isin(_POLYGONS) & gdf.intersects(self.area.context_polygon)].copy()
        return self._standardise_osm_buildings(gdf)

    def _standardise_osm_buildings(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        age = self.cfg.metrics.building_age
        max_year = age.reference_year
        btype = gdf["building"].astype("string") if "building" in gdf else pd.Series(pd.NA, index=gdf.index)
        if "building:use" in gdf:  # building=yes + building:use=residential is common
            use = gdf["building:use"].astype("string")
            btype = btype.where(~((btype == "yes") & use.notna()), use)
        gdf["building_type"] = btype
        gdf["levels"] = gdf.get("building:levels", pd.Series(index=gdf.index)).map(parse_number)
        height = gdf.get("height", pd.Series(index=gdf.index)).map(parse_number)
        if "building:height" in gdf:
            height = height.fillna(gdf["building:height"].map(parse_number))
        gdf["height_m"] = height
        year = pd.Series(np.nan, index=gdf.index)
        for tag in age.osm_tags:
            if tag in gdf:
                year = year.fillna(gdf[tag].map(lambda v: parse_year(v, age.min_year, max_year)))
        gdf["year_built"] = year
        gdf["function"] = pd.NA
        gdf["geometry"] = gdf.geometry.make_valid()
        return gdf.reset_index(drop=True)

    def _standardise_user_buildings(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        cats = set(self.cfg.metrics.land_use.categories)
        gdf["building_type"] = gdf["building"].astype("string") if "building" in gdf else pd.NA
        for col in ("levels", "height_m", "year_built"):
            gdf[col] = pd.to_numeric(gdf[col], errors="coerce") if col in gdf else np.nan
        if "function" in gdf:
            func = gdf["function"].astype("string").str.lower()
            bad = func.notna() & ~func.isin(cats)
            if bad.any():
                log.warning("buildings: %d values of `function` are not in %s and are ignored: %s",
                            bad.sum(), sorted(cats), sorted(func[bad].unique())[:10])
            gdf["function"] = func.where(~bad)
        else:
            gdf["function"] = pd.NA
        gdf["geometry"] = gdf.geometry.make_valid()
        return gdf.reset_index(drop=True)

    def _load_transit_routes(self) -> gpd.GeoDataFrame:
        src = self.source("transit_routes")
        if src.source == "file":
            gdf = self._read_file(src, extent=self.area.network_polygon)
            if "route_key" not in gdf:
                raise ValueError("transit_routes file needs a `route_key` column (one value per route)")
            gdf["way_id"] = pd.NA
            return gdf[["route_key", "way_id", "geometry"]]
        gdf = self._cached_osm("transit_routes", self._download_transit_routes, {
            "extent": self._bounds(self._wgs84_extent(self.area.network_polygon)),
            "route_types": self.cfg.metrics.transit.route_types})
        gdf = gdf.to_crs(self.area.crs)
        dedupe = self.cfg.metrics.transit.dedupe_by
        ref = gdf["ref"].astype("string")
        by_id = "rel" + gdf["relation_id"].astype(str)
        gdf["route_key"] = (gdf["route"] + ":" + ref).where(ref.notna() & (dedupe == "ref"), by_id)
        return gdf

    def _download_transit_routes(self) -> gpd.GeoDataFrame:
        types = "|".join(self.cfg.metrics.transit.route_types)
        w, s, e, n = self._wgs84_extent(self.area.network_polygon).bounds
        ql = (f'[out:json][timeout:{self.cfg.overpass.timeout_s}];'
              f'relation["type"="route"]["route"~"^({types})$"]({s},{w},{n},{e});'
              f'out geom({s},{w},{n},{e});')  # member geometry only inside the extent
        data = self.overpass.query(ql)
        rows = []
        for rel in data.get("elements", []):
            tags = rel.get("tags", {})
            for m in rel.get("members", []):
                if m.get("type") != "way" or m.get("role", "") in _STOP_ROLES:
                    continue
                pts = [(p["lon"], p["lat"]) for p in m.get("geometry") or [] if p]
                if len(pts) < 2:
                    continue
                rows.append({"relation_id": rel["id"], "route": tags.get("route"),
                             "ref": tags.get("ref"), "name": tags.get("name"),
                             "way_id": m["ref"], "geometry": LineString(pts)})
        cols = ["relation_id", "route", "ref", "name", "way_id"]
        if not rows:
            return gpd.GeoDataFrame({c: [] for c in cols}, geometry=[], crs=4326)
        return gpd.GeoDataFrame(rows, crs=4326)

    def _read_file(self, src: LayerSource, extent) -> gpd.GeoDataFrame:
        path = Path(src.path)
        if not path.exists():
            raise FileNotFoundError(f"Layer file not found: {path}")
        gdf = gpd.read_file(path, layer=src.layer)
        if gdf.crs is None:
            raise ValueError(f"{path} has no CRS")
        gdf = gdf.to_crs(self.area.crs)
        gdf = gdf[gdf.intersects(extent)]
        log.info("Read %s: %d features", path, len(gdf))
        return gdf.reset_index(drop=True)
