"""Configuration schema, loading and validation.

A city config (YAML) is deep-merged on top of ``defaults.yaml`` and validated
against the pydantic models below, so typos and wrong types fail early with a
readable message instead of deep inside the pipeline.
"""
from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Literal, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DEFAULTS_PATH = Path(__file__).with_name("defaults.yaml")

# OSM tag filter: key -> True (any value) or a list of accepted values.
TagSpec = dict[str, Union[bool, list[str]]]
BlockName = Literal["transport", "context"]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ── Area ─────────────────────────────────────────────────────────────────────

class PointSpec(_Model):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    radius_m: float = Field(gt=0)


class FileSpec(_Model):
    path: str
    layer: str | None = None


class AreaConfig(_Model):
    name: str
    mode: Literal["place", "point", "polygon"]
    place: str | None = None
    point: PointSpec | None = None
    polygon: FileSpec | None = None
    crs: str = "auto"
    network_buffer_m: float = Field(ge=0)
    context_buffer_m: float = Field(ge=0)

    @field_validator("name")
    @classmethod
    def _slug(cls, v: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_\-]+", v):
            raise ValueError("area.name must be a slug: latin letters, digits, '_' or '-'")
        return v

    @model_validator(mode="after")
    def _mode_has_spec(self) -> "AreaConfig":
        if getattr(self, self.mode) is None:
            raise ValueError(f"area.mode is '{self.mode}' but area.{self.mode} is not set")
        return self


class PathsConfig(_Model):
    cache_dir: str
    output_dir: str
    web_dir: str


class OverpassConfig(_Model):
    urls: list[str] = Field(min_length=1)
    timeout_s: int = Field(gt=0)
    retries: int = Field(ge=1)


# ── Layers ───────────────────────────────────────────────────────────────────

class LayerSource(_Model):
    source: Literal["osm", "file", "none"] = "osm"
    path: str | None = None
    layer: str | None = None
    id_column: str | None = None  # network only: stable segment id for `extra_features` joins

    @model_validator(mode="after")
    def _file_needs_path(self) -> "LayerSource":
        if self.source == "file" and not self.path:
            raise ValueError("a layer with source: file needs `path`")
        return self


class LayersConfig(_Model):
    network: LayerSource
    buildings: LayerSource
    pois: LayerSource
    landuse: LayerSource
    green: LayerSource
    transit_routes: LayerSource
    transit_stops: LayerSource

    @field_validator("network")
    @classmethod
    def _network_required(cls, v: LayerSource) -> LayerSource:
        if v.source == "none":
            raise ValueError("layers.network cannot be 'none'")
        return v


# ── Network & space syntax ───────────────────────────────────────────────────

class DualCarriagewayConfig(_Model):
    detect: bool
    max_distance_m: float = Field(gt=0)
    max_angle_deg: float = Field(gt=0, lt=90)
    min_overlap: float = Field(gt=0, le=1)


class NetworkConfig(_Model):
    highway_types: list[str] = Field(min_length=1)
    exclude_access: list[str]
    unclassified_highway_types: list[str]
    consolidate_tolerance_m: float = Field(ge=0)
    merge_pseudo_junctions: bool
    min_segment_length_m: float = Field(ge=0)
    snap_tolerance_m: float = Field(gt=0)
    dual_carriageway: DualCarriagewayConfig


class SpaceSyntaxConfig(_Model):
    radii: list[Union[int, Literal["n"]]] = Field(min_length=1)
    angle_unit_deg: float = Field(gt=0)
    direction_sample_m: float = Field(gt=0)
    n_jobs: int

    @field_validator("radii")
    @classmethod
    def _radii(cls, v: list) -> list:
        for r in v:
            if r != "n" and r <= 0:
                raise ValueError("space_syntax.radii: metric radii must be positive")
        if len(set(map(str, v))) != len(v):
            raise ValueError("space_syntax.radii contains duplicates")
        return v


# ── Metrics ──────────────────────────────────────────────────────────────────

class CarriagewayConfig(_Model):
    lane_width_m: float = Field(gt=0)


class FrontageConfig(_Model):
    enabled: bool
    buffer_m: float = Field(gt=0)


class PoiDensityConfig(_Model):
    enabled: bool
    buffer_m: float = Field(gt=0)
    assignment: Literal["nearest", "all"]
    tags: TagSpec


class GreenAreaConfig(_Model):
    enabled: bool
    buffer_m: float = Field(gt=0)
    tags: TagSpec


class BuildingAgeConfig(_Model):
    enabled: bool
    buffer_m: float = Field(gt=0)
    osm_tags: list[str]
    min_coverage: float = Field(ge=0, le=1)
    min_year: int
    reference_year: int


class LandUseConfig(_Model):
    enabled: bool
    buffer_m: float = Field(gt=0)
    floor_height_m: float = Field(gt=0)
    min_level_samples: int = Field(ge=1)
    default_levels: dict[str, float]
    mixed_use_ground_floor: bool
    max_unknown_share: float = Field(ge=0, le=1)
    categories: list[str]
    building_tags: dict[str, list[str]]
    poi_tags: dict[str, TagSpec]
    landuse_tags: dict[str, TagSpec]

    @model_validator(mode="after")
    def _known_categories(self) -> "LandUseConfig":
        if "_default" not in self.default_levels:
            raise ValueError("metrics.land_use.default_levels must contain `_default`")
        for section in ("building_tags", "poi_tags", "landuse_tags"):
            unknown = set(getattr(self, section)) - set(self.categories)
            if unknown:
                raise ValueError(f"metrics.land_use.{section}: unknown categories {sorted(unknown)}")
        return self


class LanesConfig(_Model):
    enabled: bool
    defaults_by_highway: dict[str, float]


class MaxspeedConfig(_Model):
    enabled: bool
    defaults_by_highway: dict[str, float]
    zone_values: dict[str, float]


class TransitConfig(_Model):
    enabled: bool
    route_types: list[str]
    dedupe_by: Literal["ref", "id"]
    stop_tags: TagSpec
    stop_merge_distance_m: float = Field(ge=0)
    stops_buffer_m: float = Field(gt=0)
    geometric_match_m: float = Field(gt=0)


class MetricsConfig(_Model):
    carriageway: CarriagewayConfig
    frontage: FrontageConfig
    poi_density: PoiDensityConfig
    green_area: GreenAreaConfig
    building_age: BuildingAgeConfig
    land_use: LandUseConfig
    lanes: LanesConfig
    maxspeed: MaxspeedConfig
    transit: TransitConfig


class ExtraFeatureConfig(_Model):
    path: str
    layer: str | None = None
    columns: dict[str, Literal["transport", "context", "none"]] = Field(min_length=1)
    join: Literal["spatial", "id"] = "spatial"
    id_column: str | None = None
    max_distance_m: float = Field(default=15, gt=0)

    @model_validator(mode="after")
    def _id_join(self) -> "ExtraFeatureConfig":
        if self.join == "id" and not self.id_column:
            raise ValueError("extra_features: join: id needs `id_column`")
        return self


# ── Clustering & output ──────────────────────────────────────────────────────

class BlockConfig(_Model):
    features: list[str] = Field(min_length=1)
    k: Union[int, Literal["auto"]]
    order_by: str

    @field_validator("k")
    @classmethod
    def _k(cls, v):
        if v != "auto" and v < 2:
            raise ValueError("k must be >= 2 or 'auto'")
        return v


class ClusteringConfig(_Model):
    transport: BlockConfig
    context: BlockConfig
    k_range: tuple[int, int]
    min_cluster_frac: float = Field(ge=0, lt=0.5)
    skew_threshold: float
    max_mode_share: float = Field(gt=0, le=1)
    clip_scaled: float = Field(gt=0)
    kmeans_n_init: int = Field(ge=1)
    gmm_covariance_type: Literal["full", "tied", "diag", "spherical"]
    random_state: int
    min_silhouette: float
    min_confidence: float = Field(ge=0, le=1)
    silhouette_sample_size: int = Field(ge=100)
    correlation_warning: float = Field(gt=0, le=1)

    @field_validator("k_range")
    @classmethod
    def _k_range(cls, v):
        if v[0] < 2 or v[1] < v[0]:
            raise ValueError("clustering.k_range must be [min, max] with 2 <= min <= max")
        return v

    def block(self, name: BlockName) -> BlockConfig:
        return getattr(self, name)


class NamesConfig(_Model):
    transport: dict[int, str]
    context: dict[int, str]
    morphotype: dict[str, str]

    @field_validator("transport", "context", "morphotype", mode="before")
    @classmethod
    def _null_is_empty(cls, v):
        # `null` clears names inherited through `extends` (a mapping would merge key by key)
        return {} if v is None else v


class OutputConfig(_Model):
    excel: bool
    gpkg: bool
    figures: bool
    web: bool


# ── Roots ────────────────────────────────────────────────────────────────────

class CityConfig(_Model):
    """Configuration of one city (study area) run."""

    area: AreaConfig
    paths: PathsConfig
    overpass: OverpassConfig
    layers: LayersConfig
    network: NetworkConfig
    space_syntax: SpaceSyntaxConfig
    metrics: MetricsConfig
    extra_features: list[ExtraFeatureConfig]
    clustering: ClusteringConfig
    names: NamesConfig
    output: OutputConfig

    @property
    def cache_dir(self) -> Path:
        return Path(self.paths.cache_dir) / self.area.name

    @property
    def output_dir(self) -> Path:
        return Path(self.paths.output_dir) / self.area.name

    def to_yaml(self) -> str:
        return yaml.safe_dump(self.model_dump(mode="json"), sort_keys=False, allow_unicode=True)


class PooledConfig(_Model):
    """Several cities clustered together into one shared typology."""

    name: str
    cities: list[str] = Field(min_length=1)  # paths to city configs
    paths: PathsConfig
    clustering: ClusteringConfig
    names: NamesConfig
    output: OutputConfig

    @property
    def output_dir(self) -> Path:
        return Path(self.paths.output_dir) / self.name

    def to_yaml(self) -> str:
        return yaml.safe_dump(self.model_dump(mode="json"), sort_keys=False, allow_unicode=True)


# ── Loading ──────────────────────────────────────────────────────────────────

def deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge ``override`` into a copy of ``base``.

    Mappings are merged key by key; lists and scalars are replaced.
    """
    out = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def _read_yaml(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: the top level of a config must be a mapping")
    return data


def load_defaults() -> dict:
    return _read_yaml(DEFAULTS_PATH)


def _read_with_extends(path: str | Path, seen: tuple[Path, ...] = ()) -> dict:
    """Read a config; ``extends: other.yaml`` (relative to this file) is merged underneath."""
    path = Path(path).resolve()
    if path in seen:
        raise ValueError(f"Circular `extends` in {path}")
    data = _read_yaml(path)
    parent = data.pop("extends", None)
    if parent is None:
        return data
    return deep_merge(_read_with_extends(path.parent / parent, seen + (path,)), data)


def load_config(path: str | Path) -> CityConfig | PooledConfig:
    """Load a city or pooled config file, merged on top of the defaults.

    A config may start with ``extends: <file>`` to override only a few settings
    of another config (e.g. an experiment with a different k).
    """
    user = _read_with_extends(path)
    defaults = load_defaults()
    if user.get("mode") == "pooled":
        user = {k: v for k, v in user.items() if k != "mode"}
        base = {k: defaults[k] for k in ("paths", "clustering", "names", "output")}
        return PooledConfig.model_validate(deep_merge(base, user))
    return CityConfig.model_validate(deep_merge(defaults, user))


def load_city_config(path: str | Path) -> CityConfig:
    cfg = load_config(path)
    if not isinstance(cfg, CityConfig):
        raise ValueError(f"{path} is a pooled config, a city config was expected")
    return cfg
