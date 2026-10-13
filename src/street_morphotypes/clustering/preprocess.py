"""Feature preprocessing: median imputation -> log1p for skewed features -> robust scaling."""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


class FeatureScaler:
    """Fit on one dataset, apply unchanged to another (needed for ``apply`` mode).

    1. Near-constant features (the most frequent value covers more than
       ``max_mode_share`` of the segments) are dropped: a feature that is 0 almost
       everywhere has no typological content, and its few non-zero segments would
       become extreme outliers after scaling.
    2. Missing values -> median of the training data.
    3. ``log1p`` for non-negative features whose skewness exceeds ``skew_threshold``
       (intensities and densities are heavily right-skewed).
    4. ``(x - median) / IQR``: robust to the few very dense streets that would
       otherwise pull the whole partition. Features with IQR = 0 fall back to the
       standard deviation (dividing by 1 would let their raw units dominate).
    5. Scaled values are clipped to ``±clip_scaled`` so that a single extreme
       segment cannot form a cluster of its own.
    """

    def __init__(self, skew_threshold: float = 1.0, max_mode_share: float = 1.0,
                 clip_scaled: float | None = None) -> None:
        self.skew_threshold = skew_threshold
        self.max_mode_share = max_mode_share
        self.clip_scaled = clip_scaled
        self.features: list[str] = []
        self.dropped: dict[str, str] = {}
        self.fill_: pd.Series | None = None
        self.log_cols_: list[str] = []
        self.center_: pd.Series | None = None
        self.scale_: pd.Series | None = None

    @classmethod
    def from_config(cls, cfg) -> "FeatureScaler":
        return cls(cfg.skew_threshold, cfg.max_mode_share, cfg.clip_scaled)

    def fit(self, df: pd.DataFrame, features: list[str]) -> "FeatureScaler":
        X = df[features].astype(float)
        self.dropped = {}
        for c in features:
            mode_share = X[c].value_counts(normalize=True, dropna=True).max()
            if not mode_share < 1.0:
                self.dropped[c] = "constant"
            elif mode_share > self.max_mode_share:
                self.dropped[c] = f"near-constant ({mode_share:.0%} identical values)"
        if self.dropped:
            log.warning("Features dropped from clustering: %s", self.dropped)
        kept = [c for c in features if c not in self.dropped]
        if not kept:
            raise ValueError(f"All features were dropped as (near-)constant: {self.dropped}")
        X = X[kept]
        self.fill_ = X.median()
        X = X.fillna(self.fill_)
        self.log_cols_ = [c for c in kept if (X[c] >= 0).all() and X[c].skew() > self.skew_threshold]
        X[self.log_cols_] = np.log1p(X[self.log_cols_])
        center = X.median()
        iqr = X.quantile(0.75) - X.quantile(0.25)
        scale = iqr.where(iqr > 0, X.std(ddof=0))
        fallback = [c for c in kept if not iqr[c] > 0]
        if fallback:
            log.info("IQR = 0, scaled by standard deviation instead: %s", fallback)
        self.features = kept
        self.center_, self.scale_ = center, scale
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        X = df[self.features].astype(float).fillna(self.fill_)
        X[self.log_cols_] = np.log1p(X[self.log_cols_].clip(lower=0))
        Z = ((X - self.center_) / self.scale_).to_numpy()
        if self.clip_scaled is not None:
            Z = np.clip(Z, -self.clip_scaled, self.clip_scaled)
        return Z

    def fit_transform(self, df: pd.DataFrame, features: list[str]) -> np.ndarray:
        return self.fit(df, features).transform(df)
