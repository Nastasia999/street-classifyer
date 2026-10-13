"""Angular segment analysis (space syntax) on the segment (dual) graph.

Vertices of the dual graph are street segments; two segments are linked when
they share a junction. The cost of a transition is the turn angle divided by
``angle_unit_deg`` (90 deg = 1, as in depthmapX), so the shortest path is the
path of least angular change.

For every radius ``r`` (``"n"`` = whole graph, or metres along the network)
the analysis returns per segment:

- ``NC``  node count: segments reachable within the radius, origin included
- ``TD``  total angular depth to them
- ``CH``  choice: number of least-angle paths between pairs of segments
          (both ends within the radius) that pass through the segment
- ``NAIN = NC^1.2 / (TD + 2)``           (Hillier, Yang & Turner 2012)
- ``NACH = log(CH + 1) / log(TD + 3)``   (Hillier, Yang & Turner 2012)

Rn is computed with igraph (C). Metric radii use a Brandes-style
least-angle search that stops when the metric distance along the path,
measured between segment midpoints, exceeds ``r`` (the depthmapX approach).
"""
from __future__ import annotations

import heapq
import logging
import math
import os
from dataclasses import dataclass
from functools import cached_property

import igraph as ig
import numpy as np
import pandas as pd
import shapely
from joblib import Parallel, delayed

from ..config import SpaceSyntaxConfig
from .segments import SegmentNetwork

log = logging.getLogger(__name__)

EPS = 1e-6           # added to every transition so that straight continuations are not free
_TIE = 1e-9          # tolerance for equal-cost paths


@dataclass
class DualGraph:
    """Segment graph in CSR form (both directions stored)."""

    seg_ids: np.ndarray      # position -> seg_id
    lengths: np.ndarray
    src: np.ndarray          # undirected transitions, one row per pair
    dst: np.ndarray
    angle_deg: np.ndarray

    @property
    def n(self) -> int:
        return len(self.seg_ids)

    def degree(self) -> np.ndarray:
        return np.bincount(np.concatenate([self.src, self.dst]), minlength=self.n)

    @classmethod
    def from_network(cls, network: SegmentNetwork, direction_sample_m: float) -> "DualGraph":
        segs = network.segments
        geoms = segs.geometry.values
        lengths = segs["length"].to_numpy()
        n = len(segs)
        node_xy = {nid: (p.x, p.y) for nid, p in network.nodes.geometry.items()}

        starts = shapely.get_point(geoms, 0)
        ends = shapely.get_point(geoms, -1)
        step = np.minimum(direction_sample_m, lengths / 2)
        inner_start = shapely.line_interpolate_point(geoms, step)
        inner_end = shapely.line_interpolate_point(geoms, lengths - step)
        xy = lambda pts: shapely.get_coordinates(pts)  # noqa: E731
        s_xy, e_xy, is_xy, ie_xy = xy(starts), xy(ends), xy(inner_start), xy(inner_end)
        out_start = is_xy - s_xy   # leaving the junction at the start, into the segment
        out_end = ie_xy - e_xy

        # (junction, position, outgoing vector) for every segment end
        incidence: dict[int, list[tuple[int, np.ndarray]]] = {}
        u_arr, v_arr = segs["u"].to_numpy(), segs["v"].to_numpy()
        for i in range(n):
            u, v = u_arr[i], v_arr[i]
            if u == v:
                ends_at = [(u, out_start[i]), (u, out_end[i])]
            else:
                ux, uy = node_xy[u]
                start_at_u = math.hypot(s_xy[i, 0] - ux, s_xy[i, 1] - uy) <= \
                    math.hypot(e_xy[i, 0] - ux, e_xy[i, 1] - uy)
                ends_at = ([(u, out_start[i]), (v, out_end[i])] if start_at_u
                           else [(u, out_end[i]), (v, out_start[i])])
            for node, vec in ends_at:
                incidence.setdefault(node, []).append((i, vec))

        best: dict[tuple[int, int], float] = {}
        for members in incidence.values():
            for a in range(len(members)):
                ia, va = members[a]
                for b in range(a + 1, len(members)):
                    ib, vb = members[b]
                    if ia == ib:
                        continue
                    key = (ia, ib) if ia < ib else (ib, ia)
                    turn = _turn_angle(va, vb)
                    if turn < best.get(key, math.inf):
                        best[key] = turn
        pairs = np.array(list(best.keys()), dtype=np.int64).reshape(-1, 2)
        angles = np.fromiter(best.values(), dtype=float, count=len(best))
        log.info("Dual graph: %d segments, %d transitions", n, len(pairs))
        return cls(segs.index.to_numpy(), lengths, pairs[:, 0], pairs[:, 1], angles)


def _turn_angle(out_a: np.ndarray, out_b: np.ndarray) -> float:
    """Direction change (0..180 deg) when moving from segment a into segment b.

    Both vectors point away from the shared junction; going straight through
    means they are opposite (180 deg apart), i.e. a turn of 0 deg.
    """
    na, nb = math.hypot(*out_a), math.hypot(*out_b)
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    cos = (out_a[0] * out_b[0] + out_a[1] * out_b[1]) / (na * nb)
    return 180.0 - math.degrees(math.acos(max(-1.0, min(1.0, cos))))


class AngularSegmentAnalysis:
    """Computes NC, TD, choice, NAIN and NACH for every configured radius."""

    def __init__(self, graph: DualGraph, cfg: SpaceSyntaxConfig) -> None:
        self.g = graph
        self.cfg = cfg
        self.cost = graph.angle_deg / cfg.angle_unit_deg + EPS
        self.metric = (graph.lengths[graph.src] + graph.lengths[graph.dst]) / 2

    def run(self, targets: np.ndarray, dist_to_area: np.ndarray) -> pd.DataFrame:
        """
        targets       boolean mask of segments that need results (the study area)
        dist_to_area  euclidean distance of each segment midpoint to the study area (0 inside);
                      used to skip sources that cannot reach the area within a metric radius
        """
        out = pd.DataFrame(index=pd.Index(self.g.seg_ids, name="seg_id"))
        out["ss_connectivity"] = self.g.degree()
        for r in self.cfg.radii:
            label = str(r)
            log.info("Space syntax: radius %s ...", label)
            if r == "n":
                nc, td, ch = self._global(targets)
            else:
                nc, td, ch = self._metric_radius(float(r), targets, dist_to_area <= r)
            with np.errstate(divide="ignore", invalid="ignore"):
                out[f"ss_nc_{label}"] = nc
                out[f"ss_td_{label}"] = td
                out[f"ss_mean_depth_{label}"] = np.where(nc > 1, td / (nc - 1), np.nan)
                out[f"ss_choice_{label}"] = ch
                out[f"ss_nain_{label}"] = nc ** 1.2 / (td + 2)
                out[f"ss_nach_{label}"] = np.log(ch + 1) / np.log(td + 3)
        out = out.astype(float)
        out.loc[~targets] = np.nan
        return out

    # ── Rn: igraph ───────────────────────────────────────────────────────────

    def _global(self, targets: np.ndarray):
        n = self.g.n
        graph = ig.Graph(n=n, edges=np.column_stack([self.g.src, self.g.dst]).tolist(), directed=False)
        graph.es["w"] = self.cost.tolist()
        components = graph.connected_components()
        comp_size = np.array(components.sizes())[components.membership]
        tgt = np.flatnonzero(targets)
        closeness = np.array(graph.closeness(vertices=tgt.tolist(), weights="w", normalized=False),
                             dtype=float)
        nc = np.full(n, np.nan)
        td = np.full(n, np.nan)
        nc[tgt] = comp_size[tgt]
        with np.errstate(divide="ignore"):
            td[tgt] = np.where(closeness > 0, 1.0 / closeness, 0.0)
        log.info("Space syntax: global choice on %d segments (igraph) ...", n)
        ch = np.array(graph.betweenness(weights="w", directed=False), dtype=float)
        return nc, td, ch

    # ── Metric radius: Brandes with a metric cut-off ─────────────────────────

    def _metric_radius(self, radius: float, targets: np.ndarray, sources: np.ndarray):
        n = self.g.n
        indptr, indices, cost, metric = self._csr
        src_ids = np.flatnonzero(sources)
        n_jobs = self.cfg.n_jobs if self.cfg.n_jobs > 0 else (os.cpu_count() or 1)
        # each chunk converts the graph to Python lists once, so keep chunks few but balanced
        chunks = [c for c in np.array_split(src_ids, max(1, n_jobs * 2)) if len(c)]
        log.info("Space syntax: r=%g m, %d sources, %d workers", radius, len(src_ids), n_jobs)
        results = Parallel(n_jobs=n_jobs)(
            delayed(_brandes_chunk)(chunk, indptr, indices, cost, metric, radius, targets, n)
            for chunk in chunks
        )
        nc = np.full(n, np.nan)
        td = np.full(n, np.nan)
        ch = np.zeros(n)
        for ids, nc_part, td_part, ch_part in results:
            nc[ids] = nc_part
            td[ids] = td_part
            ch += ch_part
        return nc, td, ch / 2.0  # undirected: every pair was counted from both ends

    @cached_property
    def _csr(self):
        """Both directions of every transition, sorted by origin (built once per analysis)."""
        g = self.g
        a = np.concatenate([g.src, g.dst])
        b = np.concatenate([g.dst, g.src])
        cost = np.concatenate([self.cost, self.cost])
        metric = np.concatenate([self.metric, self.metric])
        order = np.argsort(a, kind="stable")
        indptr = np.zeros(g.n + 1, dtype=np.int64)
        np.add.at(indptr, a + 1, 1)
        return np.cumsum(indptr), b[order], cost[order], metric[order]


def _brandes_chunk(sources, indptr, indices, cost, metric, radius, targets, n):
    """Least-angle Brandes from each source, restricted to metric distance <= radius."""
    indptr, indices = indptr.tolist(), indices.tolist()
    cost, metric = cost.tolist(), metric.tolist()
    bc = np.zeros(n)
    keep = [int(s) for s in sources if targets[s]]
    nc_out, td_out = [], []
    for s in sources.tolist():
        dist = {s: 0.0}
        mdist = {s: 0.0}
        sigma = {s: 1.0}
        preds: dict[int, list[int]] = {s: []}
        order: list[int] = []
        done: set[int] = set()
        heap = [(0.0, s)]
        while heap:
            d, v = heapq.heappop(heap)
            if v in done:
                continue
            done.add(v)
            order.append(v)
            mv = mdist[v]
            for k in range(indptr[v], indptr[v + 1]):
                w = indices[k]
                if w in done:
                    continue
                m = mv + metric[k]
                if m > radius:
                    continue
                nd = d + cost[k]
                old = dist.get(w)
                if old is None or nd < old - _TIE:
                    dist[w], mdist[w], sigma[w], preds[w] = nd, m, sigma[v], [v]
                    heapq.heappush(heap, (nd, w))
                elif nd <= old + _TIE:
                    sigma[w] += sigma[v]
                    preds[w].append(v)
        if targets[s]:
            nc_out.append(len(order))
            td_out.append(sum(dist[v] for v in order))
        delta = dict.fromkeys(order, 0.0)
        for w in reversed(order):
            coeff = (1.0 + delta[w]) / sigma[w]
            for v in preds[w]:
                delta[v] += sigma[v] * coeff
            if w != s:
                bc[w] += delta[w]
    return np.array(keep, dtype=np.int64), np.array(nc_out, float), np.array(td_out, float), bc
