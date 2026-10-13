"""Bootstrap stability of the clusters of one run.

The model is refitted on random subsamples of the segments (k fixed at the
values of the reference run) and every refit labels all segments. Agreement
with the reference labelling is measured per block with the Adjusted Rand
Index, and per cluster with the Jaccard coefficient of its best-matching
cluster (Hennig 2007): a cluster with mean Jaccard below ~0.6 is not a stable
pattern of the data, above ~0.75 it is.

    python scripts/stability.py configs/wroclaw.yaml --runs 30 --frac 0.8
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

from street_morphotypes.clustering import BLOCKS, MorphotypeClassifier
from street_morphotypes.config import load_city_config
from street_morphotypes.features import CityFeatures
from street_morphotypes.pipeline import classification_frame


def best_jaccard(ref: np.ndarray, other: np.ndarray) -> dict[int, float]:
    out = {}
    for c in np.unique(ref):
        a = ref == c
        out[int(c)] = max(((a & (other == d)).sum() / (a | (other == d)).sum()) for d in np.unique(other))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("config", type=Path)
    ap.add_argument("--runs", type=int, default=30)
    ap.add_argument("--frac", type=float, default=0.8)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    logging.basicConfig(level=logging.ERROR)

    cfg = load_city_config(args.config)
    feats = CityFeatures.load(cfg.output_dir)
    df = classification_frame(feats)
    summary = json.loads((cfg.output_dir / "summary.json").read_text(encoding="utf-8"))
    ccfg = cfg.clustering.model_copy(deep=True)
    for block in BLOCKS:  # stability of the partition, not of the choice of k
        ccfg.block(block).k = summary["k"][block]
    clf = MorphotypeClassifier(ccfg, cfg.names)
    _, ref = clf.fit(df, feats.extra_blocks, [cfg.area.name])

    rng = np.random.default_rng(args.seed)
    ari = {b: [] for b in BLOCKS}
    jac = {b: [] for b in BLOCKS}
    for i in range(args.runs):
        sample = df.sample(frac=args.frac, random_state=int(rng.integers(1 << 31))).reset_index(drop=True)
        model, _ = clf.fit(sample, feats.extra_blocks, ["bootstrap"])
        res = clf.apply(model, df)
        for block, col in (("transport", "T_cluster"), ("context", "C_cluster")):
            a, b = ref.table[col].to_numpy(), res.table[col].to_numpy()
            ok = (a >= 0) & (b >= 0)
            ari[block].append(adjusted_rand_score(a[ok], b[ok]))
            jac[block].append(best_jaccard(a[ok], b[ok]))
        print(f"run {i + 1}/{args.runs}: ARI T={ari['transport'][-1]:.3f} C={ari['context'][-1]:.3f}", flush=True)

    report = {"city": cfg.area.name, "runs": args.runs, "subsample": args.frac, "k": summary["k"]}
    for block in BLOCKS:
        names = summary["cluster_names"][block]
        per_cluster = pd.DataFrame(jac[block]).mean().round(3)
        report[block] = {
            "ARI_mean": round(float(np.mean(ari[block])), 3),
            "ARI_min": round(float(np.min(ari[block])), 3),
            "jaccard_by_cluster": {names[str(c)]: float(v) for c, v in per_cluster.items()},
        }
    run_tag = "_".join(cfg.output_dir.parts[1:])  # outputs/experiments/context_k4/irkutsk -> experiments_context_k4_irkutsk
    out = Path("docs/stability") / f"{run_tag}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
