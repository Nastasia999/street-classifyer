"""User-supplied segment attributes (``extra_features`` in the config)."""
from __future__ import annotations

import logging
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from ..config import ExtraFeatureConfig
from ..tags import as_list
from .base import MetricContext, corridor_overlaps, pair_index

log = logging.getLogger(__name__)


class ExtraFeatureJoiner:
    """Transfers columns of a user layer onto the study-area segments.

    - ``join: id``      the layer has ``id_column`` matching ``layers.network.id_column``
                        of a user-supplied network (a segment merged from several user
                        segments gets the mean of their numeric values, the first otherwise);
    - ``join: spatial`` lines: the feature running alongside the segment for the
                        longest stretch within ``max_distance_m``; points: the
                        nearest feature within ``max_distance_m``; polygons: the
                        polygon containing the segment midpoint.
    """

    def __init__(self, ctx: MetricContext) -> None:
        self.ctx = ctx

    def join_all(self) -> tuple[pd.DataFrame, dict[str, str]]:
        """Returns the joined columns and a ``column -> block`` mapping."""
        segs = self.ctx.segments
        out = pd.DataFrame(index=segs.index)
        blocks: dict[str, str] = {}
        for spec in self.ctx.cfg.extra_features:
            cols = self._join(spec)
            for col, block in spec.columns.items():
                if col in out:
                    raise ValueError(f"extra_features: column '{col}' is provided twice")
                out[col] = cols[col]
                blocks[col] = block
            log.info("extra_features: %s -> %s (%d of %d segments matched)", spec.path,
                     list(spec.columns), int(cols.notna().any(axis=1).sum()), len(segs))
        return out, blocks

    def _join(self, spec: ExtraFeatureConfig) -> pd.DataFrame:
        if not Path(spec.path).exists():
            raise FileNotFoundError(f"extra_features: {spec.path} not found")
        layer = gpd.read_file(spec.path, layer=spec.layer)
        missing = [c for c in spec.columns if c not in layer.columns]
        if missing:
            raise ValueError(f"extra_features: {spec.path} has no columns {missing}")
        segs = self.ctx.segments
        if spec.join == "id":
            return self._join_by_id(spec, layer, segs)
        if layer.crs is None:
            raise ValueError(f"extra_features: {spec.path} has no CRS")
        layer = layer.to_crs(segs.crs).reset_index(drop=True)
        gtype = layer.geom_type.iloc[0] if len(layer) else "Point"
        if "Line" in gtype:
            src = self._match_lines(layer, segs, spec.max_distance_m)
        elif "Polygon" in gtype:
            src = self._match_polygons(layer, segs)
        else:
            src = self._match_points(layer, segs, spec.max_distance_m)
        return pd.DataFrame({c: _take(layer[c], src) for c in spec.columns}, index=segs.index)

    def _join_by_id(self, spec: ExtraFeatureConfig, layer, segs) -> pd.DataFrame:
        if self.ctx.cfg.layers.network.source != "file" or not self.ctx.cfg.layers.network.id_column:
            raise ValueError("extra_features join: id requires a network from a file with "
                             "`layers.network.id_column` set")
        table = pd.DataFrame(layer.drop(columns="geometry", errors="ignore")).set_index(spec.id_column)
        if not table.index.is_unique:
            raise ValueError(f"extra_features: {spec.id_column} in {spec.path} is not unique")
        # a segment merged from several user segments carries all their ids
        ids = segs["user_id"].map(as_list).explode().dropna()
        out = pd.DataFrame(index=segs.index)
        for c in spec.columns:
            values = ids.map(table[c])
            numeric = pd.api.types.is_numeric_dtype(table[c])
            agg = values.astype(float).groupby(level=0).mean() if numeric else values.groupby(level=0).first()
            out[c] = agg.reindex(segs.index)
        return out

    @staticmethod
    def _match_lines(layer, segs, tol) -> pd.Series:
        pairs = corridor_overlaps(segs, layer, tol)
        best = pairs.sort_values("length", ascending=False).drop_duplicates("seg_id").set_index("seg_id")["j"]
        return best.reindex(segs.index)

    @staticmethod
    def _match_points(layer, segs, tol) -> pd.Series:
        joined = gpd.sjoin_nearest(segs[["geometry"]], layer[["geometry"]], max_distance=tol,
                                   how="left", distance_col="_d")
        joined = joined.sort_values("_d").groupby(level=0)["index_right"].first()
        return joined.reindex(segs.index)

    @staticmethod
    def _match_polygons(layer, segs) -> pd.Series:
        mids = gpd.GeoDataFrame(geometry=segs.geometry.interpolate(0.5, normalized=True), crs=segs.crs)
        mi, pj = pair_index(mids, layer, predicate="within")
        return pd.Series(pj, index=segs.index.to_numpy()[mi]).groupby(level=0).first().reindex(segs.index)


def _take(values: pd.Series, positions: pd.Series) -> pd.Series:
    """``values`` at integer ``positions`` (NaN position -> missing value)."""
    ok = positions.notna().to_numpy()
    out = pd.Series(np.nan, index=positions.index, dtype=object)
    out[ok] = values.to_numpy()[positions[ok].astype(int).to_numpy()]
    return out.infer_objects()
