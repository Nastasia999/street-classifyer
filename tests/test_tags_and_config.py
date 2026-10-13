import numpy as np
import pandas as pd
import pytest
import yaml

from street_morphotypes.config import deep_merge, load_config
from street_morphotypes.tags import (TagClassifier, TagMatcher, merge_tag_specs, parse_maxspeed,
                                     parse_number, parse_year, resolve_highway)


def test_parse_number():
    assert parse_number("2") == 2
    assert parse_number("2;3") == 3
    assert parse_number(["2", "4"]) == 4
    assert np.isnan(parse_number(None))


def test_parse_maxspeed():
    zones = {"RU:urban": 60}
    assert parse_maxspeed("50", zones) == 50
    assert parse_maxspeed("30 mph", zones) == pytest.approx(48.28, abs=0.01)
    assert parse_maxspeed("RU:urban", zones) == 60
    assert np.isnan(parse_maxspeed("signals", zones))


@pytest.mark.parametrize("raw,year", [("1965", 1965), ("1965-03-12", 1965), ("~1900", 1900),
                                      ("1960s", 1960), ("C19", 1850), ("unknown", None)])
def test_parse_year(raw, year):
    got = parse_year(raw, 1000, 2026)
    assert (np.isnan(got) if year is None else got == year)


def test_resolve_highway_prefers_ranking():
    assert resolve_highway(["residential", "primary"], ["primary", "residential"]) == "primary"


def test_tag_classifier_explicit_beats_wildcard():
    df = pd.DataFrame({"office": ["government", "company", None], "amenity": [None, None, "school"]})
    clf = TagClassifier({
        "commercial": {"office": True},
        "social": {"office": ["government"], "amenity": ["school"]},
    })
    assert clf.classify(df).tolist() == ["social", "commercial", "social"]


def test_tag_matcher_ignores_no():
    df = pd.DataFrame({"shop": ["bakery", "no", None]})
    assert TagMatcher({"shop": True}).mask(df).tolist() == [True, False, False]


def test_merge_tag_specs():
    assert merge_tag_specs({"a": ["x"]}, {"a": ["y"], "b": True}, {"b": ["z"]}) == {"a": ["x", "y"], "b": True}


def test_deep_merge_replaces_lists_and_merges_dicts():
    base = {"a": {"x": 1, "y": [1, 2]}, "b": 1}
    out = deep_merge(base, {"a": {"y": [3]}})
    assert out == {"a": {"x": 1, "y": [3]}, "b": 1}
    assert base["a"]["y"] == [1, 2]


def test_city_config_loads_with_defaults(tmp_path):
    path = tmp_path / "c.yaml"
    path.write_text(yaml.safe_dump({"area": {"name": "t", "mode": "point",
                                             "point": {"lat": 52.0, "lon": 104.0, "radius_m": 500}}}))
    cfg = load_config(path)
    assert cfg.area.name == "t"
    assert cfg.space_syntax.radii == ["n", 800, 2000]


def test_config_rejects_unknown_keys(tmp_path):
    path = tmp_path / "c.yaml"
    path.write_text(yaml.safe_dump({"area": {"name": "t", "mode": "place", "place": "X"},
                                    "metrics": {"frontage": {"bufer_m": 10}}}))
    with pytest.raises(Exception, match="bufer_m"):
        load_config(path)


def test_extends_overrides_parent(tmp_path):
    (tmp_path / "base.yaml").write_text(yaml.safe_dump({
        "area": {"name": "t", "mode": "place", "place": "X"},
        "clustering": {"context": {"k": 2}}}))
    (tmp_path / "exp.yaml").write_text(yaml.safe_dump({
        "extends": "base.yaml", "clustering": {"context": {"k": 4}}, "paths": {"output_dir": "out/exp"}}))
    cfg = load_config(tmp_path / "exp.yaml")
    assert cfg.area.name == "t"
    assert cfg.clustering.context.k == 4
    assert cfg.paths.output_dir == "out/exp"
    assert cfg.clustering.context.order_by == "poi_per_100m"  # defaults still apply


def test_cache_fingerprint_detects_changed_settings(tmp_path):
    from street_morphotypes.data.layers import LayerRepository
    path = tmp_path / "pois.gpkg"
    assert not LayerRepository._cache_is_current(path, {"extent": [0, 0, 1, 1]})  # nothing cached yet
    path.write_text("data")
    assert LayerRepository._cache_is_current(path, {"extent": [0, 0, 1, 1]})      # same settings
    assert not LayerRepository._cache_is_current(path, {"extent": [0, 0, 2, 2]})  # extent changed
    assert not path.exists()                                                        # stale file removed
    legacy = tmp_path / "green.gpkg"
    legacy.write_text("data")                                                       # cache without fingerprint
    assert LayerRepository._cache_is_current(legacy, {"extent": [0, 0, 1, 1]})


def test_reference_year_is_fixed_in_config(tmp_path):
    path = tmp_path / "c.yaml"
    path.write_text(yaml.safe_dump({"area": {"name": "t", "mode": "place", "place": "X"}}))
    assert load_config(path).metrics.building_age.reference_year == 2026


def test_null_names_clear_inherited_ones(tmp_path):
    (tmp_path / "base.yaml").write_text(yaml.safe_dump({
        "area": {"name": "x", "mode": "place", "place": "X"},
        "names": {"transport": {0: "Local street"}, "context": {0: "Green street"}}}))
    (tmp_path / "exp.yaml").write_text(yaml.safe_dump({"extends": "base.yaml", "names": {"context": None}}))
    cfg = load_config(tmp_path / "exp.yaml")
    assert cfg.names.transport == {0: "Local street"}
    assert cfg.names.context == {}
