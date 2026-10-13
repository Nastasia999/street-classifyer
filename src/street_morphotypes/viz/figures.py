"""Static figures (PNG) for reports: cluster diagnostics, profiles and maps.

Colour roles follow one rule each: ordered clusters (T and C are numbered by
an ordering feature) use one-hue ordinal ramps, centroid profiles use a
diverging blue-gray-red map, magnitudes use a sequential blue ramp, and
morphotypes are shown as small multiples (one highlighted panel each) instead
of a many-hue categorical map.
"""
from __future__ import annotations

import logging
import math
import textwrap
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from ..clustering import BLOCKS, ClassificationResult, MorphotypeModel  # noqa: E402
from ..labels import label  # noqa: E402

log = logging.getLogger(__name__)

# ── Palette (reference data-viz palette, light mode) ─────────────────────────
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
CONTEXT_NET = "#d9d8d1"           # background network on maps
BLUE_ORDINAL = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281", "#0d366b"]
ORANGE_ORDINAL = ["#f6c2a8", "#f2996f", "#eb6834", "#c4501f", "#933a12", "#6b2a0c"]
NULL_COLOR = "#b5b4ad"
ACCENT = "#2a78d6"
SEQ_BLUE = LinearSegmentedColormap.from_list(
    "seq_blue", ["#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#184f95", "#0d366b"])
DIVERGING = LinearSegmentedColormap.from_list("blue_gray_red", ["#184f95", "#6da7ec", "#f0efec",
                                                                 "#ec8a89", "#b8302f"])

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"], "font.size": 9,
    "text.color": INK, "axes.labelcolor": INK_2, "axes.edgecolor": AXIS,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.titlesize": 11, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "axes.grid": False, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False, "axes.axisbelow": True,
})


def _ordinal(ramp: list[str], k: int) -> list[str]:
    """k evenly spaced steps of a ramp (light -> dark = low -> high)."""
    if k <= len(ramp):
        idx = np.round(np.linspace(0, len(ramp) - 1, k)).astype(int)
        return [ramp[i] for i in idx]
    return [matplotlib.colors.to_hex(c) for c in
            LinearSegmentedColormap.from_list("r", ramp)(np.linspace(0, 1, k))]


class FigureMaker:
    def __init__(self, out_dir: Path) -> None:
        self.out_dir = out_dir
        out_dir.mkdir(parents=True, exist_ok=True)

    def make_all(self, df: pd.DataFrame, result: ClassificationResult, model: MorphotypeModel,
                 labelled: dict[str, gpd.GeoDataFrame]) -> None:
        steps = [
            ("k_scan", lambda: self.k_scan(result)),
            ("silhouette", lambda: self.silhouette(result, model)),
            ("profiles", lambda: self.profiles(model)),
            ("matrix", lambda: self.morphotype_matrix(result, model)),
        ]
        for city, gdf in labelled.items():
            steps += [
                (f"map_clusters_{city}", lambda c=city, g=gdf: self.cluster_maps(c, g, model)),
                (f"map_morphotypes_{city}", lambda c=city, g=gdf: self.morphotype_multiples(c, g, model)),
                (f"map_space_syntax_{city}", lambda c=city, g=gdf: self.space_syntax_maps(c, g)),
                (f"map_borderline_{city}", lambda c=city, g=gdf: self.borderline_map(c, g)),
            ]
        if df["city"].nunique() > 1:
            steps.append(("city_composition", lambda: self.city_composition(df, result)))
        for name, fn in steps:
            try:
                fn()
            except Exception as exc:  # a failed figure must not lose the computed results
                log.warning("Figure %s failed: %s: %s", name, type(exc).__name__, exc)
        log.info("Figures saved to %s", self.out_dir)

    def _save(self, fig, name: str) -> None:
        path = self.out_dir / f"{name}.png"
        try:
            fig.savefig(path, dpi=200, bbox_inches="tight")
        except OSError:  # Windows: the file may be locked by an image viewer
            path = path.with_name(f"{name}_new.png")
            log.warning("Could not overwrite the figure (open elsewhere?), saved as %s", path.name)
            fig.savefig(path, dpi=200, bbox_inches="tight")
        finally:
            plt.close(fig)

    # ── Diagnostics ──────────────────────────────────────────────────────────

    def k_scan(self, result: ClassificationResult) -> None:
        if not result.scans:
            return
        fig, axes = plt.subplots(1, len(result.scans), figsize=(4.2 * len(result.scans), 3), squeeze=False)
        for ax, (block, scan) in zip(axes[0], result.scans.items()):
            ok = scan["min_cluster_ok"].to_numpy()
            ax.plot(scan["k"], scan["silhouette"], color=ACCENT, lw=2, solid_capstyle="round", zorder=2)
            ax.scatter(scan["k"][ok], scan["silhouette"][ok], s=40, color=ACCENT, edgecolor=SURFACE,
                       linewidth=2, zorder=3, label="all clusters ≥ min size")
            ax.scatter(scan["k"][~ok], scan["silhouette"][~ok], s=40, facecolor=SURFACE, edgecolor=ACCENT,
                       linewidth=1.5, zorder=3, label="a cluster below min size")
            ax.set_title(f"{block.capitalize()} block")
            ax.set_xlabel("k (clusters)")
            ax.set_ylabel("Mean silhouette")
            ax.set_xticks(scan["k"])
            ax.grid(axis="y")
            ax.legend(loc="best", fontsize=8)
        fig.suptitle("Choice of k: silhouette by number of clusters", x=0.01, ha="left", fontweight="bold")
        fig.tight_layout()
        self._save(fig, "01_k_scan")

    def silhouette(self, result: ClassificationResult, model: MorphotypeModel) -> None:
        fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
        for ax, block, ramp in zip(axes, BLOCKS, (BLUE_ORDINAL, ORANGE_ORDINAL)):
            r = result.blocks[block]
            k = model.block(block).k
            colors = _ordinal(ramp, k)
            y = 0
            for c in range(k):
                vals = np.sort(r.silhouette[r.labels == c])
                ax.barh(np.arange(y, y + len(vals)), vals, height=1.0, color=colors[c], linewidth=0)
                ax.text(-0.02, y + len(vals) / 2, model.names[block][c].split(" · ")[0], ha="right",
                        va="center", fontsize=8, color=INK_2)
                y += len(vals) + max(3, len(r.labels) // 60)
            ax.axvline(r.sil_mean, color=INK_2, lw=1)
            ax.text(r.sil_mean, y, f" mean {r.sil_mean:.2f}", fontsize=8, color=INK_2, va="bottom")
            ax.set_yticks([])
            ax.spines["left"].set_visible(False)
            ax.set_xlabel("Silhouette")
            ax.set_title(f"{block.capitalize()} block")
        fig.tight_layout()
        self._save(fig, "02_silhouette")

    def profiles(self, model: MorphotypeModel) -> None:
        fig, axes = plt.subplots(1, 2, figsize=(13, 4.8),
                                 gridspec_kw={"width_ratios": [len(model.block(b).features) for b in BLOCKS]})
        for ax, block in zip(axes, BLOCKS):
            cen = model.block(block).centroids
            lim = max(1.0, float(np.nanmax(np.abs(cen.to_numpy()))))
            lim = min(lim, 3.0)
            ax.imshow(cen.to_numpy(), cmap=DIVERGING, vmin=-lim, vmax=lim, aspect="auto")
            for (i, j), v in np.ndenumerate(cen.to_numpy()):
                ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=7.5,
                        color="white" if abs(v) > 0.65 * lim else INK)
            ax.set_xticks(range(cen.shape[1]), [label(f, short=True) for f in cen.columns],
                          rotation=40, ha="right")
            ax.set_yticks(range(cen.shape[0]), [model.names[block][c] for c in cen.index], fontsize=8)
            ax.tick_params(length=0)
            for s in ax.spines.values():
                s.set_visible(False)
            ax.set_title(f"{block.capitalize()} clusters: centroid, IQRs from the median")
        fig.tight_layout()
        self._save(fig, "03_cluster_profiles")

    def morphotype_matrix(self, result: ClassificationResult, model: MorphotypeModel) -> None:
        t = result.table
        kt, kc = model.transport.k, model.context.k
        cols = list(range(kc)) + ([-1] if (t["C_cluster"] < 0).any() else [])
        m = pd.crosstab(t["T_cluster"], t["C_cluster"]).reindex(index=range(kt), columns=cols, fill_value=0)
        fig, ax = plt.subplots(figsize=(1.6 * len(cols) + 3, 0.7 * kt + 1.6))
        ax.imshow(m.to_numpy(), cmap=SEQ_BLUE, aspect="auto")
        vmax = m.to_numpy().max() or 1
        for (i, j), v in np.ndenumerate(m.to_numpy()):
            ax.text(j, i, f"{v:,}", ha="center", va="center", fontsize=9,
                    color="white" if v > 0.55 * vmax else INK)
        ax.set_xticks(range(len(cols)), [model.names["context"].get(c, "C_null").replace(" · ", "\n")
                                         for c in cols], fontsize=7.5)
        ax.set_yticks(range(kt), [model.names["transport"][c] for c in range(kt)], fontsize=8)
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_title("Morphotype matrix: segments per transport x context class")
        self._save(fig, "04_morphotype_matrix")

    def city_composition(self, df: pd.DataFrame, result: ClassificationResult) -> None:
        share = pd.crosstab(result.table["morphotype"], df["city"], normalize="columns")
        cities = list(share.columns)
        fig, axes = plt.subplots(1, len(cities), figsize=(3.6 * len(cities), 0.32 * len(share) + 1.5),
                                 sharey=True, squeeze=False)
        for ax, city in zip(axes[0], cities):
            vals = share[city].to_numpy()
            y = np.arange(len(share))
            ax.barh(y, vals, height=0.6, color=ACCENT)
            for yi, v in zip(y, vals):
                if v > 0:
                    ax.text(v, yi, f" {v:.0%}", va="center", fontsize=7.5, color=INK_2)
            ax.set_yticks(y, share.index, fontsize=8)
            ax.set_axisbelow(True)
            ax.set_xlim(0, share.to_numpy().max() * 1.25)
            ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
            ax.set_title(city)
            ax.grid(axis="x")
        axes[0][0].invert_yaxis()  # shared y axis: invert once
        fig.suptitle("Share of classified segments by morphotype", x=0.01, ha="left", fontweight="bold")
        fig.tight_layout()
        self._save(fig, "05_city_composition")

    # ── Maps ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _map_axes(ax, gdf: gpd.GeoDataFrame) -> None:
        gdf.plot(ax=ax, color=CONTEXT_NET, linewidth=0.4)
        ax.set_axis_off()
        ax.set_aspect("equal")

    def _ordinal_map(self, ax, gdf, column, names, ramp, title, null_label=None) -> None:
        classified = gdf[gdf[column].notna()]
        k = int(classified[column].max()) + 1 if len(classified) else 0
        colors = _ordinal(ramp, k)
        self._map_axes(ax, gdf)
        handles = []
        if null_label is not None and (classified[column] < 0).any():
            classified[classified[column] < 0].plot(ax=ax, color=NULL_COLOR, linewidth=0.9)
            handles.append(Line2D([], [], color=NULL_COLOR, lw=3, label=null_label))
        for c in range(k):
            part = classified[classified[column] == c]
            if len(part):
                part.plot(ax=ax, color=colors[c], linewidth=1.2)
            handles.append(Line2D([], [], color=colors[c], lw=3, label=names.get(c, str(c))))
        ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.0, 0.0), fontsize=8)
        ax.set_title(title)

    def cluster_maps(self, city: str, gdf: gpd.GeoDataFrame, model: MorphotypeModel) -> None:
        fig, axes = plt.subplots(1, 2, figsize=(14, 8.5))
        self._ordinal_map(axes[0], gdf, "T_cluster", model.names["transport"], BLUE_ORDINAL,
                          f"{city}: transport clusters")
        self._ordinal_map(axes[1], gdf, "C_cluster", model.names["context"], ORANGE_ORDINAL,
                          f"{city}: context clusters", null_label="C_null · no reliable building data")
        fig.tight_layout()
        self._save(fig, f"10_map_clusters_{city}")

    def morphotype_multiples(self, city: str, gdf: gpd.GeoDataFrame, model: MorphotypeModel) -> None:
        classified = gdf[gdf["morphotype"].notna()]
        types = sorted(classified["morphotype"].unique())
        if not types:
            return
        ncol = min(4, len(types))
        nrow = math.ceil(len(types) / ncol)
        fig, axes = plt.subplots(nrow, ncol, figsize=(4.2 * ncol, 4.4 * nrow), squeeze=False)
        for ax, code in zip(axes.flat, types):
            part = classified[classified["morphotype"] == code]
            self._map_axes(ax, gdf)
            part.plot(ax=ax, color=ACCENT, linewidth=1.3)
            name = textwrap.fill(part["morphotype_name"].iloc[0], 48)
            ax.set_title(f"{code} · {len(part):,} segments\n{name}", fontsize=8, fontweight="normal")
        for ax in list(axes.flat)[len(types):]:
            ax.set_axis_off()
        fig.suptitle(f"{city}: morphotypes", x=0.01, y=1.0, ha="left", va="bottom", fontweight="bold")
        fig.tight_layout(h_pad=2.5)
        self._save(fig, f"11_map_morphotypes_{city}")

    def space_syntax_maps(self, city: str, gdf: gpd.GeoDataFrame) -> None:
        cols = [c for c in gdf.columns if c.startswith(("ss_nain_", "ss_nach_"))]
        if not cols:
            return
        cols = sorted(cols, key=lambda c: (c.split("_")[1], c != "ss_" + c.split("_")[1] + "_n", c))
        ncol = 2
        nrow = math.ceil(len(cols) / ncol)
        fig, axes = plt.subplots(nrow, ncol, figsize=(8 * ncol, 7 * nrow), squeeze=False)
        for ax, col in zip(axes.flat, cols):
            data = gdf[gdf[col].notna()].sort_values(col)
            self._map_axes(ax, gdf)
            lo, hi = np.nanpercentile(data[col], [2, 98])
            data.plot(ax=ax, column=col, cmap=SEQ_BLUE, vmin=lo, vmax=hi, linewidth=1.0)
            sm = plt.cm.ScalarMappable(cmap=SEQ_BLUE, norm=plt.Normalize(lo, hi))
            fig.colorbar(sm, ax=ax, shrink=0.5, pad=0.01).outline.set_visible(False)
            ax.set_title(label(col))
        for ax in list(axes.flat)[len(cols):]:
            ax.set_axis_off()
        fig.suptitle(f"{city}: space syntax (colour range: 2nd-98th percentile)", x=0.01, ha="left",
                     fontweight="bold")
        fig.tight_layout()
        self._save(fig, f"12_map_space_syntax_{city}")

    def borderline_map(self, city: str, gdf: gpd.GeoDataFrame) -> None:
        fig, ax = plt.subplots(figsize=(9, 8))
        self._map_axes(ax, gdf)
        classified = gdf[gdf["borderline"].notna()]
        solid = classified[~classified["borderline"].astype(bool)]
        weak = classified[classified["borderline"].astype(bool)]
        solid.plot(ax=ax, color=MUTED, linewidth=0.8)
        weak.plot(ax=ax, color="#e34948", linewidth=1.3)
        ax.legend(handles=[Line2D([], [], color=MUTED, lw=3, label=f"confident ({len(solid):,})"),
                           Line2D([], [], color="#e34948", lw=3, label=f"borderline ({len(weak):,})")],
                  loc="upper left", bbox_to_anchor=(0.0, 0.0), fontsize=8)
        ax.set_title(f"{city}: borderline segments (low silhouette or GMM confidence)")
        self._save(fig, f"13_map_borderline_{city}")
