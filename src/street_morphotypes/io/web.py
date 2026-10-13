"""Data for the web map (``web/``): every run in the output folder, one script per city.

The page reads ``<web_dir>/data/manifest.js`` and nothing else, so the data folder
is rebuilt from scratch on every export: a city that is no longer among the
outputs disappears from the map. Data are written as small scripts rather than
JSON so that ``index.html`` also works when opened straight from disk.

City choice: a local run of the city is preferred; otherwise its labels come
from the first pooled run (by folder name) that contains it. Runs whose
``summary.json`` says ``"web": false`` (experiments, test areas) are skipped.
"""
from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio

from ..labels import label

log = logging.getLogger(__name__)

TRANSPORT_COLUMNS = ["lanes", "maxspeed", "pt_routes", "pt_stops_per_100m"]
CONTEXT_COLUMNS = ["frontage", "poi_per_100m", "green_m2_per_100m", "building_age_median",
                   "fn_residential", "fn_commercial", "fn_social", "fn_industrial"]
SHARE_COLUMNS = {"frontage", "fn_residential", "fn_commercial", "fn_social", "fn_industrial"}
INFO_COLUMNS = ["seg_id", "name", "highway", "length", "lanes_imputed", "maxspeed_imputed",
                "T_cluster", "C_cluster", "morphotype", "T_confidence", "C_confidence", "borderline"]
# Fixed classes where a value has a meaning of its own, so the legend reads the same in every city.
_SHARES = [(0.0, "0"), (1e-9, "< 25%"), (0.25, "25–50%"), (0.5, "50–75%"), (0.75, "≥ 75%")]
FIXED_CLASSES = {
    **{c: _SHARES for c in SHARE_COLUMNS},
    "lanes": [(0.0, "1"), (1.5, "2"), (2.5, "3"), (3.5, "4–5"), (5.5, "6 and more")],
    "maxspeed": [(0.0, "< 30"), (30.0, "30–40"), (45.0, "50"), (55.0, "60–70"), (75.0, "80 and more")],
}
FAMILIES = {"ss_nain": "Integration · NAIN", "ss_nach": "Through-movement · NACH",
            "fn": "Floor-area function"}
NOTES = {
    "ss_nain": "Normalised angular integration: how easy the segment is to reach from everywhere "
               "within the radius (to-movement).",
    "ss_nach": "Normalised angular choice: how often the segment lies on the simplest routes "
               "within the radius (through-movement).",
    "lanes": "Lanes across the street, both carriageways of a divided road.",
    "maxspeed": "Speed limit; missing OSM tags are filled with national defaults by road class.",
    "pt_routes": "Public transport routes running along the segment.",
    "pt_stops_per_100m": "Public transport stops per 100 m of street.",
    "frontage": "Share of the segment length lined by buildings (street wall).",
    "poi_per_100m": "Shops, services and other organisations per 100 m.",
    "green_m2_per_100m": "Green area in the side strips per 100 m of street.",
    "building_age_median": "Median age of the buildings along the street.",
    "fn": "Share of floor area along the street by function.",
}


def area_label(area) -> str:
    """Human-readable city name from an ``AreaConfig``: the first part of a place query."""
    if area.mode == "place" and area.place:
        return area.place.split(",")[0].strip()
    return area.name.replace("_", " ").replace("-", " ").title()


# ── Discovery ────────────────────────────────────────────────────────────────

def _runs(output_root: Path) -> list[tuple[Path, dict]]:
    runs = []
    for d in sorted(p for p in output_root.iterdir() if p.is_dir()):
        path = d / "summary.json"
        if not path.exists():
            continue
        summary = json.loads(path.read_text(encoding="utf-8"))
        if summary.get("web", True):
            runs.append((d, summary))
    return runs


def _gpkg(run_dir: Path, summary: dict, city: str) -> Path:
    single = run_dir / "morphotypes.gpkg"
    return single if len(summary["cities"]) == 1 else run_dir / f"morphotypes_{city}.gpkg"


def pick_city_runs(output_root: Path) -> dict[str, tuple[Path, dict]]:
    """city -> (run folder, summary): the city's local run, else the first pooled run with it."""
    chosen: dict[str, tuple[Path, dict]] = {}
    for run_dir, summary in _runs(output_root):
        for city in summary.get("cities", []):
            if not _gpkg(run_dir, summary, city).exists():
                continue
            local = summary["cities"] == [city]
            if city not in chosen or (local and chosen[city][1]["cities"] != [city]):
                chosen[city] = (run_dir, summary)
    return dict(sorted(chosen.items()))


# ── Layers ───────────────────────────────────────────────────────────────────

def _sig(v: float, digits: int = 3) -> float:
    return float(f"{v:.{digits}g}")


def _fmt(v: float, kind: str) -> str:
    if kind == "pct":
        return f"{v * 100:.0f}%"
    if kind == "int" or abs(v) >= 100:
        return f"{v:,.0f}"
    return f"{v:.2g}" if abs(v) < 1 else f"{v:.3g}"


def numeric_classes(values: pd.Series, kind: str) -> list[dict]:
    """Up to five classes: one per value for few distinct values, else quantiles.

    A column dominated by zeros (no PT routes, no shops) gets a class of its own
    for zero and quantiles of the positive values for the rest.
    """
    v = values.dropna().astype(float)
    if v.empty:
        return []
    if values.name in FIXED_CLASSES:
        return [{"min": lo, "label": text} for lo, text in FIXED_CLASSES[values.name]]
    distinct = np.sort(v.unique())
    if len(distinct) <= 6:
        return [{"min": float(x), "label": _fmt(x, kind)} for x in distinct]
    zero_class = (v == 0).mean() >= 0.15
    if zero_class:
        pos = v[v > 0]
        breaks = {_sig(q) for q in np.quantile(pos, [.25, .5, .75])}
        if kind == "int":
            breaks = {float(np.ceil(b)) for b in breaks}
        lows = sorted({0.0, float(pos.min())} | {b for b in breaks if b > pos.min()})
    else:
        breaks = {_sig(q) for q in np.quantile(v, [.2, .4, .6, .8])}
        if kind == "int":
            breaks = {float(np.ceil(b)) for b in breaks}
        lows = sorted({float(v.min())} | {b for b in breaks if b > v.min()})
    classes = []
    for i, lo in enumerate(lows):
        if zero_class and i == 0:
            text = "0"
        elif i == len(lows) - 1:
            text = f"≥ {_fmt(lo, kind)}"
        elif kind == "int":
            hi = lows[i + 1] - 1
            text = f"{lo:g}" if hi <= lo else f"{lo:g}–{hi:g}"
        elif i == 0 or (zero_class and i == 1):
            text = f"< {_fmt(lows[i + 1], kind)}"
        else:
            text = f"{_fmt(lo, kind)} – {_fmt(lows[i + 1], kind)}"
        classes.append({"min": lo, "label": text})
    return classes


def _capital(text: str) -> str:
    return text[:1].upper() + text[1:]


def _ss_key(col: str) -> tuple:
    radius = col.rsplit("_", 1)[1]
    return (("nain", "nach").index(col.split("_")[1]), radius != "n", float(radius) if radius != "n" else 0.0)


def _radius_text(col: str) -> str:
    r = col.rsplit("_", 1)[1]
    return "Rn" if r == "n" else f"{r} m"


def excluded_reason(values: pd.DataFrame, col: str, model_feats: set[str]) -> str:
    """Why a computed metric is not among the clustering features of its block."""
    v = values[col].dropna()
    if len(v):
        top = v.value_counts(normalize=True)
        if top.iloc[0] >= 0.9:
            return (f"Not used in clustering: {top.iloc[0]:.0%} of the segments have the same value "
                    f"({top.index[0]:g}), so it cannot tell streets apart.")
    if col.startswith("ss_"):
        family = col.rsplit("_", 1)[0]
        used = [c for c in model_feats if c.startswith(family + "_")]
        if used:
            rho = max(values[col].corr(values[c], method="spearman") for c in used)
            radii = " and ".join(_radius_text(c) for c in sorted(used, key=_ss_key))
            return (f"Not used in clustering: the model takes {radii}. This radius lies between them "
                    f"(Spearman ρ up to {rho:.2f}) and is shown for interpretation.")
    return "Not used in clustering: shown for interpretation."


def build_layers(gdf: gpd.GeoDataFrame, summary: dict) -> list[dict]:
    model_feats = {b: set(f) for b, f in summary["features"].items()}
    classified = gdf[gdf["classify"].astype(bool)]
    known = set(TRANSPORT_COLUMNS) | set(CONTEXT_COLUMNS)
    ss = sorted((c for c in gdf.columns if c.startswith(("ss_nain_", "ss_nach_"))), key=_ss_key)
    extra = {b: [c for c in sorted(model_feats.get(b, ())) if c not in known and not c.startswith("ss_")]
             for b in ("transport", "context")}
    columns = ([("transport", c) for c in ss + TRANSPORT_COLUMNS + extra["transport"]]
               + [("context", c) for c in CONTEXT_COLUMNS + extra["context"]])
    layers = []
    for block, col in columns:
        if col not in gdf.columns or not pd.api.types.is_numeric_dtype(gdf[col]) or gdf[col].notna().sum() == 0:
            continue
        family = col.rsplit("_", 1)[0] if col.startswith("ss_") else ("fn" if col.startswith("fn_") else col)
        if col.startswith("ss_"):
            r = col.rsplit("_", 1)[1]
            chip = "Rn" if r == "n" else r
        elif family == "fn":
            chip = col[3:]
        else:
            chip = None
        kind = "pct" if col in SHARE_COLUMNS else (
            "int" if col in ("lanes", "maxspeed", "pt_routes") else "num")
        in_model = col in model_feats.get(block, set())
        layers.append({
            "id": col, "group": block, "kind": "numeric", "format": kind,
            "family": family, "family_label": FAMILIES.get(family, label(col)), "chip": chip,
            "label": label(col), "short": _capital(label(col, short=True)), "note": NOTES.get(family, ""),
            "in_model": in_model,
            "excluded_reason": None if in_model else excluded_reason(classified, col, model_feats.get(block, set())),
            "classes": numeric_classes(classified[col], kind),
        })
    layers += [
        {"id": "morphotype", "group": "morphotypes", "kind": "morphotype", "label": "Morphotypes T × C",
         "note": "Every street segment is a pair of classes: transport (line width) × context (colour)."},
        {"id": "T_cluster", "group": "morphotypes", "kind": "cluster", "block": "transport",
         "label": "Transport clusters", "note": "Classes of the street as a link in the movement network."},
        {"id": "C_cluster", "group": "morphotypes", "kind": "cluster", "block": "context",
         "label": "Context clusters", "note": "Classes of the street as a place: buildings, uses, greenery."},
        {"id": "borderline", "group": "morphotypes", "kind": "borderline", "label": "Borderline segments",
         "note": "Segments whose class is uncertain: low silhouette or low model confidence in either block."},
    ]
    return layers


# ── Data ─────────────────────────────────────────────────────────────────────

def _clean(v):
    if v is None or (isinstance(v, float) and not np.isfinite(v)) or v is pd.NA:
        return None
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    if isinstance(v, (np.integer, int)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        return _sig(float(v), 4)
    return str(v)


def _line_coords(geom) -> list:
    if geom.geom_type == "LineString":
        return [[round(x, 5), round(y, 5)] for x, y in geom.coords]
    return [[[round(x, 5), round(y, 5)] for x, y in part.coords] for part in geom.geoms]


def _boolish(s: pd.Series) -> pd.Series:
    return s.map(lambda v: None if v is None or (isinstance(v, float) and np.isnan(v))
                 else str(v).lower() in ("true", "1"))


def city_geojson(gdf: gpd.GeoDataFrame, layers: list[dict]) -> dict:
    cols = [c for c in INFO_COLUMNS if c in gdf.columns] + [l["id"] for l in layers if l["kind"] == "numeric"]
    props = gdf[list(dict.fromkeys(cols))].copy()
    for c in ("T_cluster", "C_cluster"):
        if c in props:
            props[c] = props[c].astype("Int64").astype(object)
    for c in ("borderline", "lanes_imputed", "maxspeed_imputed"):
        if c in props:
            props[c] = _boolish(props[c])
    geoms = gdf.geometry.to_crs(4326)
    features = []
    for i, (geom, row) in enumerate(zip(geoms, props.itertuples(index=False))):
        if geom is None or geom.is_empty:
            continue
        features.append({
            "type": "Feature", "id": i,
            "geometry": {"type": geom.geom_type, "coordinates": _line_coords(geom)},
            "properties": {k: v for k, v in zip(props.columns, map(_clean, row)) if v is not None},
        })
    return {"type": "FeatureCollection", "features": features}


def _area_geojson(path: Path) -> dict | None:
    if "study_area" not in pyogrio.list_layers(path)[:, 0]:
        return None
    area = gpd.read_file(path, layer="study_area")
    if "name" in area:  # the layer also holds "<city>_network_extent", the space syntax buffer
        area = area[~area["name"].astype(str).str.endswith("_network_extent")]
    area = area.set_geometry(area.geometry.simplify(10)).to_crs(4326)
    return json.loads(area[["geometry"]].to_json(drop_id=True))


def _clusters(gdf: gpd.GeoDataFrame, summary: dict, block: str) -> list[dict]:
    col = "T_cluster" if block == "transport" else "C_cluster"
    counts = gdf[col].dropna().astype(int).value_counts()
    profiles = summary.get("cluster_profiles", {}).get(block, {})
    out = []
    for c, name in sorted(summary["cluster_names"][block].items(), key=lambda kv: int(kv[0])):
        profile = profiles.get(str(c))
        if profile == "average profile":
            profile = "close to the city median on every feature"
        out.append({"id": int(c), "name": name, "count": int(counts.get(int(c), 0)),
                    # the generated profile, shown under a manual name as its evidence
                    "profile": profile if profile and profile not in name else None})
    if block == "context" and counts.get(-1, 0):
        out.append({"id": -1, "name": "C_null · no reliable building data", "count": int(counts[-1])})
    return out


def _morphotypes(gdf: gpd.GeoDataFrame) -> dict:
    data = gdf.dropna(subset=["morphotype"])
    names = data.groupby("morphotype")["morphotype_name"].first()
    counts = data["morphotype"].value_counts()
    return {m: {"count": int(counts[m]), "name": str(names[m])} for m in sorted(counts.index)}


def _xlsx_label(run_dir: Path) -> str | None:
    """City name from the config sheet of an older run (written before ``area_labels``)."""
    import yaml
    from openpyxl import load_workbook
    try:
        wb = load_workbook(run_dir / "morphotypes.xlsx", read_only=True)
        rows = [r[0] for r in wb["config"].iter_rows(min_row=2, values_only=True) if r[0] is not None]
        wb.close()
        area = yaml.safe_load("\n".join(rows)).get("area", {})
    except Exception:  # noqa: BLE001 — a label is a nicety, never a reason to fail
        return None
    if area.get("mode") == "place" and area.get("place"):
        return area["place"].split(",")[0].strip()
    return None


def _order_by(run_dir: Path, summary: dict) -> dict[str, str]:
    """Feature by which each block's clusters are numbered (older runs: read from the saved model)."""
    if "order_by" in summary:
        return summary["order_by"]
    try:
        from ..clustering import MorphotypeModel
        model = MorphotypeModel.load(run_dir / "model.joblib")
        return {b: model.block(b).order_by for b in ("transport", "context")}
    except Exception:  # noqa: BLE001 — the legend then simply omits the ordering
        return {}


def _city_label(city: str, run_dir: Path, summary: dict, output_root: Path) -> str:
    labels = summary.get("area_labels", {})
    if city in labels:
        return labels[city]
    for d in (output_root / city, run_dir):
        if (d / "morphotypes.xlsx").exists() and (found := _xlsx_label(d)):
            return found
    return city.replace("_", " ").title()


# ── Export ───────────────────────────────────────────────────────────────────

def export_web(output_root: Path, web_dir: Path) -> list[str]:
    """Rebuild ``<web_dir>/data`` from the runs in ``output_root``; returns the cities written."""
    output_root, web_dir = Path(output_root), Path(web_dir)
    data_dir = web_dir / "data"
    chosen = pick_city_runs(output_root) if output_root.exists() else {}
    if data_dir.exists():
        shutil.rmtree(data_dir)
    (data_dir / "cities").mkdir(parents=True)

    cities = []
    for city, (run_dir, summary) in chosen.items():
        path = _gpkg(run_dir, summary, city)
        gdf = gpd.read_file(path, layer="segments")
        if "in_area" in gdf:
            gdf = gdf[_boolish(gdf["in_area"]).fillna(True).astype(bool)]
        gdf = gdf.reset_index(drop=True)
        layers = build_layers(gdf, summary)
        geojson = city_geojson(gdf, layers)
        bounds = gdf.geometry.to_crs(4326).total_bounds
        file = f"data/cities/{city}.js"
        payload = {"segments": geojson, "area": _area_geojson(path)}
        (web_dir / file).write_text(
            f"window.SM_DATA = window.SM_DATA || {{}};\nwindow.SM_DATA[{json.dumps(city)}] = "
            + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
        quality = summary.get("data_quality", {}).get(city, {})
        cities.append({
            "id": city,
            "label": _city_label(city, run_dir, summary, output_root),
            "run": run_dir.name,
            "mode": "local" if summary["cities"] == [city] else "pooled",
            "trained_on": summary.get("trained_on", []),
            "file": file,
            "version": int(path.stat().st_mtime),
            "bounds": [round(float(b), 5) for b in bounds],
            "stats": {
                "segments": int(len(gdf)),
                "classified": int(gdf["T_cluster"].notna().sum()),
                "borderline": int(_boolish(gdf["borderline"]).fillna(False).sum()),
                "k": summary.get("k", {}),
                "mean_silhouette": summary.get("mean_silhouette", {}),
                "lanes_imputed_share": quality.get("lanes_imputed_share"),
                "maxspeed_imputed_share": quality.get("maxspeed_imputed_share"),
                "unknown_function_share": quality.get("building_function_gfa_share", {}).get("unknown"),
            },
            "clusters": {b: _clusters(gdf, summary, b) for b in ("transport", "context")},
            "order_by": {b: {"id": f, "label": label(f, short=True)} for b, f in _order_by(run_dir, summary).items()},
            "morphotypes": _morphotypes(gdf),
            "layers": layers,
        })
        log.info("Web map: %s from %s (%d segments)", city, run_dir.name, len(gdf))

    manifest = {"generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "output_root": output_root.as_posix(), "cities": cities}
    (data_dir / "manifest.js").write_text(
        "window.SM_MANIFEST = " + json.dumps(manifest, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")
    if not cities:
        log.warning("Web map: no runs with web output in %s; the page will show an empty state", output_root)
    log.info("Web map data written to %s (%d cities)", data_dir, len(cities))
    return [c["id"] for c in cities]
