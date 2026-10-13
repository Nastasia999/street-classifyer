"""Street segments (junction-to-junction links) built from OSM or from a user layer."""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
import shapely
from shapely.geometry import LineString, Point

from ..area import StudyArea
from ..config import CityConfig, DualCarriagewayConfig
from ..tags import as_list, parse_bool, resolve_highway

log = logging.getLogger(__name__)


@dataclass
class SegmentNetwork:
    """Undirected street network as junction-to-junction segments.

    ``segments`` is indexed by ``seg_id`` and holds at least:
    ``u, v, geometry, length, highway, oneway, lanes_raw, maxspeed_raw, name,
    osm_ways, in_area, classify, twin_id, outer_side``.
    ``nodes`` is indexed by node id and holds point geometries.
    """

    segments: gpd.GeoDataFrame
    nodes: gpd.GeoDataFrame

    @property
    def analysis(self) -> gpd.GeoDataFrame:
        """Segments that are classified."""
        return self.segments[self.segments["classify"]]


class SegmentNetworkBuilder:
    """Builds a :class:`SegmentNetwork` from OSM or from a user line layer."""

    def __init__(self, cfg: CityConfig, area: StudyArea) -> None:
        self.cfg = cfg
        self.area = area

    # ── Sources ──────────────────────────────────────────────────────────────

    def from_osm(self, G) -> SegmentNetwork:
        import osmnx as ox

        G = ox.project_graph(G, to_crs=self.area.crs)
        tol = self.cfg.network.consolidate_tolerance_m
        if tol > 0:
            G = ox.consolidate_intersections(G, tolerance=tol, rebuild_graph=True,
                                             dead_ends=False, reconnect_edges=True)
        Gu = ox.convert.to_undirected(G)
        nodes, edges = ox.graph_to_gdfs(Gu)
        edges = edges.reset_index()
        segs = gpd.GeoDataFrame({
            "u": edges["u"].values,
            "v": edges["v"].values,
            "highway": edges["highway"].map(
                lambda h: resolve_highway(h, self.cfg.network.highway_types)).values,
            "oneway": edges.get("oneway", pd.Series(False, index=edges.index)).map(parse_bool).values,
            "lanes_raw": self._column(edges, "lanes"),
            "maxspeed_raw": self._column(edges, "maxspeed"),
            "name": self._column(edges, "name"),
            "osm_ways": edges["osmid"].map(lambda x: [int(i) for i in as_list(x)]).values,
            "user_id": pd.NA,
        }, geometry=edges.geometry.values, crs=self.area.crs)
        nodes = gpd.GeoDataFrame(geometry=nodes.geometry, crs=self.area.crs)
        return self._finalise(segs, nodes, oriented=True)

    def from_lines(self, lines: gpd.GeoDataFrame, id_column: str | None) -> SegmentNetwork:
        """User network: lines must already be split at junctions; endpoints are snapped."""
        lines = lines.explode(index_parts=False).reset_index(drop=True)
        lines = lines[lines.geometry.length > 0]
        coords = [list(g.coords) for g in lines.geometry]
        ends = np.array([[c[0][0], c[0][1]] for c in coords] + [[c[-1][0], c[-1][1]] for c in coords])
        node_of_end, node_xy = self._snap(ends, self.cfg.network.snap_tolerance_m)
        n = len(lines)
        geoms = []
        for i, c in enumerate(coords):
            c[0], c[-1] = tuple(node_xy[node_of_end[i]]), tuple(node_xy[node_of_end[n + i]])
            geoms.append(LineString(c))
        types = self.cfg.network.highway_types
        segs = gpd.GeoDataFrame({
            "u": node_of_end[:n],
            "v": node_of_end[n:],
            "highway": (lines["highway"].map(lambda h: resolve_highway(h, types))
                        if "highway" in lines else pd.NA),
            "oneway": lines["oneway"].map(parse_bool) if "oneway" in lines else False,
            "lanes_raw": lines["lanes"] if "lanes" in lines else pd.NA,
            "maxspeed_raw": lines["maxspeed"] if "maxspeed" in lines else pd.NA,
            "name": lines["name"] if "name" in lines else pd.NA,
            "osm_ways": (lines["osm_id"].map(lambda x: [int(i) for i in as_list(x)])
                         if "osm_id" in lines else [[] for _ in range(n)]),
            "user_id": lines[id_column].values if id_column else pd.NA,
        }, geometry=geoms, crs=self.area.crs)
        nodes = gpd.GeoDataFrame(geometry=[Point(xy) for xy in node_xy], crs=self.area.crs)
        return self._finalise(segs, nodes, oriented=False)

    # ── Shared steps ─────────────────────────────────────────────────────────

    @staticmethod
    def _column(df: pd.DataFrame, name: str):
        return df[name].values if name in df.columns else pd.NA

    @staticmethod
    def _snap(points: np.ndarray, tol: float) -> tuple[np.ndarray, np.ndarray]:
        """Cluster points closer than ``tol``; returns cluster id per point and cluster centroids."""
        pairs = cKDTree(points).query_pairs(tol, output_type="ndarray")
        n = len(points)
        adj = coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(n, n))
        _, labels = connected_components(adj, directed=False)
        centroids = pd.DataFrame(points).groupby(labels).mean().to_numpy()
        return labels, centroids

    def _finalise(self, segs: gpd.GeoDataFrame, nodes: gpd.GeoDataFrame, oriented: bool) -> SegmentNetwork:
        net = self.cfg.network
        segs = segs[segs.geometry.length > 0].reset_index(drop=True)
        if net.merge_pseudo_junctions:
            segs = PseudoJunctionMerger(net.highway_types).merge(segs)
        segs = segs.reset_index(drop=True)
        segs.index.name = "seg_id"
        segs["length"] = segs.geometry.length
        midpoints = segs.geometry.interpolate(0.5, normalized=True)
        segs["in_area"] = midpoints.within(self.area.polygon)
        segs["classify"] = (
            segs["in_area"]
            & (segs["length"] >= net.min_segment_length_m)
            & ~segs["highway"].isin(net.unclassified_highway_types)
        )
        segs["twin_id"] = -1
        segs["outer_side"] = None
        if net.dual_carriageway.detect:
            DualCarriagewayDetector(net.dual_carriageway, oriented).detect(segs)
        log.info("Network: %d segments (%d in area, %d classified, %d twinned carriageways)",
                 len(segs), segs["in_area"].sum(), segs["classify"].sum(), (segs["twin_id"] >= 0).sum())
        return SegmentNetwork(segs, nodes)


class DualCarriagewayDetector:
    """Finds the parallel opposite carriageway ("twin") of one-way segments.

    A twin is another one-way segment within ``max_distance_m`` that is parallel
    within ``max_angle_deg`` and runs alongside at least ``min_overlap`` of the
    segment length. When geometries follow the travel direction (``oriented``,
    true for OSM one-way ways) the twin must also carry traffic the opposite way,
    which rules out parallel one-way streets in the same direction. The side
    facing away from the twin is the segment's outer side.
    """

    _SAMPLES = 11

    def __init__(self, cfg: DualCarriagewayConfig, oriented: bool = False) -> None:
        self.cfg = cfg
        self.oriented = oriented

    def detect(self, segs: gpd.GeoDataFrame) -> None:
        oneway = segs[segs["oneway"]]
        if oneway.empty:
            return
        sindex = oneway.sindex
        geoms = oneway.geometry
        for sid, geom in geoms.items():
            cand_pos = sindex.query(geom.buffer(self.cfg.max_distance_m), predicate="intersects")
            best, best_score = None, (0.0, math.inf)
            samples = [geom.interpolate(t, normalized=True) for t in np.linspace(0.05, 0.95, self._SAMPLES)]
            for pos in cand_pos:
                tid = geoms.index[pos]
                if tid == sid:
                    continue
                other = geoms.iloc[pos]
                if self._angle_between(geom, other) > self.cfg.max_angle_deg:
                    continue
                dists = np.array([other.distance(p) for p in samples])
                # alongside = the nearest point on the twin is inside it, not its end
                # (otherwise the next segment of the same street would qualify)
                t = np.array([other.project(p) for p in samples])
                interior = (t > 1.0) & (t < other.length - 1.0)
                overlap = float(np.mean(interior & (dists > 0.5) & (dists <= self.cfg.max_distance_m)))
                if overlap < self.cfg.min_overlap:
                    continue
                score = (overlap, float(np.median(dists)))
                if score[0] > best_score[0] or (score[0] == best_score[0] and score[1] < best_score[1]):
                    best, best_score = tid, score
            if best is not None:
                segs.at[sid, "twin_id"] = best
                segs.at[sid, "outer_side"] = self._outer_side(geom, geoms.loc[best])

    @staticmethod
    def _bearing(line: LineString) -> float:
        (x0, y0), (x1, y1) = line.coords[0], line.coords[-1]
        return math.degrees(math.atan2(y1 - y0, x1 - x0)) % 360.0

    def _angle_between(self, a: LineString, b: LineString) -> float:
        """Deviation from being parallel; with ``oriented``, from running in opposite directions."""
        d = abs(self._bearing(a) - self._bearing(b)) % 360.0
        d = min(d, 360.0 - d)  # 0..180: 0 = same direction, 180 = opposite
        return 180.0 - d if self.oriented else min(d, 180.0 - d)

    @staticmethod
    def _outer_side(line: LineString, twin: LineString) -> str:
        mid = line.interpolate(0.5, normalized=True)
        ahead = line.interpolate(min(line.length, line.project(mid) + 1.0))
        behind = line.interpolate(max(0.0, line.project(mid) - 1.0))
        dx, dy = ahead.x - behind.x, ahead.y - behind.y
        target = twin.interpolate(twin.project(mid))
        cross = dx * (target.y - mid.y) - dy * (target.x - mid.x)
        return "right" if cross > 0 else "left"  # twin on the left -> outer side is right


class PseudoJunctionMerger:
    """Joins segments that meet at a node where nothing else meets (degree 2).

    A segment must run from junction to junction. Nodes of degree 2 are left
    behind by intersection consolidation (and by one-way/two-way changes or
    user networks split at arbitrary points); the chain of segments through
    them is merged into one segment. Geometry is joined exactly (no
    straightening); attributes are combined: the most important ``highway``,
    one-way if most of the length is one-way, all values of lanes / maxspeed /
    names / OSM ways / user ids.
    """

    def __init__(self, highway_ranking: list[str]) -> None:
        self.ranking = highway_ranking

    def merge(self, segs: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        u, v = segs["u"].to_numpy(), segs["v"].to_numpy()
        incident: dict = {}
        for i in range(len(segs)):
            incident.setdefault(u[i], []).append(i)
            incident.setdefault(v[i], []).append(i)
        pseudo = {n for n, ids in incident.items() if len(ids) == 2 and ids[0] != ids[1]}
        if not pseudo:
            return segs

        seen = np.zeros(len(segs), dtype=bool)
        kept, kept_order, merged, merged_order = [], [], [], []
        for start in range(len(segs)):
            if seen[start]:
                continue
            seen[start] = True
            chain, terminals = [start], []
            for node in (u[start], v[start]):  # walk both ways from the start segment
                cur = start
                while node in pseudo:
                    nxt = incident[node][0] if incident[node][1] == cur else incident[node][1]
                    if seen[nxt]:  # closed ring
                        break
                    seen[nxt] = True
                    chain.append(nxt)
                    node = v[nxt] if u[nxt] == node else u[nxt]
                    cur = nxt
                terminals.append(node)
            row = self._combine(segs.iloc[chain], terminals) if len(chain) > 1 else None
            if row is None:
                kept.extend(chain)
                kept_order.extend([len(kept_order) + len(merged_order) + k for k in range(len(chain))])
            else:
                merged.append(row)
                merged_order.append(len(kept_order) + len(merged_order))
        # only merged rows are rebuilt; the rest keep their dtypes, and the order is unchanged
        parts = [segs.iloc[kept].assign(_order=kept_order)]
        if merged:
            parts.append(gpd.GeoDataFrame(merged, geometry="geometry", crs=segs.crs).assign(_order=merged_order))
        out = pd.concat(parts).sort_values("_order").drop(columns="_order")
        out = out.astype({c: segs[c].dtype for c in ("u", "v", "oneway") if c in segs})
        log.info("Network: merged segments through %d pseudo-junctions (%d -> %d segments)",
                 len(pseudo), len(segs), len(out))
        return gpd.GeoDataFrame(out, geometry="geometry", crs=segs.crs)

    def _combine(self, part: gpd.GeoDataFrame, terminals: list) -> pd.Series:
        lengths = part.geometry.length.to_numpy()
        oneway = bool(lengths[part["oneway"].to_numpy(dtype=bool)].sum() > lengths.sum() / 2)
        parts = shapely.MultiLineString(list(part.geometry))
        line = shapely.line_merge(parts, directed=True) if oneway else parts
        if line.geom_type != "LineString":  # directions mixed, or a two-way chain
            line = shapely.line_merge(parts)
        if line.geom_type != "LineString":  # not a simple chain: leave it unmerged
            log.debug("Could not merge segments %s", list(part.index))
            return None
        row = part.iloc[0].copy()
        row["u"], row["v"] = self._orient(part, line, *terminals)
        row["geometry"] = line
        row["oneway"] = oneway
        row["highway"] = resolve_highway(list(part["highway"]), self.ranking)
        for col in ("lanes_raw", "maxspeed_raw"):
            row[col] = [x for val in part[col] for x in as_list(val)]
        names = list(dict.fromkeys(str(x) for val in part["name"] for x in as_list(val)))
        row["name"] = names[0] if len(names) == 1 else (names or pd.NA)
        row["osm_ways"] = list(dict.fromkeys(w for ways in part["osm_ways"] for w in ways))
        ids = [x for val in part["user_id"] for x in as_list(val)]
        row["user_id"] = ids or pd.NA  # a merged user segment keeps all its source ids
        return row

    @staticmethod
    def _orient(part: gpd.GeoDataFrame, line, a, b) -> tuple:
        """(u, v) with u = the terminal node at the start of the merged line."""
        if a == b:
            return a, b
        seg_a = part[(part["u"] == a) | (part["v"] == a)].geometry.iloc[0]
        start = shapely.Point(line.coords[0])
        end = shapely.Point(line.coords[-1])
        return (a, b) if seg_a.distance(start) <= seg_a.distance(end) else (b, a)
