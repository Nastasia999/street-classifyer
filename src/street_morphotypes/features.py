"""Builds the per-segment feature table of one city (network -> space syntax -> metrics)."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio

from .area import StudyArea
from .config import CityConfig
from .data.layers import LayerRepository
from .io.export import gpkg_safe
from .metrics import METRICS, ExtraFeatureJoiner, MetricContext
from .network.segments import SegmentNetwork, SegmentNetworkBuilder
from .network.space_syntax import AngularSegmentAnalysis, DualGraph

log = logging.getLogger(__name__)

FEATURES_FILE = "features.gpkg"
META_FILE = "features_meta.json"


@dataclass
class CityFeatures:
    """Feature table of the study-area segments of one city."""

    city: str
    segments: gpd.GeoDataFrame                 # indexed by seg_id
    extra_blocks: dict[str, str] = field(default_factory=dict)  # extra feature -> block
    quality: dict = field(default_factory=dict)
    area: gpd.GeoDataFrame | None = None       # study area polygon (+ network extent)

    def save(self, out_dir: Path) -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        gpkg_safe(self.segments).to_file(out_dir / FEATURES_FILE, layer="segments", driver="GPKG")
        if self.area is not None:
            self.area.to_file(out_dir / FEATURES_FILE, layer="study_area", driver="GPKG")
        meta = {"city": self.city, "extra_blocks": self.extra_blocks, "quality": self.quality}
        (out_dir / META_FILE).write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
        log.info("Features saved: %s", out_dir / FEATURES_FILE)

    @classmethod
    def load(cls, out_dir: Path) -> "CityFeatures":
        gdf = gpd.read_file(out_dir / FEATURES_FILE, layer="segments").set_index("seg_id")
        meta = json.loads((out_dir / META_FILE).read_text(encoding="utf-8"))
        layers = pyogrio.list_layers(out_dir / FEATURES_FILE)[:, 0]
        area = gpd.read_file(out_dir / FEATURES_FILE, layer="study_area") if "study_area" in layers else None
        return cls(meta["city"], gdf, meta.get("extra_blocks", {}), meta.get("quality", {}), area)

    @staticmethod
    def exists(out_dir: Path) -> bool:
        return (out_dir / FEATURES_FILE).exists() and (out_dir / META_FILE).exists()


class FeatureBuilder:
    """Runs every enabled metric for one city config."""

    def __init__(self, cfg: CityConfig) -> None:
        self.cfg = cfg
        self.area = StudyArea.from_config(cfg.area)
        self.layers = LayerRepository(cfg, self.area)
        self._check_buffers()

    def fetch(self) -> None:
        self.layers.prefetch()

    def build_network(self) -> SegmentNetwork:
        builder = SegmentNetworkBuilder(self.cfg, self.area)
        src = self.cfg.layers.network
        if src.source == "osm":
            return builder.from_osm(self.layers.osm_network_graph())
        return builder.from_lines(self.layers.network_lines(), src.id_column)

    def build(self) -> CityFeatures:
        network = self.build_network()
        segs = network.segments
        table = segs[segs["in_area"]].drop(columns=["lanes_raw", "maxspeed_raw"]).copy()

        ss = self._space_syntax(network)
        table = table.join(ss.loc[table.index])

        ctx = MetricContext(self.cfg, network, self.layers)
        for metric_cls in METRICS:
            metric = metric_cls(ctx)
            if not metric.enabled:
                log.info("Metric %s: disabled in config", metric.name)
                continue
            missing = metric.missing_layers()
            if missing:
                log.warning("Metric %s: skipped, layers %s are set to 'none'", metric.name, missing)
                continue
            log.info("Metric %s ...", metric.name)
            table = table.join(metric.compute())

        extra, blocks = ExtraFeatureJoiner(ctx).join_all()
        table = table.join(extra)
        self._summarise(table, ctx.quality)
        return CityFeatures(self.cfg.area.name, table, blocks, ctx.quality, self.area.as_gdf())

    # ── Steps ────────────────────────────────────────────────────────────────

    def _space_syntax(self, network: SegmentNetwork) -> pd.DataFrame:
        sscfg = self.cfg.space_syntax
        graph = DualGraph.from_network(network, sscfg.direction_sample_m)
        segs = network.segments.loc[graph.seg_ids]
        midpoints = segs.geometry.interpolate(0.5, normalized=True)
        dist = midpoints.distance(self.area.polygon).to_numpy()
        return AngularSegmentAnalysis(graph, sscfg).run(segs["in_area"].to_numpy(), dist)

    def _check_buffers(self) -> None:
        m = self.cfg.metrics
        lanes = max(m.lanes.defaults_by_highway.values(), default=4)
        widest = max(m.frontage.buffer_m, m.poi_density.buffer_m, m.green_area.buffer_m,
                     m.building_age.buffer_m, m.land_use.buffer_m, m.transit.stops_buffer_m)
        reach = widest + lanes * m.carriageway.lane_width_m / 2
        if reach > self.cfg.area.context_buffer_m:
            log.warning("area.context_buffer_m (%g m) is smaller than the widest metric reach (%.0f m): "
                        "metrics of segments near the boundary will be underestimated",
                        self.cfg.area.context_buffer_m, reach)
        radii = [r for r in self.cfg.space_syntax.radii if r != "n"]
        if radii and max(radii) > self.cfg.area.network_buffer_m:
            log.warning("area.network_buffer_m (%g m) is smaller than the largest space syntax radius "
                        "(%g m): edge effects near the boundary", self.cfg.area.network_buffer_m, max(radii))

    @staticmethod
    def _summarise(table: pd.DataFrame, quality: dict) -> None:
        quality["segments_in_area"] = int(len(table))
        quality["segments_classified"] = int(table["classify"].sum())
        quality["twinned_carriageways"] = int((table["twin_id"] >= 0).sum())
        num = table.select_dtypes("number")
        quality["missing_share_by_column"] = {
            c: round(float(v), 3) for c, v in num[table["classify"]].isna().mean().items() if v > 0}
        log.info("Feature table: %d segments, %d columns", len(table), table.shape[1])
        if np.any(list(quality["missing_share_by_column"].values())):
            log.info("Columns with missing values: %s", quality["missing_share_by_column"])
