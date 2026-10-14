"""Bootstrap noise of the silhouette scan: how firmly the data choose k.

Every k in ``k_range`` is fitted on random subsamples of the segments. For each
k the report gives the mean silhouette and its spread, the paired difference
from the best k (same subsample, so the noise shared by all k cancels), how
often the smallest cluster passes ``min_cluster_frac``, how often k wins, and
the stability of its partition (ARI of each refit against the fit on all
segments). A k whose difference from the best is within its own spread is not
distinguishable from it by the silhouette.

    python scripts/k_selection.py configs/irkutsk.yaml --runs 30 --frac 0.8
"""
from __future__ import annotations

import argparse
import json
import logging
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score

from street_morphotypes.clustering import BLOCKS, MorphotypeClassifier
from street_morphotypes.clustering.preprocess import FeatureScaler
from street_morphotypes.config import load_city_config
from street_morphotypes.features import CityFeatures
from street_morphotypes.pipeline import classification_frame


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("config", type=Path)
    ap.add_argument("--runs", type=int, default=30)
    ap.add_argument("--frac", type=float, default=0.8)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    logging.basicConfig(level=logging.ERROR)

    cfg = load_city_config(args.config)
    ccfg = cfg.clustering
    feats = CityFeatures.load(cfg.output_dir)
    df = classification_frame(feats)
    features = MorphotypeClassifier(ccfg, cfg.names).resolve_features(df, feats.extra_blocks)
    rows = {"transport": np.ones(len(df), bool), "context": MorphotypeClassifier.context_mask(df)}
    ks = list(range(ccfg.k_range[0], ccfg.k_range[1] + 1))

    def kmeans(k: int) -> KMeans:
        return KMeans(n_clusters=k, n_init=ccfg.kmeans_n_init, random_state=ccfg.random_state)

    report = {"city": cfg.area.name, "runs": args.runs, "subsample": args.frac}
    for block in BLOCKS:
        data = df[rows[block]].reset_index(drop=True)
        f = features[block]
        Z_all = FeatureScaler.from_config(ccfg).fit_transform(data, f)
        ref = {k: kmeans(k).fit_predict(Z_all) for k in ks}
        rng = np.random.default_rng(args.seed)
        sil, ok, ari = ({k: [] for k in ks} for _ in range(3))
        wins = Counter()
        for i in range(args.runs):
            sample = data.sample(frac=args.frac, random_state=int(rng.integers(1 << 31))).reset_index(drop=True)
            scaler = FeatureScaler.from_config(ccfg).fit(sample, f)
            Z, Z_full = scaler.transform(sample), scaler.transform(data)
            for k in ks:
                km = kmeans(k).fit(Z)
                sil[k].append(silhouette_score(Z, km.labels_, sample_size=min(len(Z), ccfg.silhouette_sample_size),
                                               random_state=ccfg.random_state))
                ok[k].append(min(Counter(km.labels_).values()) >= ccfg.min_cluster_frac * len(Z))
                ari[k].append(adjusted_rand_score(ref[k], km.predict(Z_full)))
            allowed = [k for k in ks if ok[k][-1]] or ks  # the same rule as `k: auto`
            wins[max(allowed, key=lambda k: sil[k][-1])] += 1
            print(f"{block} run {i + 1}/{args.runs}", flush=True)

        valid = [k for k in ks if np.mean(ok[k]) >= 0.5] or ks
        best = max(valid, key=lambda k: np.mean(sil[k]))
        table = []
        for k in ks:
            diff = np.array(sil[k]) - np.array(sil[best])
            table.append({
                "k": k,
                "silhouette_mean": round(float(np.mean(sil[k])), 3),
                "silhouette_sd": round(float(np.std(sil[k], ddof=1)), 3),
                "diff_from_best_mean": round(float(diff.mean()), 3),
                "diff_from_best_sd": round(float(diff.std(ddof=1)), 3),
                "min_cluster_ok_share": round(float(np.mean(ok[k])), 2),
                "wins": wins[k],
                "ARI_mean": round(float(np.mean(ari[k])), 3),
                "ARI_min": round(float(np.min(ari[k])), 3),
            })
        report[block] = {"features": f, "best_mean_silhouette_k": best, "by_k": table}
        print(f"\n== {block}: best mean silhouette at k = {best}\n{pd.DataFrame(table).to_string(index=False)}\n")

    out = Path("docs/k_selection") / f"{cfg.area.name}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
