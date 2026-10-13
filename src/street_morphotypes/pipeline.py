"""Run modes: one city (local), several cities in one typology (pooled), a saved model (apply)."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from .area import StudyArea
from .clustering import BLOCKS, ClassificationResult, MorphotypeClassifier, MorphotypeModel
from .clustering.naming import ClusterNamer
from .config import CityConfig, NamesConfig, PooledConfig, load_city_config
from .features import CityFeatures, FeatureBuilder
from .io.export import attach_labels, write_excel, write_gpkg, write_json
from .io.web import area_label, export_web

log = logging.getLogger(__name__)

MODEL_FILE = "model.joblib"


def classification_frame(features: CityFeatures) -> pd.DataFrame:
    """Rows that take part in clustering, with ``city`` and ``seg_id`` columns."""
    segs = features.segments
    df = pd.DataFrame(segs[segs["classify"].astype(bool)].drop(columns="geometry")).reset_index()
    df.insert(0, "city", features.city)
    return df


class CityPipeline:
    """Everything for one city config: fetch, features, scan, local run, apply."""

    def __init__(self, cfg: CityConfig) -> None:
        self.cfg = cfg
        self.out_dir = cfg.output_dir

    def fetch(self) -> None:
        FeatureBuilder(self.cfg).fetch()

    def features(self, recompute: bool = False) -> CityFeatures:
        if not recompute and CityFeatures.exists(self.out_dir):
            log.info("%s: using saved features (%s); pass --recompute to rebuild", self.cfg.area.name,
                     self.out_dir)
            return CityFeatures.load(self.out_dir)
        features = FeatureBuilder(self.cfg).build()
        features.save(self.out_dir)
        return features

    def scan(self, recompute: bool = False) -> dict[str, pd.DataFrame]:
        features = self.features(recompute)
        return report_scan(self.cfg.clustering, self.cfg.names, classification_frame(features),
                           features.extra_blocks)

    def run(self, recompute: bool = False) -> ClassificationResult:
        features = self.features(recompute)
        df = classification_frame(features)
        clf = MorphotypeClassifier(self.cfg.clustering, self.cfg.names)
        model, result = clf.fit(df, features.extra_blocks, trained_on=[self.cfg.area.name])
        model.save(self.out_dir / MODEL_FILE)
        corr = clf.correlations(df, [f for b in BLOCKS for f in model.block(b).features])
        export_results(self.out_dir, self.cfg.output, df, result, model, [features],
                       {features.city: self.cfg}, self.cfg.to_yaml(), corr)
        update_web(self.cfg.paths, self.cfg.output)
        return result

    def apply(self, model_path: Path, recompute: bool = False) -> ClassificationResult:
        model = MorphotypeModel.load(model_path)
        log.info("Applying model trained on %s", model.trained_on)
        features = self.features(recompute)
        df = classification_frame(features)
        clf = MorphotypeClassifier(self.cfg.clustering, self.cfg.names)
        result = clf.apply(model, df)
        out_dir = self.out_dir / f"applied_{model_path.parent.name}"
        export_results(out_dir, self.cfg.output, df, result, model, [features],
                       {features.city: self.cfg}, self.cfg.to_yaml())
        return result


class PooledPipeline:
    """Several cities clustered together: one shared typology, a model for new cities."""

    def __init__(self, cfg: PooledConfig) -> None:
        self.cfg = cfg
        self.city_cfgs = [load_city_config(p) for p in cfg.cities]
        names = [c.area.name for c in self.city_cfgs]
        if len(set(names)) != len(names):
            raise ValueError(f"Pooled cities must have distinct area.name values: {names}")

    def _features(self, recompute: bool) -> list[CityFeatures]:
        return [CityPipeline(c).features(recompute) for c in self.city_cfgs]

    def scan(self, recompute: bool = False) -> dict[str, pd.DataFrame]:
        feats = self._features(recompute)
        df, extra = _pool(feats, self.cfg.clustering)
        return report_scan(self.cfg.clustering, self.cfg.names, df, extra)

    def run(self, recompute: bool = False) -> ClassificationResult:
        feats = self._features(recompute)
        df, extra = _pool(feats, self.cfg.clustering)
        clf = MorphotypeClassifier(self.cfg.clustering, self.cfg.names)
        model, result = clf.fit(df, extra, trained_on=[f.city for f in feats])
        model.save(self.cfg.output_dir / MODEL_FILE)
        corr = clf.correlations(df, [f for b in BLOCKS for f in model.block(b).features])
        export_results(self.cfg.output_dir, self.cfg.output, df, result, model, feats,
                       {c.area.name: c for c in self.city_cfgs}, self.cfg.to_yaml(), corr)
        update_web(self.cfg.paths, self.cfg.output)
        return result


def _pool(feats: list[CityFeatures], ccfg) -> tuple[pd.DataFrame, dict[str, str]]:
    """Concatenate the cities' tables, keeping only features that every city has.

    A feature missing in one city (metric disabled, dropped for low coverage,
    layer set to ``none``) would be filled with the other cities' median for all
    of that city's segments and split the clusters by city instead of by form.
    """
    extra: dict[str, str] = {}
    for f in feats:
        for col, block in f.extra_blocks.items():
            if extra.setdefault(col, block) != block:
                raise ValueError(f"extra feature '{col}' is assigned to different blocks in different cities")
    frames = [classification_frame(f) for f in feats]
    wanted = set(extra) | {c for b in BLOCKS for c in ccfg.block(b).features}
    for col in sorted(wanted):
        lacking = [f.city for f, fr in zip(feats, frames) if col not in fr or fr[col].notna().sum() == 0]
        if lacking and len(lacking) < len(feats):
            log.warning("Feature '%s' is dropped from the pooled typology: no values in %s", col, lacking)
            frames = [fr.drop(columns=col, errors="ignore") for fr in frames]
    df = pd.concat(frames, ignore_index=True)
    return df, {c: b for c, b in extra.items() if c in df.columns}


def update_web(paths, ocfg) -> None:
    """Rebuild the web map data from every run in the output folder (``output.web``)."""
    if ocfg.web:
        export_web(Path(paths.output_dir), Path(paths.web_dir))


def report_scan(ccfg, names, df: pd.DataFrame, extra_blocks: dict[str, str]) -> dict[str, pd.DataFrame]:
    clf = MorphotypeClassifier(ccfg, names)
    scans = clf.scan(df, extra_blocks)
    feats = clf.resolve_features(df, extra_blocks)
    for block in BLOCKS:
        print(f"\n== {block.upper()} ({len(feats[block])} features: {', '.join(feats[block])}) ==")
        print(scans[block].to_string(index=False))
    corr = clf.correlations(df, feats["transport"] + feats["context"])
    if not corr.empty:
        print(f"\nHighly correlated feature pairs (|r| >= {ccfg.correlation_warning}):")
        print(corr.to_string(index=False))
    return scans


def export_results(out_dir: Path, ocfg, df: pd.DataFrame, result: ClassificationResult,
                   model: MorphotypeModel, feats: list[CityFeatures], city_cfgs: dict[str, CityConfig],
                   config_yaml: str, corr: pd.DataFrame | None = None) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    table = pd.concat([df[["city", "seg_id"]], result.table], axis=1)
    quality = {f.city: f.quality for f in feats}
    labelled = {}
    for f in feats:
        labelled[f.city] = attach_labels(f.segments, table[table["city"] == f.city].drop(columns="city"))
        if ocfg.gpkg:
            area = f.area if f.area is not None else StudyArea.from_config(city_cfgs[f.city].area).as_gdf()
            name = "morphotypes.gpkg" if len(feats) == 1 else f"morphotypes_{f.city}.gpkg"
            write_gpkg(out_dir / name, labelled[f.city], area)
    if ocfg.excel:
        write_excel(out_dir / "morphotypes.xlsx", df, result, model, quality, config_yaml, corr)
    write_json(out_dir / "summary.json", {
        "trained_on": model.trained_on,
        "cities": [f.city for f in feats],
        "k": {b: model.block(b).k for b in BLOCKS},
        "features": {b: model.block(b).features for b in BLOCKS},
        "mean_silhouette": {b: round(result.blocks[b].sil_mean, 4) for b in BLOCKS},
        "cluster_names": model.names,
        "order_by": {b: model.block(b).order_by for b in BLOCKS},
        "cluster_profiles": {b: ClusterNamer(NamesConfig(transport={}, context={}, morphotype={}))
                             .descriptions(b, model.block(b).centroids) for b in BLOCKS},
        "morphotype_counts": result.table["morphotype"].value_counts().sort_index().to_dict(),
        "borderline_share": round(float(result.table["borderline"].mean()), 4),
        "data_quality": quality,
        "area_labels": {city: area_label(c.area) for city, c in city_cfgs.items()},
        "web": ocfg.web,
    })
    if ocfg.figures:
        from .viz.figures import FigureMaker
        FigureMaker(out_dir / "figures").make_all(df, result, model, labelled)
