"""Membership confidence: posterior probabilities under a Gaussian model of the clusters."""
from __future__ import annotations

import numpy as np
from scipy.special import logsumexp


class GaussianConfidence:
    """A Gaussian mixture whose components *are* the given clusters.

    Means, covariances and weights are estimated from the partition itself
    (no EM), so component j always corresponds to cluster j. The confidence of
    a segment is the posterior probability of its own cluster: close to 1 deep
    inside a cluster, close to 1/k between clusters. (A freely fitted GMM, even
    when started at the KMeans centroids, drifts to components that no longer
    match the clusters, and its posterior then describes a different partition.)
    """

    def __init__(self, covariance_type: str = "full", reg_covar: float = 1e-3) -> None:
        self.covariance_type = covariance_type
        self.reg_covar = reg_covar
        self.means_: np.ndarray | None = None
        self.covariances_: list[np.ndarray] = []
        self.log_weights_: np.ndarray | None = None

    def fit(self, Z: np.ndarray, labels: np.ndarray) -> "GaussianConfidence":
        k, d = int(labels.max()) + 1, Z.shape[1]
        self.means_ = np.vstack([Z[labels == j].mean(axis=0) for j in range(k)])
        sizes = np.bincount(labels, minlength=k)
        self.log_weights_ = np.log(sizes / sizes.sum())
        resid = Z - self.means_[labels]
        pooled = np.atleast_2d(np.cov(resid, rowvar=False, bias=True)) if len(Z) > 1 else np.eye(d)
        covs = []
        for j in range(k):
            Rj = resid[labels == j]
            if self.covariance_type == "tied" or len(Rj) <= d:
                cov = pooled  # too few members for an own covariance
            elif self.covariance_type == "full":
                cov = np.atleast_2d(np.cov(Rj, rowvar=False, bias=True))
            elif self.covariance_type == "diag":
                cov = np.diag(Rj.var(axis=0))
            else:  # spherical
                cov = np.eye(d) * Rj.var()
            covs.append(cov + self.reg_covar * np.eye(d))
        self.covariances_ = covs
        return self

    def predict_proba(self, Z: np.ndarray) -> np.ndarray:
        logp = np.column_stack([
            self._log_gauss(Z, m, c) + w for m, c, w in zip(self.means_, self.covariances_, self.log_weights_)
        ])
        return np.exp(logp - logsumexp(logp, axis=1, keepdims=True))

    @staticmethod
    def _log_gauss(Z: np.ndarray, mean: np.ndarray, cov: np.ndarray) -> np.ndarray:
        L = np.linalg.cholesky(cov)
        sol = np.linalg.solve(L, (Z - mean).T)
        maha = (sol ** 2).sum(axis=0)
        logdet = 2 * np.log(np.diag(L)).sum()
        return -0.5 * (maha + logdet + Z.shape[1] * np.log(2 * np.pi))
