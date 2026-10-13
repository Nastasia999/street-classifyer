"""Agreement between two labellings of the same city's segments.

Typical use: how much does a city's typology change when it is labelled by
its own model (local), by another city's model (apply) or by a shared model
(pooled)?

    python scripts/compare_runs.py outputs/wroclaw/morphotypes.gpkg \
        outputs/wroclaw/applied_irkutsk/morphotypes.gpkg --names local applied_irkutsk

Reports the Adjusted Rand Index (ARI; 1 = identical partitions, ~0 = chance)
and the normalised mutual information (NMI) for the transport classes, the
context classes and the morphotypes, plus the transport and context
contingency tables (row-normalised: where do the segments of each class of
run A end up in run B).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score


def load(path: Path) -> pd.DataFrame:
    gdf = gpd.read_file(path, layer="segments", ignore_geometry=True)
    return gdf[gdf["morphotype"].notna()].set_index("seg_id")


def compare(a: pd.DataFrame, b: pd.DataFrame, names: tuple[str, str]) -> dict:
    common = a.index.intersection(b.index)
    a, b = a.loc[common], b.loc[common]
    out = {"segments": int(len(common))}
    null = (a["C_cluster"] < 0) | (b["C_cluster"] < 0)  # C_null is not a class
    for col in ("T_cluster", "C_cluster", "morphotype"):
        mask = ~null if col != "T_cluster" else pd.Series(True, index=a.index)
        out[col] = {
            "ARI": round(float(adjusted_rand_score(a.loc[mask, col], b.loc[mask, col])), 3),
            "NMI": round(float(normalized_mutual_info_score(a.loc[mask, col], b.loc[mask, col])), 3),
        }
    for prefix in ("T", "C"):
        table = pd.crosstab(a[f"{prefix}_name"], b[f"{prefix}_name"], normalize="index").round(2)
        table.index.name, table.columns.name = names
        out[f"{prefix}_crosstab"] = table
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("a", type=Path)
    ap.add_argument("b", type=Path)
    ap.add_argument("--names", nargs=2, default=["A", "B"])
    ap.add_argument("--json", type=Path, help="also write the scores to this file")
    args = ap.parse_args()
    res = compare(load(args.a), load(args.b), tuple(args.names))
    scores = {k: v for k, v in res.items() if not k.endswith("crosstab")}
    print(json.dumps(scores, indent=2))
    pd.set_option("display.width", 250)
    for prefix in ("T", "C"):
        print(f"\n{prefix} classes, share of row ({args.names[0]}) going to each column ({args.names[1]}):")
        print(res[f"{prefix}_crosstab"].to_string())
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({"runs": args.names, **scores}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
