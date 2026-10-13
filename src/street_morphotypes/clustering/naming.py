"""Readable cluster and morphotype names, generated from profiles or taken from the config."""
from __future__ import annotations

import logging
import re

import pandas as pd

from ..config import NamesConfig
from ..labels import label

log = logging.getLogger(__name__)

_PREFIX = {"transport": "T", "context": "C"}
NULL_CONTEXT = "C_null"


class ClusterNamer:
    """Names a cluster after its most distinctive features.

    A cluster centroid is expressed in robust-scaled units (IQRs from the
    median); the two features furthest from 0 (at least ``threshold``) give the
    name, e.g. "T2 · high through-movement Rn, high PT routes".
    """

    def __init__(self, names: NamesConfig, threshold: float = 0.5, top: int = 2) -> None:
        self.names = names
        self.threshold = threshold
        self.top = top

    def cluster_names(self, block: str, centroids: pd.DataFrame) -> dict[int, str]:
        manual: dict[int, str] = getattr(self.names, block)
        unknown = sorted(set(manual) - set(centroids.index))
        if unknown:
            log.warning("names.%s: no clusters %s (k = %d); were the names written for another run?",
                        block, unknown, len(centroids))
        parts = {cid: self._parts(row) for cid, row in centroids.iterrows()}
        shown = {cid: self.top for cid in parts}
        for _ in range(3):  # clusters named by the same features get one more feature
            sets = {cid: frozenset(parts[cid][: shown[cid]]) for cid in parts}
            dups = [cid for cid in parts if list(sets.values()).count(sets[cid]) > 1]
            if not dups:
                break
            for cid in dups:
                shown[cid] += 1
        out = {}
        for cid in centroids.index:
            code = f"{_PREFIX[block]}{cid}"
            if cid in manual:
                out[cid] = f"{code} · {manual[cid]}"
                continue
            words = parts[cid][: shown[cid]]
            out[cid] = f"{code} · " + (", ".join(words) if words else "average profile")
        return out

    def descriptions(self, block: str, centroids: pd.DataFrame) -> dict[int, str]:
        """Generated profile of every cluster ("high PT stops, high PT routes"), ignoring manual names."""
        auto = ClusterNamer(NamesConfig(transport={}, context={}, morphotype={}), self.threshold, self.top)
        return {cid: name.split(" · ", 1)[1] for cid, name in auto.cluster_names(block, centroids).items()}

    def _parts(self, row: pd.Series) -> list[str]:
        """Distinctive features of a centroid, strongest first, one per measure."""
        parts, measures = [], set()
        for f in row[row.abs() >= self.threshold].abs().sort_values(ascending=False).index:
            measure = re.sub(r"_(n|\d+)$", "", f)  # the same measure at another radius adds nothing
            if measure not in measures:
                measures.add(measure)
                parts.append(f"{'high' if row[f] > 0 else 'low'} {label(f, short=True)}")
        return parts

    def morphotype_code(self, t: int, c: int) -> str:
        return f"T{t}-{NULL_CONTEXT}" if c < 0 else f"T{t}-C{c}"

    def morphotype_name(self, t: int, c: int, t_names: dict[int, str], c_names: dict[int, str]) -> str:
        key = f"{t}-{c}"
        if key in self.names.morphotype:
            return self.names.morphotype[key]
        c_name = "no reliable building data" if c < 0 else c_names[c].split(" · ", 1)[-1]
        return f"{t_names[t].split(' · ', 1)[-1]} | {c_name}"
