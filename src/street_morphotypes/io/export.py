"""Result export: GeoPackage for GIS, Excel workbook for tables."""
from __future__ import annotations

import json
import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd

from ..clustering import BLOCKS, ClassificationResult, MorphotypeModel
from ..labels import label

log = logging.getLogger(__name__)

LABEL_COLUMNS = ["T_cluster", "T_name", "T_confidence", "T_silhouette",
                 "C_cluster", "C_name", "C_confidence", "C_silhouette",
                 "morphotype", "morphotype_name", "borderline"]


def attach_labels(segments: gpd.GeoDataFrame, table: pd.DataFrame) -> gpd.GeoDataFrame:
    """All study-area segments with labels (unclassified segments keep empty labels)."""
    labels = table.set_index("seg_id")[LABEL_COLUMNS]
    return segments.join(labels, how="left")


def gpkg_safe(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Index as a column; lists, sets and dicts as strings (GPKG cannot store them)."""

    def flat(v):
        if isinstance(v, (list, set, tuple)):
            return ";".join(map(str, v))
        if isinstance(v, dict):
            return json.dumps(v, ensure_ascii=False, default=str)
        return v

    gdf = gdf.reset_index()
    for col in gdf.columns:
        if gdf[col].dtype == object and gdf[col].map(lambda v: isinstance(v, (list, set, tuple, dict))).any():
            gdf[col] = gdf[col].map(flat)
    return gdf


def write_gpkg(path: Path, segments: gpd.GeoDataFrame, area: gpd.GeoDataFrame | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    gpkg_safe(segments).to_file(path, layer="segments", driver="GPKG")
    if area is not None:
        area.to_file(path, layer="study_area", driver="GPKG")
    log.info("Saved %s", path)


def block_profiles(df: pd.DataFrame, table: pd.DataFrame, model: MorphotypeModel, block: str) -> pd.DataFrame:
    """Median of every block feature per cluster, with cluster names and sizes."""
    prefix = "T" if block == "transport" else "C"
    feats = model.block(block).features
    data = df[feats].astype(float).assign(cluster=table[f"{prefix}_cluster"].to_numpy())
    data = data[data["cluster"] >= 0]
    prof = data.groupby("cluster")[feats].median().round(3)
    prof.columns = [f"{label(f)} [{f}]" for f in feats]
    prof.insert(0, "segments", data.groupby("cluster").size())
    prof.insert(0, "name", [model.names[block][c] for c in prof.index])
    return prof


def write_excel(path: Path, df: pd.DataFrame, result: ClassificationResult, model: MorphotypeModel,
                quality: dict, config_yaml: str, correlations: pd.DataFrame | None = None) -> None:
    """Workbook: segments, profiles, morphotype matrix, borderline, diagnostics, config."""
    path.parent.mkdir(parents=True, exist_ok=True)
    table = result.table
    feats = [f for b in BLOCKS for f in model.block(b).features]
    id_cols = [c for c in ("city", "seg_id", "name", "highway", "length") if c in df.columns]
    segments = pd.concat([df[id_cols], df[feats].round(4), table[LABEL_COLUMNS]], axis=1)

    matrix = pd.crosstab(table["T_name"], table["C_name"], margins=True, margins_name="total")
    morph = (table.groupby(["morphotype", "morphotype_name"]).size().rename("segments").reset_index()
             .sort_values("morphotype"))
    if "city" in df.columns and df["city"].nunique() > 1:
        by_city = pd.crosstab(table["morphotype"], df["city"], normalize="columns").round(3)
        morph = morph.merge(by_city, left_on="morphotype", right_index=True)

    with pd.ExcelWriter(path, engine="openpyxl") as xl:
        segments.to_excel(xl, sheet_name="segments", index=False)
        morph.to_excel(xl, sheet_name="morphotypes", index=False)
        matrix.to_excel(xl, sheet_name="morphotype_matrix")
        for block in BLOCKS:
            block_profiles(df, table, model, block).to_excel(xl, sheet_name=f"{block}_profiles")
        segments[table["borderline"]].sort_values(["T_silhouette", "C_silhouette"]) \
            .to_excel(xl, sheet_name="borderline", index=False)
        for block, scan in result.scans.items():
            scan.assign(sizes=scan["sizes"].astype(str)).to_excel(xl, sheet_name=f"k_scan_{block}", index=False)
        if correlations is not None and not correlations.empty:
            correlations.to_excel(xl, sheet_name="correlations", index=False)
        _flatten(quality).to_excel(xl, sheet_name="data_quality", index=False)
        pd.DataFrame({"config": config_yaml.splitlines()}).to_excel(xl, sheet_name="config", index=False)
    log.info("Saved %s", path)


def _flatten(quality: dict) -> pd.DataFrame:
    rows = []
    for scope, q in quality.items():
        for key, val in q.items():
            if isinstance(val, dict):
                for sub, v in val.items():
                    rows.append((scope, f"{key}.{sub}", v))
            else:
                rows.append((scope, key, val))
    return pd.DataFrame(rows, columns=["scope", "indicator", "value"])


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
