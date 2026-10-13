import geopandas as gpd
import numpy as np
import pytest
from shapely.geometry import LineString, Point

from street_morphotypes.config import SpaceSyntaxConfig
from street_morphotypes.network.segments import SegmentNetwork
from street_morphotypes.network.space_syntax import AngularSegmentAnalysis, DualGraph, _turn_angle


def grid_network(n: int = 5, step: float = 100.0, jitter: float = 0.0, seed: int = 0) -> SegmentNetwork:
    """n x n grid of junctions, segments between neighbours."""
    rng = np.random.default_rng(seed)
    xy = {}
    for i in range(n):
        for j in range(n):
            dx, dy = rng.normal(0, jitter, 2) if jitter else (0, 0)
            xy[i * n + j] = (i * step + dx, j * step + dy)
    rows = []
    for i in range(n):
        for j in range(n):
            a = i * n + j
            if i + 1 < n:
                rows.append((a, a + n))
            if j + 1 < n:
                rows.append((a, a + 1))
    segs = gpd.GeoDataFrame({"u": [r[0] for r in rows], "v": [r[1] for r in rows]},
                            geometry=[LineString([xy[u], xy[v]]) for u, v in rows])
    segs.index.name = "seg_id"
    segs["length"] = segs.geometry.length
    nodes = gpd.GeoDataFrame(geometry=[Point(xy[k]) for k in sorted(xy)])
    return SegmentNetwork(segs, nodes)


def test_turn_angle():
    assert _turn_angle(np.array([-1.0, 0]), np.array([1.0, 0])) == pytest.approx(0.0)    # straight on
    assert _turn_angle(np.array([-1.0, 0]), np.array([0, 1.0])) == pytest.approx(90.0)   # right angle
    assert _turn_angle(np.array([1.0, 0]), np.array([1.0, 0])) == pytest.approx(180.0)   # U-turn


def test_dual_graph_of_grid():
    g = DualGraph.from_network(grid_network(3), direction_sample_m=10)
    # straight continuations through the centre junction cost ~0, turns 90 deg
    assert set(np.round(g.angle_deg)) == {0.0, 90.0}
    assert g.n == 12


def cfg(radii):
    return SpaceSyntaxConfig(radii=radii, angle_unit_deg=90, direction_sample_m=10, n_jobs=1)


def test_metric_radius_without_limit_equals_igraph_global():
    """Python Brandes with an infinite radius must reproduce igraph closeness and betweenness."""
    net = grid_network(6, jitter=6.0, seed=1)
    g = DualGraph.from_network(net, direction_sample_m=10)
    asa = AngularSegmentAnalysis(g, cfg(["n"]))
    targets = np.ones(g.n, dtype=bool)
    nc_g, td_g, ch_g = asa._global(targets)
    nc_r, td_r, ch_r = asa._metric_radius(1e12, targets, targets)
    np.testing.assert_allclose(nc_r, nc_g)
    np.testing.assert_allclose(td_r, td_g, rtol=1e-6)
    np.testing.assert_allclose(ch_r, ch_g, rtol=1e-6, atol=1e-6)


def test_metric_radius_limits_reach():
    net = grid_network(6)
    g = DualGraph.from_network(net, direction_sample_m=10)
    asa = AngularSegmentAnalysis(g, cfg([150]))
    targets = np.ones(g.n, dtype=bool)
    nc, _, _ = asa._metric_radius(150.0, targets, targets)
    # midpoint-to-midpoint distance between neighbours is 100 m: only direct neighbours are reachable
    np.testing.assert_array_equal(nc, g.degree() + 1)


def test_nain_nach_formulas():
    net = grid_network(4)
    g = DualGraph.from_network(net, direction_sample_m=10)
    out = AngularSegmentAnalysis(g, cfg(["n"])).run(np.ones(g.n, bool), np.zeros(g.n))
    nc, td, ch = out["ss_nc_n"], out["ss_td_n"], out["ss_choice_n"]
    np.testing.assert_allclose(out["ss_nain_n"], nc ** 1.2 / (td + 2))
    np.testing.assert_allclose(out["ss_nach_n"], np.log(ch + 1) / np.log(td + 3))
    # central segments of a grid are more integrated than peripheral ones
    centre = out["ss_nain_n"].idxmax()
    assert net.segments.geometry[centre].centroid.distance(Point(150, 150)) < 110
