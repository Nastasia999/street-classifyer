"""Two parallel block clusterings combined into morphotypes (T x C)."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .. import __version__
from ..config import ClusteringConfig, NamesConfig
from .block import BlockClusterer, BlockModel, BlockResult
from .naming import NULL_CONTEXT, ClusterNamer

log = logging.getLogger(__name__)

BLOCKS = ("transport", "context")


@dataclass
class MorphotypeModel:
    """A trained typology that can be applied to any city with the same features."""

    transport: BlockModel
    context: BlockModel
    names: dict[str, dict[int, str]]          # block -> cluster id -> name
    morphotype_names: dict[str, str]          # manual "t-c" -> name
    trained_on: list[str]
    clustering: dict                          # clustering config snapshot
    version: str = __version__

    def block(self, name: str) -> BlockModel:
        return getattr(self, name)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        log.info("Model saved: %s", path)

    @staticmethod
    def load(path: Path) -> "MorphotypeModel":
        model = joblib.load(path)
        if not isinstance(model, MorphotypeModel):
            raise TypeError(f"{path} is not a street-morphotypes model")
        return model


@dataclass
class ClassificationResult:
    table: pd.DataFrame                                   # one row per input segment
    blocks: dict[str, BlockResult]                        # rows = clustered subset of each block
    block_rows: dict[str, np.ndarray]                     # positions of those rows in `table`
    scans: dict[str, pd.DataFrame] = field(default_factory=dict)


class MorphotypeClassifier:
    """Fits or applies the transport and context clusterings independently, then crosses them."""

    def __init__(self, cfg: ClusteringConfig, names: NamesConfig) -> None:
        self.cfg = cfg
        self.names = names
        self.namer = ClusterNamer(names)

    # ── Features ─────────────────────────────────────────────────────────────

    def resolve_features(self, df: pd.DataFrame, extra_blocks: dict[str, str]) -> dict[str, list[str]]:
        """Configured features that exist and are not empty, plus user extra features."""
        out = {}
        for block in BLOCKS:
            wanted = list(self.cfg.block(block).features)
            wanted += [c for c, b in extra_blocks.items() if b == block and c not in wanted]
            usable = []
            for f in wanted:
                if f not in df.columns:
                    log.warning("%s: feature '%s' is not available (metric disabled or dropped)", block, f)
                elif df[f].notna().sum() == 0:
                    log.warning("%s: feature '%s' has no values and is dropped", block, f)
                else:
                    usable.append(f)
            if not usable:
                raise ValueError(f"No usable features left in the {block} block")
            out[block] = usable
        return out

    def correlations(self, df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
        """Feature pairs with |Spearman r| above ``correlation_warning``."""
        corr = df[features].astype(float).corr(method="spearman")
        rows = [(a, b, round(corr.loc[a, b], 3))
                for i, a in enumerate(features) for b in features[i + 1:]
                if abs(corr.loc[a, b]) >= self.cfg.correlation_warning]
        return pd.DataFrame(rows, columns=["feature_a", "feature_b", "spearman_r"])

    @staticmethod
    def context_mask(df: pd.DataFrame) -> np.ndarray:
        """Segments whose context can be clustered (not C_null)."""
        if "context_null" in df.columns:
            return ~df["context_null"].fillna(False).astype(bool).to_numpy()
        return np.ones(len(df), dtype=bool)

    def _block_rows(self, df: pd.DataFrame) -> dict[str, np.ndarray]:
        return {"transport": np.arange(len(df)), "context": np.flatnonzero(self.context_mask(df))}

    # ── Scan / fit / apply ───────────────────────────────────────────────────

    def scan(self, df: pd.DataFrame, extra_blocks: dict[str, str]) -> dict[str, pd.DataFrame]:
        feats = self.resolve_features(df, extra_blocks)
        clusterer = BlockClusterer(self.cfg)
        rows = self._block_rows(df)
        return {b: clusterer.scan(df.iloc[rows[b]], feats[b]) for b in BLOCKS}

    def fit(self, df: pd.DataFrame, extra_blocks: dict[str, str],
            trained_on: list[str]) -> tuple[MorphotypeModel, ClassificationResult]:
        feats = self.resolve_features(df, extra_blocks)
        clusterer = BlockClusterer(self.cfg)
        rows = self._block_rows(df)
        models, results, scans = {}, {}, {}
        for block in BLOCKS:  # independent: neither block sees the other's features or labels
            sub = df.iloc[rows[block]].reset_index(drop=True)
            models[block], results[block], scan = clusterer.fit(sub, feats[block], self.cfg.block(block), block)
            if scan is not None:
                scans[block] = scan
        names = {b: self.namer.cluster_names(b, models[b].centroids) for b in BLOCKS}
        model = MorphotypeModel(models["transport"], models["context"], names,
                                dict(self.names.morphotype), trained_on, self.cfg.model_dump(mode="json"))
        table = self._assemble(df, model, results, rows)
        return model, ClassificationResult(table, results, rows, scans)

    def apply(self, model: MorphotypeModel, df: pd.DataFrame) -> ClassificationResult:
        rows = self._block_rows(df)
        results = {}
        for block in BLOCKS:
            bm = model.block(block)
            missing = [f for f in bm.features if f not in df.columns]
            if missing:
                raise ValueError(f"The model needs {block} features that this city lacks: {missing}")
            results[block] = bm.predict(df.iloc[rows[block]].reset_index(drop=True))
        return ClassificationResult(self._assemble(df, model, results, rows), results, rows)

    # ── Output table ─────────────────────────────────────────────────────────

    def _assemble(self, df: pd.DataFrame, model: MorphotypeModel,
                  results: dict[str, BlockResult], rows: dict[str, np.ndarray]) -> pd.DataFrame:
        n = len(df)
        out = pd.DataFrame(index=df.index)
        for block, prefix in (("transport", "T"), ("context", "C")):
            labels = np.full(n, -1, dtype=int)
            conf = np.full(n, np.nan)
            sil = np.full(n, np.nan)
            r = results[block]
            labels[rows[block]], conf[rows[block]], sil[rows[block]] = r.labels, r.confidence, r.silhouette
            out[f"{prefix}_cluster"] = labels
            out[f"{prefix}_name"] = [model.names[block].get(x, NULL_CONTEXT) for x in labels]
            out[f"{prefix}_confidence"] = conf.round(3)
            out[f"{prefix}_silhouette"] = sil.round(3)
        namer = ClusterNamer(NamesConfig(transport={}, context={}, morphotype=model.morphotype_names))
        t, c = out["T_cluster"].to_numpy(), out["C_cluster"].to_numpy()
        out["morphotype"] = [namer.morphotype_code(a, b) for a, b in zip(t, c)]
        out["morphotype_name"] = [namer.morphotype_name(a, b, model.names["transport"], model.names["context"])
                                  for a, b in zip(t, c)]
        weak_t = (out["T_silhouette"] < self.cfg.min_silhouette) | (out["T_confidence"] < self.cfg.min_confidence)
        weak_c = (out["C_silhouette"] < self.cfg.min_silhouette) | (out["C_confidence"] < self.cfg.min_confidence)
        out["borderline"] = weak_t | (weak_c & (out["C_cluster"] >= 0))
        log.info("Morphotypes: %d segments, %d borderline (%.0f%%)", n, out["borderline"].sum(),
                 100 * out["borderline"].mean() if n else 0)
        return out
