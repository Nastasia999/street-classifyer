"""Study area: the polygon whose segments are classified, plus its buffers."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import cached_property

import geopandas as gpd
from pyproj import CRS
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry

from .config import AreaConfig

log = logging.getLogger(__name__)


@dataclass
class StudyArea:
    """Analysis polygon in a projected CRS and the derived download extents."""

    name: str
    polygon: BaseGeometry          # projected, metres
    crs: CRS
    network_buffer_m: float
    context_buffer_m: float

    @classmethod
    def from_config(cls, cfg: AreaConfig) -> "StudyArea":
        gdf = cls._resolve_wgs84(cfg)
        crs = gdf.estimate_utm_crs() if cfg.crs == "auto" else CRS.from_user_input(cfg.crs)
        projected = gdf.to_crs(crs)
        if cfg.mode == "point":
            centre = projected.geometry.iloc[0]
            polygon = centre.buffer(cfg.point.radius_m, quad_segs=32)
        else:
            polygon = projected.geometry.union_all()
        if polygon.is_empty or polygon.area == 0:
            raise ValueError(f"Study area '{cfg.name}' resolved to an empty polygon")
        log.info("Study area '%s': %.1f km2, CRS %s", cfg.name, polygon.area / 1e6, crs.to_string())
        return cls(cfg.name, polygon, crs, cfg.network_buffer_m, cfg.context_buffer_m)

    @staticmethod
    def _resolve_wgs84(cfg: AreaConfig) -> gpd.GeoDataFrame:
        if cfg.mode == "place":
            import osmnx as ox
            gdf = ox.geocode_to_gdf(cfg.place)
            return gdf[["geometry"]].to_crs(4326)
        if cfg.mode == "point":
            return gpd.GeoDataFrame(geometry=[Point(cfg.point.lon, cfg.point.lat)], crs=4326)
        gdf = gpd.read_file(cfg.polygon.path, layer=cfg.polygon.layer)
        if gdf.crs is None:
            raise ValueError(f"{cfg.polygon.path} has no CRS")
        gdf = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]
        if gdf.empty:
            raise ValueError(f"{cfg.polygon.path} contains no polygons")
        return gdf[["geometry"]].to_crs(4326)

    # ── Extents ──────────────────────────────────────────────────────────────

    @cached_property
    def network_polygon(self) -> BaseGeometry:
        """Area + network buffer: the space syntax graph is built on it."""
        return self.polygon.buffer(self.network_buffer_m)

    @cached_property
    def context_polygon(self) -> BaseGeometry:
        """Area + context margin: buildings, POI, green are downloaded for it."""
        return self.polygon.buffer(self.context_buffer_m)

    def to_wgs84(self, geom: BaseGeometry) -> BaseGeometry:
        return gpd.GeoSeries([geom], crs=self.crs).to_crs(4326).iloc[0]

    def as_gdf(self) -> gpd.GeoDataFrame:
        return gpd.GeoDataFrame(
            {"name": [self.name, f"{self.name}_network_extent"]},
            geometry=[self.polygon, self.network_polygon],
            crs=self.crs,
        )
