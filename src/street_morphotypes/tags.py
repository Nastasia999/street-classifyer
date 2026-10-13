"""OSM tag filtering, categorisation and value parsing."""
from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping

import numpy as np
import pandas as pd

from .config import TagSpec

_NEGATIVE_VALUES = {"no", "none", "false", "0"}
_MPH_TO_KMH = 1.609344


def _first_value(series: pd.Series) -> pd.Series:
    """First value of OSM multi-values ("a;b" -> "a"), stripped, as string."""
    return series.astype("string").str.split(";").str[0].str.strip()


def merge_tag_specs(*specs: Mapping[str, bool | list[str]]) -> dict[str, bool | list[str]]:
    """Union of several tag filters (``True`` wins over value lists)."""
    out: dict[str, bool | list[str]] = {}
    for spec in specs:
        for key, val in spec.items():
            prev = out.get(key)
            if prev is True or val is True:
                out[key] = True
            else:
                out[key] = sorted(set(prev or []) | set(val))
    return out


class TagMatcher:
    """Boolean mask of features that match a tag filter ``{key: True | [values]}``."""

    def __init__(self, spec: TagSpec) -> None:
        self.spec = dict(spec)

    @property
    def keys(self) -> list[str]:
        return list(self.spec)

    def explicit_mask(self, df: pd.DataFrame) -> pd.Series:
        return self._mask(df, wildcard=False)

    def wildcard_mask(self, df: pd.DataFrame) -> pd.Series:
        return self._mask(df, wildcard=True)

    def mask(self, df: pd.DataFrame) -> pd.Series:
        return self.explicit_mask(df) | self.wildcard_mask(df)

    def _mask(self, df: pd.DataFrame, wildcard: bool) -> pd.Series:
        out = pd.Series(False, index=df.index)
        for key, val in self.spec.items():
            if key not in df.columns or (val is True) != wildcard:
                continue
            values = _first_value(df[key])
            if val is True:
                out |= values.notna() & ~values.str.lower().isin(_NEGATIVE_VALUES)
            else:
                out |= values.isin(val).fillna(False)
        return out.astype(bool)


class TagClassifier:
    """Assigns one category per feature from ``{category: tag filter}``.

    Explicit value matches take precedence over wildcard (``True``) matches;
    within the same precedence the first category in mapping order wins.
    """

    def __init__(self, categories: Mapping[str, TagSpec]) -> None:
        self.matchers = {cat: TagMatcher(spec) for cat, spec in categories.items()}

    @property
    def keys(self) -> list[str]:
        return sorted({k for m in self.matchers.values() for k in m.keys})

    def classify(self, df: pd.DataFrame) -> pd.Series:
        result = pd.Series(pd.NA, index=df.index, dtype="object")
        for use_wildcard in (False, True):
            for cat, matcher in self.matchers.items():
                hit = matcher.wildcard_mask(df) if use_wildcard else matcher.explicit_mask(df)
                result[hit & result.isna()] = cat
        return result


class ValueMapClassifier:
    """Assigns a category from the value of a single key, e.g. ``building``."""

    def __init__(self, key: str, categories: Mapping[str, Iterable[str]]) -> None:
        self.key = key
        self.lookup = {v: cat for cat, values in categories.items() for v in values}

    def classify(self, df: pd.DataFrame) -> pd.Series:
        if self.key not in df.columns:
            return pd.Series(pd.NA, index=df.index, dtype="object")
        return _first_value(df[self.key]).map(self.lookup).astype("object")


# ── Value parsing ────────────────────────────────────────────────────────────

def as_list(value) -> list:
    """OSMnx stores attributes of merged ways as lists; normalise to a list."""
    if isinstance(value, (list, tuple, set, np.ndarray)):
        return [v for v in value if not _is_missing(v)]
    return [] if _is_missing(value) else [value]


def _is_missing(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return value is pd.NA


_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


def parse_number(value) -> float:
    """Largest number in an OSM value or list of values ("2;3" -> 3, ["2", "4"] -> 4)."""
    nums = [
        float(m.replace(",", "."))
        for v in as_list(value)
        for m in _NUMBER.findall(str(v))
    ]
    return max(nums) if nums else np.nan


def parse_maxspeed(value, zone_values: Mapping[str, float]) -> float:
    """Maxspeed in km/h; handles mph, zone codes (``RU:urban``) and lists."""
    speeds = []
    for v in as_list(value):
        for part in str(v).split(";"):
            part = part.strip()
            if part in zone_values:
                speeds.append(float(zone_values[part]))
                continue
            m = _NUMBER.search(part)
            if m:
                speed = float(m.group().replace(",", "."))
                speeds.append(speed * _MPH_TO_KMH if "mph" in part.lower() else speed)
    return max(speeds) if speeds else np.nan


_YEAR = re.compile(r"(?<!\d)(\d{4})(?!\d)")
_CENTURY = re.compile(r"\bC(\d{2})\b")


def parse_year(value, min_year: int, max_year: int) -> float:
    """Construction year from OSM date strings ("1965", "1960s", "~1900", "1965-03", "C19")."""
    if _is_missing(value):
        return np.nan
    text = str(value)
    years = [int(y) for y in _YEAR.findall(text) if min_year <= int(y) <= max_year]
    if years:
        return float(years[0])
    m = _CENTURY.search(text)
    if m:  # "C19" -> middle of the 19th century
        year = (int(m.group(1)) - 1) * 100 + 50
        return float(year) if min_year <= year <= max_year else np.nan
    return np.nan


def resolve_highway(value, ranking: list[str]) -> str | None:
    """Most important highway class among merged ways (by ``ranking`` order)."""
    values = [str(v) for v in as_list(value)]
    ranked = [v for v in ranking if v in values]
    if ranked:
        return ranked[0]
    return values[0] if values else None


def parse_bool(value) -> bool:
    vals = as_list(value)
    return any(str(v).lower() in {"true", "yes", "1", "-1"} for v in vals) or any(v is True for v in vals)
