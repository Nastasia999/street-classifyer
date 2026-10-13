"""Compare this package's angular segment analysis with a depthmapX segment map export.

depthmapX (tulip) exports a MapInfo file with one straight line per segment and
the columns ``T<bins>_Node_Count``, ``T<bins>_Total_Depth``, ``T<bins>_Choice``.
The same lines are analysed here at radius n and the measures are compared.

    python scripts/validate_depthmapx.py path/to/Segment_Map.mif --out docs/validation
"""
from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

from street_morphotypes.config import SpaceSyntaxConfig, load_defaults
from street_morphotypes.network.segments import SegmentNetwork, SegmentNetworkBuilder
from street_morphotypes.network.space_syntax import AngularSegmentAnalysis, DualGraph

log = logging.getLogger("validate")


def load_segments(path: Path, snap: float) -> tuple[SegmentNetwork, pd.DataFrame]:
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs(3857, allow_override=True)  # NonEarth metres: any metric CRS will do
    prefix = next(re.match(r"(T\d+)_Choice", c).group(1) for c in gdf.columns if re.match(r"T\d+_Choice", c))
    ref = pd.DataFrame({
        "nc": gdf[f"{prefix}_Node_Count"], "td": gdf[f"{prefix}_Total_Depth"], "ch": gdf[f"{prefix}_Choice"],
    })
    ends = np.array([[g.coords[0], g.coords[-1]] for g in gdf.geometry]).reshape(-1, 2)
    labels, xy = SegmentNetworkBuilder._snap(ends, snap)
    n = len(gdf)
    segs = gpd.GeoDataFrame({"u": labels[0::2], "v": labels[1::2]}, geometry=gdf.geometry.values, crs=gdf.crs)
    segs.index.name = "seg_id"
    segs["length"] = segs.geometry.length
    nodes = gpd.GeoDataFrame(geometry=gpd.points_from_xy(xy[:, 0], xy[:, 1]), crs=gdf.crs)
    log.info("%d segments, %d junctions (%s)", n, len(xy), prefix)
    return SegmentNetwork(segs, nodes), ref


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mif", type=Path)
    ap.add_argument("--out", type=Path, default=Path("docs/validation"))
    ap.add_argument("--snap", type=float, default=0.01, help="endpoint snapping tolerance, map units")
    ap.add_argument("--tulip-bins", type=int, default=0,
                    help="replicate depthmapX tulip quantisation of angles (e.g. 64); 0 = exact angles")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s: %(message)s", datefmt="%H:%M:%S")

    net, ref = load_segments(args.mif, args.snap)
    ss_defaults = load_defaults()["space_syntax"]
    cfg = SpaceSyntaxConfig.model_validate({**ss_defaults, "radii": ["n"]})
    # depthmapX measures the turn between the straight segments themselves
    graph = DualGraph.from_network(net, direction_sample_m=1e9)
    if args.tulip_bins:  # 0..180 deg is split into bins/2 steps, each turn rounded to the nearest step
        step = 180.0 / (args.tulip_bins / 2)
        graph.angle_deg = np.round(graph.angle_deg / step) * step
    ours = AngularSegmentAnalysis(graph, cfg).run(np.ones(graph.n, bool), np.zeros(graph.n))

    res = pd.DataFrame({"nc_dmx": ref["nc"].to_numpy(), "td_dmx": ref["td"].to_numpy(),
                        "ch_dmx": ref["ch"].to_numpy(), "nc": ours["ss_nc_n"].to_numpy(),
                        "td": ours["ss_td_n"].to_numpy(), "ch": ours["ss_choice_n"].to_numpy()})
    for side in ("", "_dmx"):
        res[f"nain{side}"] = res[f"nc{side}"] ** 1.2 / (res[f"td{side}"] + 2)
        res[f"nach{side}"] = np.log(res[f"ch{side}"] + 1) / np.log(res[f"td{side}"] + 3)

    main_comp = res["nc"] == res["nc"].max()
    summary = {"segments": int(len(res)), "segments_in_main_component": int(main_comp.sum())}
    for m in ("nc", "td", "ch", "nain", "nach"):
        a, b = res.loc[main_comp, m], res.loc[main_comp, f"{m}_dmx"]
        ok = a.notna() & b.notna()
        summary[m] = {
            "pearson_r": round(float(pearsonr(a[ok], b[ok])[0]), 4),
            "spearman_r": round(float(spearmanr(a[ok], b[ok])[0]), 4),
            "median_ratio_ours_to_depthmapx": round(float(np.median(a[ok] / b[ok].replace(0, np.nan))), 4),
        }
    args.out.mkdir(parents=True, exist_ok=True)
    summary["tulip_bins"] = args.tulip_bins
    tag = f"_tulip{args.tulip_bins}" if args.tulip_bins else "_exact"
    (args.out / f"depthmapx_comparison{tag}.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    res.to_csv(args.out / f"depthmapx_comparison{tag}.csv", index=False)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
