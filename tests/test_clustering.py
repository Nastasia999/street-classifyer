import numpy as np
import pandas as pd

from street_morphotypes.clustering import FeatureScaler, MorphotypeClassifier, MorphotypeModel
from street_morphotypes.config import ClusteringConfig, NamesConfig, load_defaults


def clustering_cfg(**overrides) -> ClusteringConfig:
    raw = load_defaults()["clustering"]
    raw["transport"] = {"features": ["t1", "t2"], "k": "auto", "order_by": "t1"}
    raw["context"] = {"features": ["c1", "c2"], "k": 2, "order_by": "c1"}
    raw.update(overrides)
    return ClusteringConfig.model_validate(raw)


def synthetic(n_per=80, seed=0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    blocks = []
    for t_centre in (0, 5, 10):
        blocks.append(pd.DataFrame({"t1": rng.normal(t_centre, 1, n_per), "t2": rng.normal(t_centre, 1, n_per)}))
    df = pd.concat(blocks, ignore_index=True)
    c = rng.integers(0, 2, len(df))
    df["c1"] = rng.normal(c * 8, 1)
    df["c2"] = rng.normal(c * 8, 1)
    df["context_null"] = False
    df.loc[:4, "context_null"] = True
    return df


def test_scaler_drops_constant_and_uses_std_when_iqr_zero():
    df = pd.DataFrame({"const": [1.0] * 20, "sparse": [0] * 16 + [5.0] * 4, "x": np.arange(20.0)})
    sc = FeatureScaler(skew_threshold=100, max_mode_share=0.95, clip_scaled=5).fit(df, ["const", "sparse", "x"])
    assert list(sc.dropped) == ["const"]
    Z = sc.transform(df)
    assert Z.shape == (20, 2)
    assert np.isfinite(Z).all()


def test_scaler_drops_near_constant_and_clips():
    df = pd.DataFrame({"rare": [0.0] * 99 + [1.0], "x": np.r_[np.arange(99.0), 1e6]})
    sc = FeatureScaler(skew_threshold=100, max_mode_share=0.95, clip_scaled=5).fit(df, ["rare", "x"])
    assert "rare" in sc.dropped
    assert sc.transform(df).max() == 5


def test_blocks_are_clustered_independently_and_ordered():
    df = synthetic()
    clf = MorphotypeClassifier(clustering_cfg(), NamesConfig(transport={}, context={}, morphotype={}))
    model, res = clf.fit(df, {}, ["test"])
    assert model.transport.k == 3                         # auto-k recovers the 3 groups
    t = res.table["T_cluster"]
    means = df.groupby(t)["t1"].mean()
    assert means.is_monotonic_increasing                  # ordered by order_by
    assert (res.table.loc[:4, "C_cluster"] == -1).all()   # context_null -> C_null
    assert res.table.loc[:4, "morphotype"].str.endswith("C_null").all()
    assert res.table["T_confidence"].between(0, 1).all()


def test_model_roundtrip_reproduces_labels(tmp_path):
    df = synthetic()
    clf = MorphotypeClassifier(clustering_cfg(), NamesConfig(transport={0: "Quiet"}, context={}, morphotype={}))
    model, res = clf.fit(df, {}, ["test"])
    model.save(tmp_path / "m.joblib")
    again = clf.apply(MorphotypeModel.load(tmp_path / "m.joblib"), df)
    pd.testing.assert_series_equal(again.table["morphotype"], res.table["morphotype"])
    assert res.table.loc[res.table["T_cluster"] == 0, "T_name"].iloc[0] == "T0 · Quiet"


def test_generated_names_are_unique():
    from street_morphotypes.clustering.naming import ClusterNamer
    cen = pd.DataFrame({"poi_per_100m": [0.0, 2.0, 1.8], "fn_commercial": [0.0, 1.5, 1.9],
                        "frontage": [0.0, 1.0, -1.0]})
    names = ClusterNamer(NamesConfig(transport={}, context={}, morphotype={})).cluster_names("context", cen)
    assert len(set(names.values())) == 3
    assert "frontage" in names[1] and "frontage" in names[2]


def test_pooled_drops_features_missing_in_one_city():
    import geopandas as gpd
    from shapely.geometry import Point
    from street_morphotypes.features import CityFeatures
    from street_morphotypes.pipeline import _pool

    def city(name, with_c2):
        df = synthetic(20).assign(classify=True)
        if not with_c2:
            df = df.drop(columns="c2")
        gdf = gpd.GeoDataFrame(df, geometry=[Point(i, 0) for i in range(len(df))])
        gdf.index.name = "seg_id"
        return CityFeatures(name, gdf)

    pooled, _ = _pool([city("a", True), city("b", False)], clustering_cfg())
    assert "c2" not in pooled.columns
    assert "c1" in pooled.columns
