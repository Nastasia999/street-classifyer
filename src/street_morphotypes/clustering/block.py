"""Clustering of one feature block (transport or context): KMeans + Gaussian confidence."""
from __future__ import annotations

import collections
import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples, silhouette_score

from ..config import BlockConfig, ClusteringConfig
from .confidence import GaussianConfidence
from .preprocess import FeatureScaler

log = logging.getLogger(__name__)


@dataclass
class BlockResult:
    """Labels of one block for a set of segments (row order of the input frame)."""

    labels: np.ndarray        # ordered cluster ids 0..k-1
    confidence: np.ndarray    # Gaussian posterior of the assigned cluster
    silhouette: np.ndarray    # per-segment silhouette
    Z: np.ndarray             # scaled feature matrix

    @property
    def sil_mean(self) -> float:
        return float(np.nanmean(self.silhouette)) if len(self.silhouette) else float("nan")


@dataclass
class BlockModel:
    """Everything needed to label new segments with the same clusters."""

    block: str
    scaler: FeatureScaler
    kmeans: KMeans
    gmm: GaussianConfidence          # components = raw KMeans clusters
    remap: dict[int, int]            # raw KMeans label -> ordered label
    order_by: str
    centroids: pd.DataFrame          # ordered label x feature, scaled units
    profiles: pd.DataFrame           # ordered label x feature, raw medians
    sizes: dict[int, int]

    @property
    def features(self) -> list[str]:
        return self.scaler.features

    @property
    def k(self) -> int:
        return len(self.remap)

    def predict(self, df: pd.DataFrame) -> BlockResult:
        Z = self.scaler.transform(df)
        raw = self.kmeans.predict(Z)
        proba = self.gmm.predict_proba(Z)
        confidence = proba[np.arange(len(raw)), raw]
        labels = np.array([self.remap[x] for x in raw], dtype=int)
        sil = (silhouette_samples(Z, labels) if 1 < len(set(labels)) < len(labels)
               else np.full(len(labels), np.nan))
        return BlockResult(labels, confidence, sil, Z)


class BlockClusterer:
    """Fits a :class:`BlockModel`; chooses k by silhouette when ``k: auto``."""

    def __init__(self, cfg: ClusteringConfig) -> None:
        self.cfg = cfg

    def scan(self, df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
        """Silhouette and cluster sizes for every k in ``k_range``."""
        Z = FeatureScaler.from_config(self.cfg).fit_transform(df, features)
        n = len(Z)
        rows = []
        k_min, k_max = self.cfg.k_range
        for k in range(k_min, min(k_max, n - 1) + 1):
            labels = self._kmeans(k).fit_predict(Z)
            sizes = sorted(collections.Counter(labels).values(), reverse=True)
            sil = silhouette_score(Z, labels, sample_size=min(n, self.cfg.silhouette_sample_size),
                                   random_state=self.cfg.random_state)
            rows.append({"k": k, "silhouette": round(float(sil), 4), "sizes": sizes,
                         "min_cluster_ok": min(sizes) >= self.cfg.min_cluster_frac * n})
        return pd.DataFrame(rows)

    def choose_k(self, scan: pd.DataFrame, block: str) -> int:
        ok = scan[scan["min_cluster_ok"]]
        if ok.empty:
            log.warning("%s: every k produces a cluster below min_cluster_frac; using the best silhouette",
                        block)
            ok = scan
        k = int(ok.loc[ok["silhouette"].idxmax(), "k"])
        log.info("%s: k = %d (silhouette %.3f)", block, k, ok["silhouette"].max())
        return k

    def fit(self, df: pd.DataFrame, features: list[str], bcfg: BlockConfig,
            block: str) -> tuple[BlockModel, BlockResult, pd.DataFrame | None]:
        scan = None
        if bcfg.k == "auto":
            scan = self.scan(df, features)
            k = self.choose_k(scan, block)
        else:
            k = bcfg.k
        scaler = FeatureScaler.from_config(self.cfg).fit(df, features)
        Z = scaler.transform(df)
        km = self._kmeans(k).fit(Z)
        gmm = GaussianConfidence(self.cfg.gmm_covariance_type).fit(Z, km.labels_)

        order_by = bcfg.order_by
        if order_by not in df.columns:
            log.warning("%s: order_by '%s' is not available, ordering by '%s'",
                        block, order_by, scaler.features[0])
            order_by = scaler.features[0]
        means = pd.Series(df[order_by].to_numpy(dtype=float)).groupby(km.labels_).mean()
        remap = {int(old): new for new, old in enumerate(means.sort_values().index)}
        labels = np.array([remap[x] for x in km.labels_], dtype=int)

        inv = {new: old for old, new in remap.items()}
        centroids = pd.DataFrame(km.cluster_centers_[[inv[i] for i in range(k)]],
                                 columns=scaler.features)
        profiles = df[scaler.features].astype(float).groupby(labels).median()
        sizes = {int(c): int(n) for c, n in zip(*np.unique(labels, return_counts=True))}
        model = BlockModel(block, scaler, km, gmm, remap, order_by, centroids, profiles, sizes)

        proba = gmm.predict_proba(Z)
        confidence = proba[np.arange(len(Z)), km.labels_]
        sil = silhouette_samples(Z, labels)
        result = BlockResult(labels, confidence, sil, Z)
        log.info("%s: k=%d, mean silhouette %.3f, sizes %s", block, k, result.sil_mean, sizes)
        return model, result, scan

    def _kmeans(self, k: int) -> KMeans:
        return KMeans(n_clusters=k, n_init=self.cfg.kmeans_n_init, random_state=self.cfg.random_state)
