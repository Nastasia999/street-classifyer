import json

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString

from street_morphotypes.io.web import export_web, numeric_classes, pick_city_runs


def test_numeric_classes_zero_class_and_fixed_shares():
    pt = pd.Series([0] * 50 + list(range(1, 51)), name="pt_routes", dtype=float)
    classes = numeric_classes(pt, "int")
    assert classes[0] == {"min": 0.0, "label": "0"}
    assert [c["min"] for c in classes] == sorted(c["min"] for c in classes)

    shares = numeric_classes(pd.Series([0.1, 0.9], name="frontage"), "pct")
    assert [c["label"] for c in shares] == ["0", "< 25%", "25–50%", "50–75%", "≥ 75%"]


def _run(root, name, cities, web=True):
    d = root / name
    d.mkdir(parents=True)
    summary = {"cities": cities, "trained_on": cities, "web": web, "k": {"transport": 1, "context": 1},
               "features": {"transport": ["lanes"], "context": ["frontage"]},
               "mean_silhouette": {"transport": 0.5, "context": 0.5},
               "cluster_names": {"transport": {"0": "T0 · a"}, "context": {"0": "C0 · b"}},
               "area_labels": {c: c.title() for c in cities}}
    (d / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    segs = gpd.GeoDataFrame({
        "seg_id": [1, 2], "classify": [True, True], "in_area": [True, True], "lanes": [2.0, 4.0],
        "frontage": [0.0, 0.6], "T_cluster": [0.0, 0.0], "C_cluster": [0.0, 0.0],
        "morphotype": ["T0-C0", "T0-C0"], "morphotype_name": ["a | b", "a | b"], "borderline": [False, True],
    }, geometry=[LineString([(0, 0), (100, 0)]), LineString([(100, 0), (100, 100)])], crs="EPSG:32633")
    for c in cities:
        segs.to_file(d / ("morphotypes.gpkg" if len(cities) == 1 else f"morphotypes_{c}.gpkg"), layer="segments")


def test_export_web_reflects_current_outputs(tmp_path):
    out, web = tmp_path / "outputs", tmp_path / "web"
    _run(out, "alpha", ["alpha"])
    _run(out, "ab_pooled", ["alpha", "beta"])
    _run(out, "smoke", ["smoke"], web=False)
    runs = pick_city_runs(out)
    assert {c: d.name for c, (d, _) in runs.items()} == {"alpha": "alpha", "beta": "ab_pooled"}

    assert export_web(out, web) == ["alpha", "beta"]
    assert sorted(p.name for p in (web / "data" / "cities").iterdir()) == ["alpha.js", "beta.js"]

    # A later export with other runs drops the cities that are gone.
    for p in out.iterdir():
        for f in p.iterdir():
            f.unlink()
        p.rmdir()
    _run(out, "gamma", ["gamma"])
    assert export_web(out, web) == ["gamma"]
    assert [p.name for p in (web / "data" / "cities").iterdir()] == ["gamma.js"]
    assert '"gamma"' in (web / "data" / "manifest.js").read_text(encoding="utf-8")
