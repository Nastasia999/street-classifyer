"""Human-readable feature labels for tables, figures and generated cluster names."""
from __future__ import annotations

import re

FEATURE_LABELS: dict[str, tuple[str, str]] = {
    # column: (long label, short label)
    "lanes": ("Lanes across the street", "lanes"),
    "maxspeed": ("Speed limit, km/h", "speed limit"),
    "pt_routes": ("Public transport routes", "PT routes"),
    "pt_stops_per_100m": ("PT stops per 100 m", "PT stops"),
    "frontage": ("Street-wall continuity (share of length)", "frontage"),
    "poi_per_100m": ("Organisations per 100 m", "organisations"),
    "green_m2_per_100m": ("Green area, m2 per 100 m", "greenery"),
    "building_age_median": ("Median building age, years", "building age"),
    "fn_residential": ("Residential floor-area share", "residential"),
    "fn_commercial": ("Commercial floor-area share", "commercial"),
    "fn_social": ("Social floor-area share", "social"),
    "fn_industrial": ("Industrial floor-area share", "industrial"),
    "fn_other": ("Other-use floor-area share", "other use"),
}

_SS = {
    "nain": ("NAIN (normalised angular integration)", "integration"),
    "nach": ("NACH (normalised angular choice)", "through-movement"),
    "choice": ("Angular choice", "choice"),
    "nc": ("Node count", "node count"),
    "td": ("Total angular depth", "depth"),
    "mean_depth": ("Mean angular depth", "mean depth"),
}
_SS_RE = re.compile(r"ss_(nain|nach|choice|nc|td|mean_depth)_(\w+)")


def label(feature: str, short: bool = False) -> str:
    if feature in FEATURE_LABELS:
        return FEATURE_LABELS[feature][int(short)]
    m = _SS_RE.fullmatch(feature)
    if m:
        long_, short_ = _SS[m.group(1)]
        radius = "Rn" if m.group(2) == "n" else f"R{m.group(2)} m"
        return f"{short_} {radius}" if short else f"{long_}, {radius}"
    return feature
