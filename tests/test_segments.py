import geopandas as gpd
from shapely.geometry import LineString

from street_morphotypes.config import DualCarriagewayConfig
from street_morphotypes.network.segments import DualCarriagewayDetector

CFG = DualCarriagewayConfig(detect=True, max_distance_m=40, max_angle_deg=20, min_overlap=0.5)


def segments(lines, oneway=True):
    gdf = gpd.GeoDataFrame({"oneway": [oneway] * len(lines)}, geometry=lines)
    gdf["twin_id"] = -1
    gdf["outer_side"] = None
    return gdf


def test_opposite_carriageways_are_twins_with_outer_sides():
    # right-hand traffic: eastbound on the south carriageway, westbound on the north one
    segs = segments([LineString([(0, 0), (200, 0)]), LineString([(200, 20), (0, 20)])])
    DualCarriagewayDetector(CFG, oriented=True).detect(segs)
    assert segs["twin_id"].tolist() == [1, 0]
    assert segs["outer_side"].tolist() == ["right", "right"]


def test_next_segment_of_same_street_is_not_a_twin():
    segs = segments([LineString([(0, 0), (60, 0)]), LineString([(60, 0), (120, 0)])])
    DualCarriagewayDetector(CFG, oriented=True).detect(segs)
    assert (segs["twin_id"] == -1).all()


def test_parallel_one_way_streets_in_same_direction_are_not_twins():
    segs = segments([LineString([(0, 0), (200, 0)]), LineString([(0, 30), (200, 30)])])
    DualCarriagewayDetector(CFG, oriented=True).detect(segs)
    assert (segs["twin_id"] == -1).all()
    DualCarriagewayDetector(CFG, oriented=False).detect(segs)  # orientation unknown: accepted
    assert segs["twin_id"].tolist() == [1, 0]


def test_two_way_streets_are_ignored():
    segs = segments([LineString([(0, 0), (200, 0)]), LineString([(200, 20), (0, 20)])], oneway=False)
    DualCarriagewayDetector(CFG, oriented=True).detect(segs)
    assert (segs["twin_id"] == -1).all()


def test_pseudo_junctions_are_merged_and_curves_kept():
    from street_morphotypes.network.segments import PseudoJunctionMerger
    # A(0) - B(1) - C(2) is one street split at B, where nothing else meets; D(3) branches off C
    lines = [LineString([(0, 0), (50, 10), (100, 0)]), LineString([(100, 0), (200, 0)]),
             LineString([(200, 0), (200, 100)]), LineString([(200, 0), (300, 0)])]
    segs = gpd.GeoDataFrame({
        "u": [0, 1, 2, 2], "v": [1, 2, 3, 4], "oneway": [False] * 4,
        "highway": ["residential", "tertiary", "residential", "residential"],
        "lanes_raw": ["2", "3", None, None], "maxspeed_raw": [None] * 4,
        "name": ["Main St", "Main St", "Side St", "Main St"], "osm_ways": [[1], [2], [3], [4]],
        "user_id": [None] * 4}, geometry=lines)
    out = PseudoJunctionMerger(["tertiary", "residential"]).merge(segs).reset_index(drop=True)
    assert len(out) == 3
    merged = out[out.geometry.length > 150].iloc[0]
    assert {merged["u"], merged["v"]} == {0, 2}
    assert merged["highway"] == "tertiary"
    assert merged["osm_ways"] == [1, 2]
    assert merged.geometry.length > 200  # the curve between A and B is kept, not straightened


def test_merged_user_segments_keep_all_ids():
    from street_morphotypes.network.segments import PseudoJunctionMerger
    lines = [LineString([(0, 0), (50, 0)]), LineString([(50, 0), (100, 0)]), LineString([(100, 0), (100, 50)]),
             LineString([(100, 0), (150, 0)])]
    segs = gpd.GeoDataFrame({
        "u": [0, 1, 2, 2], "v": [1, 2, 3, 4], "oneway": [False] * 4, "highway": ["residential"] * 4,
        "lanes_raw": [None] * 4, "maxspeed_raw": [None] * 4, "name": [None] * 4, "osm_ways": [[]] * 4,
        "user_id": ["a", "b", "c", "d"]}, geometry=lines)
    out = PseudoJunctionMerger(["residential"]).merge(segs)
    assert sorted(map(str, out["user_id"])) == ["['a', 'b']", "c", "d"]
    assert out["u"].dtype == segs["u"].dtype and out["oneway"].dtype == bool
