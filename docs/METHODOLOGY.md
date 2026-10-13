# Methodology

This document describes what the tool computes and why. The configuration
keys that control each step are given in `code` font; their defaults live in
[`src/street_morphotypes/defaults.yaml`](../src/street_morphotypes/defaults.yaml).

## 1. Problem

A street is two things at once: a **link in a movement network** and a
**place** lined by buildings and activities (Marshall 2005; Jones, Roberts &
Morris 2007, "Link and Place"). Street design guidance is increasingly written
per street *type*, but types are usually assigned by hand from the road
hierarchy, which only describes the link role.

The tool derives street types from data, separately for the two roles, and
crosses them:

```
              context (place) clusters  C0 … Cm
transport  T0 │ T0-C0   T0-C1   …
(link)     T1 │ T1-C0   T1-C1   …
clusters   …  │ …
```

A **morphotype** is a cell of this matrix. Clustering the blocks
*independently* (in parallel, not on one joint feature vector) is deliberate:

- each block gets its own number of clusters, chosen by its own silhouette;
- a dominant block cannot swamp the other: in a joint space the many context
  features would decide most of the partition;
- the result is readable: "arterial × residential context" is a
  combination of two interpretable labels, which a joint cluster is not.

The method generalises an earlier version developed for one Russian city on
survey data (traffic counts, pedestrian flows, commercial floor areas). Here
every input is derived from OpenStreetMap so that any city can be processed;
survey data can still be added (section 6).

## 2. Unit of analysis: the street segment

A segment is a link between two junctions of the drivable street network.

- **Network** — OSM ways with `highway` in `network.highway_types`
  (motorway … living_street and the `*_link` ramps). Footways, paths, cycleways
  and `service` roads (driveways, parking aisles) are excluded: they do not form
  the city-wide vehicular grid. Ways with `access=private|no` are excluded.
- **Simplification** — OSMnx removes interstitial nodes, so a segment runs from
  junction to junction. Clusters of junction nodes closer than
  `network.consolidate_tolerance_m` (complex intersections, roundabouts) are
  merged into one junction (Boeing 2025).
- **Pseudo-junctions are removed.** Consolidation leaves behind nodes where only
  two segments meet (in Irkutsk 1 124, in Wrocław 1 832, against ~30 in the raw
  OSMnx graph); one-way/two-way changes and user networks produce them too. A
  segment that ends at such a node does not end at a junction, so chains through
  them are merged (`network.merge_pseudo_junctions`) with their exact geometry —
  re-running OSMnx simplification is not an option, because it would replace
  curved streets by straight chords. The merged segment takes the most important
  `highway` value, is one-way if most of its length is, and keeps all lanes,
  speed and name values. Afterwards every node has degree 1 (dead end) or ≥ 3.
  Crossings without a shared node are left as they are: in both cities all of
  them but one are bridges or tunnels.
- **Divided roads are not merged.** The two carriageways of a dual carriageway
  are separate OSM ways and remain separate segments, because their two sides
  can have different contexts (shops on one side, a park on the other). A
  one-way segment's **twin** is the parallel opposite carriageway: within
  `max_distance_m`, direction within `max_angle_deg`, and running alongside for at
  least `min_overlap` of the length (the nearest point must fall inside the
  twin, so the next segment of the same one-way street does not qualify). For
  twinned segments:
  - context metrics use only the **outer side** (the side away from the twin);
  - lanes and public transport routes are summed / united over both
    carriageways, so that a divided road is comparable to an undivided one.
- **Which segments are classified** — those whose midpoint lies in the study
  area, longer than `network.min_segment_length_m` and not ramps
  (`network.unclassified_highway_types`). Short and ramp segments stay in the
  space syntax graph.

## 3. Study area and edge effects

The study area is a city boundary (geocoded), a circle around a point, or a
user polygon. Metrics that look beyond the segment are computed on larger
extents so that boundary segments are not penalised:

- the street network is downloaded for the area + `area.network_buffer_m`
  (space syntax depth and choice depend on what lies beyond the boundary);
- buildings, POIs and green areas for the area + `area.context_buffer_m`.

## 4. Transport block

### 4.1 Space syntax: angular segment analysis

Angular segment analysis (Turner 2001; Hillier & Iida 2005) models route choice
as the path of least *angular* change. It is computed on the **dual graph**:
vertices are segments, edges are the transitions between segments sharing a
junction.

- **Transition cost** = turn angle / `space_syntax.angle_unit_deg`
  (default 90°, so a right-angle turn costs 1 and going straight costs ~0, the
  depthmapX convention), plus 10⁻⁶ so that zero-cost cycles cannot occur.
- **Turn angle** at a junction is measured between the directions of the two
  segments `space_syntax.direction_sample_m` metres away from the junction
  (robust to tiny last vertices). Between two segments meeting at more than one
  junction, the smaller angle is kept.

For each radius *r* in `space_syntax.radii` and each segment *i*:

| Measure | Definition |
|---|---|
| NC(i) | node count: segments reachable within *r*, including *i* |
| TD(i) | total angular depth: Σ least-angle cost from *i* to them |
| CH(i) | choice: number of least-angle paths between pairs of segments (both within *r* of each other) that pass through *i* (betweenness) |
| **NAIN(i)** | **NC^1.2 / (TD + 2)** — normalised angular integration |
| **NACH(i)** | **log(CH + 1) / log(TD + 3)** — normalised angular choice |

Normalisations follow Hillier, Yang & Turner (2012); they make integration and
choice comparable between systems of different size, which is what a
multi-city tool needs. NAIN describes *to-movement* (how accessible a segment is
as a destination); NACH describes *through-movement* (how likely it is to be on
routes between other places).

**Radii.** `"n"` is the whole graph (global, city scale). A metric radius *r*
restricts both the reachable set and the counted paths to those whose length
along the least-angle path, measured between segment midpoints
(½·length(*a*) + ½·length(*b*) per transition), does not exceed *r* — the same
convention as depthmapX. Typical choices: 800 m (pedestrian, ~10 minutes) and
2 000 m and more (local vehicular).

**Implementation.** The global radius uses igraph (C) for closeness and
betweenness. Metric radii use a Brandes (2001) least-angle search with a metric
cut-off, written in Python and parallelised over origins (`n_jobs`); only
origins that can reach the study area within *r* are processed, and choice is
only reported for study-area segments. The two implementations agree exactly
when the radius is unbounded (unit test).

*Approximation note:* with a metric radius, the least-angle path is found
first and then cut at *r*. A path with more turns but within *r* is not
considered. depthmapX makes the same approximation.

### 4.2 OSM attributes

| Feature | Source | Gaps |
|---|---|---|
| `lanes` | `lanes` tag; both carriageways summed for twinned segments | filled from `metrics.lanes.defaults_by_highway` (two-way total; one-way gets half, rounded up); share imputed is reported |
| `maxspeed` | `maxspeed` tag; mph converted; zone codes (`RU:urban`, `GB:nsl_single`, …) via `zone_values` | filled from `metrics.maxspeed.defaults_by_highway` |
| `pt_routes` | OSM route relations (`route` in `route_types`) whose member ways include the segment's OSM ways; variants and directions with the same `ref` count once (`dedupe_by: ref`) | none; 0 when no route |
| `pt_stops_per_100m` | `highway=bus_stop`, `railway=tram_stop`, `public_transport=platform`; points closer than `stop_merge_distance_m` merged into one stop; each stop assigned to its nearest segment within `stops_buffer_m` | none |

The `highway` class itself is **not** a clustering feature: it is an expert
classification already, and using it would make the result partly circular. It
is only used to fill gaps in lanes and speed.

## 5. Context block

### 5.1 Side strips

All context metrics are measured in **one-sided strips** on the left and right
of a segment: from the centreline to the carriageway edge plus the metric's own
`buffer_m`. The carriageway half-width is lanes × `metrics.carriageway.lane_width_m`
/ 2, so wide roads are not penalised for their own width. Strips have flat ends
and do not wrap around the segment ends into side streets. Twinned carriageways
get the outer strip only.

### 5.2 Metrics

| Feature | Definition |
|---|---|
| `frontage` | **Street-wall continuity.** Buildings intersecting a strip (`metrics.frontage.buffer_m`, the maximum setback) are clipped to it and projected onto the centreline; the union of the projected intervals divided by the segment length gives the covered share of each side; the sides are averaged. 1 = a continuous wall on both sides. |
| `poi_per_100m` | Organisations (shops, offices, services, education, health, culture, … — `metrics.poi_density.tags`) inside the strips, per 100 m of segment. With `assignment: nearest` a POI counts for its closest segment only, so corner POIs are not double counted. |
| `green_m2_per_100m` | Green area (parks, gardens, lawns, woods — `metrics.green_area.tags`), dissolved first so nested polygons are not counted twice, intersected with the strips, per 100 m of segment. `green_share` = the same area / strip area (not clustered). |
| `building_age_median` | Median construction year of buildings intersecting the strips, as age in years relative to a fixed `reference_year` (so that features and saved models do not change with the date of the run). **Dropped automatically** when fewer than `min_coverage` of the area's buildings have a year (`start_date` and similar tags) — in most cities OSM coverage is far below that; supply a buildings layer with `year_built` instead (section 6). |
| `fn_residential`, `fn_commercial`, `fn_social`, `fn_industrial` | Floor-area shares of functions, section 5.3. |

### 5.3 Functional mix from open data

OSM does not record floor area by use, so the shares are **estimates**. Per
building:

1. **Floors.** `building:levels`; else `height` / `floor_height_m`; else the
   city's median floors for the same `building` value (if at least
   `min_level_samples` buildings of that type have a value); else
   `default_levels`.
2. **Gross floor area** = footprint × floors.
3. **Function** — the first rule that gives an answer:
   1. user `function` column (if a buildings layer is supplied);
   2. the `building` tag (`building:use` when `building=yes`) → `building_tags`;
   3. tags on the footprint itself (e.g. `building=yes` + `amenity=school`) → `poi_tags`;
   4. the majority category of POIs inside the footprint → `poi_tags`;
   5. the land-use polygon containing the building (the smallest one when
      several overlap) → `landuse_tags`;
   6. otherwise `unknown`.

   In every tag mapping explicit values win over wildcards, so
   `office=government` is social while any other `office=*` is commercial.
4. **Mixed use.** A residential building with commercial or social POIs inside
   gets 1/floors of its floor area (the ground floor) assigned to that category.

Per segment, each building contributes its floor area multiplied by the share
of its footprint that lies inside the strips. The shares `fn_*` are computed
over the floor area whose function is known; `fn_unknown` (share of the total)
is reported separately. When `fn_unknown > max_unknown_share` the segment's
context is unreliable: it receives the label **C_null**, is excluded from the
context clustering and keeps its transport label (as in the original study,
where segments without building data were treated the same way). Segments with
no buildings at all are *not* C_null — "no buildings" is a real context (a
road through a park or an industrial zone) and gets shares of 0.

**Limitations.** The estimate is only as good as the tagging: in many cities
most buildings are `building=yes`, so land-use polygons do much of the work and
a whole residential block may be counted as purely residential even with shops
on the ground floor. The data-quality sheet of every run reports which rule
assigned how much floor area, the share of imputed floors and the number of
mixed-use buildings, so the reliability of the shares is visible. Better data
can replace any step (section 6).

## 6. User data

Any OSM layer can be replaced by a file (`layers.<name>.source: file`), and
arbitrary segment attributes can be added through `extra_features`, each
assigned to the transport or context block. Expected column names are listed in
the README. Typical uses: traffic and pedestrian counts (the transport block of
the original study), cadastral building data with use and floor area, building
age from a city register.

## 7. Clustering

Both blocks use the same procedure.

1. **Preprocessing** (fitted on the training data, stored in the model):
   - features whose most frequent value covers more than `max_mode_share` of
     the segments are dropped as near-constant (e.g. the speed limit in a
     Russian city centre, where almost every street is 60 km/h, or the industrial
     share in a historic core). Such a feature carries no typological
     information, and after scaling its few non-zero segments become extreme
     outliers that form a cluster of their own — the degenerate
     "≈ all vs a handful" split diagnosed in the earlier study;
   - missing values → training median;
   - `log1p` for non-negative features with skewness > `skew_threshold`
     (densities and intensities are strongly right-skewed);
   - robust scaling `(x − median) / IQR`, so that a few very dense streets do
     not dominate the distance. When the IQR is 0 (a mostly-zero feature such as
     stops per 100 m) the standard deviation is used instead — dividing by 1
     would leave raw units and let that feature dominate;
   - scaled values are clipped to ±`clip_scaled` as a final guard against
     single extreme segments.
2. **Number of clusters.** For `k: auto` every k in `k_range` is fitted and the
   one with the highest mean silhouette is kept, among solutions whose smallest
   cluster holds at least `min_cluster_frac` of the segments (tiny clusters of
   outliers inflate the silhouette without being a street type).
3. **KMeans** (`kmeans_n_init` restarts, fixed `random_state`).
4. **Stable numbering.** Clusters are renumbered by the ascending mean of
   `order_by` (default NACH for transport — T0 carries the least through-movement;
   organisations per 100 m for context), so labels mean the same on every run.
5. **Confidence.** Each KMeans cluster is modelled as a Gaussian with the
   cluster's own mean, covariance (`gmm_covariance_type`; clusters with fewer
   members than features use the pooled covariance) and weight. The confidence
   of a segment is the posterior probability of *its own* cluster under this
   mixture: near 1 deep inside a cluster, near 1/k between clusters. The
   parameters are taken from the partition rather than fitted by EM on purpose:
   a freely fitted GMM — even one started at the KMeans centroids — drifts to
   components that no longer match the clusters, and its posterior then
   describes a different partition (in testing it returned 0 for almost half of
   the segments). Taking the maximum posterior over all components, as the
   earlier version did, has the same problem.
6. **Borderline segments.** A segment is flagged when, in either block, its
   silhouette is below `min_silhouette` or its confidence below
   `min_confidence`. Street types overlap in reality, so borderline segments are
   reported rather than hidden; they are the ones to check by hand.
7. **Names.** A cluster is named after the features whose centroid lies at
   least 0.5 IQR from the median (up to two), e.g. *"T3 · high through-movement
   Rn, high PT routes"*. Manual names in `names` override them.

`scan` prints the silhouette for every k and the feature pairs with
|Spearman r| ≥ `correlation_warning`, to support feature selection before a run.

## 8. One city or many

| Mode | Command | Typology |
|---|---|---|
| local | `run configs/city.yaml` | the city's own: clusters reflect what is typical *for this city* |
| pooled | `run configs/pooled.yaml` | shared by all listed cities: one set of clusters, comparable across them |
| apply | `apply configs/city.yaml --model …/model.joblib` | a saved typology (local or pooled) labels a new city without refitting |

A **pooled** model is the basis for street-type design guidance that must be the
same everywhere: the types and their recommendations are defined once, on a
diverse set of cities, and then *applied*. **Local** runs show the structure
specific to a city. The scaler is part of the model, so in `apply` a city is
measured against the training distribution, not its own.

In a pooled run only features that **every** city has are used. A feature
missing in one city (a metric disabled in its config, dropped for low data
coverage, or a layer set to `none`) would otherwise be filled with the other
cities' median for all of that city's segments, and the clusters would partly
separate cities instead of street forms; such features are dropped with a
warning.

## 9. Validation

### 9.1 Space syntax against depthmapX

`scripts/validate_depthmapx.py` reads a depthmapX segment map export (MapInfo,
with `T<bins>_Node_Count`, `T<bins>_Total_Depth`, `T<bins>_Choice`), analyses
the same straight-line segments with this package at radius n and compares the
measures segment by segment. On a 47 139-segment city network (depthmapX tulip
analysis, 64 bins):

| Measure | Pearson r | Spearman ρ | Note |
|---|---|---|---|
| NC (node count) | — | — | identical for every segment; dual-graph degree identical to depthmapX connectivity |
| TD (total angular depth) | 0.977 | 0.977 | ours is 10–40 % higher (median ratio 1.22) |
| Choice | 0.849 | 0.921 | heavy-tailed; log-scale r = 0.93 |
| **NAIN** | **0.978** | **0.977** | |
| **NACH** | **0.932** | **0.922** | |

The graph topology is reproduced exactly, and the ranking of segments — which
is what clustering uses after robust scaling — agrees closely. The remaining
systematic difference in total depth is not fully explained. Replicating
depthmapX's quantisation of angles into 64 bins (`--tulip-bins 64`) lowers the
median ratio from 1.29 to 1.22 and raises the correlations slightly, so binning
is part of it; the rest presumably comes from details of the tulip search that
are not reproduced here. Values are therefore comparable within this package
(between cities and runs), but not interchangeable with depthmapX values.

### 9.2 Bootstrap stability

`scripts/stability.py` refits a run 30 times on random 80 % subsamples of the
segments (k fixed at the run's values), labels all segments with each refit and
compares with the reference labelling: Adjusted Rand Index (ARI) per block, and
per cluster the mean Jaccard coefficient of its best-matching cluster (Hennig
2007; < 0.6 unstable, > 0.75 stable).

| Run | Transport ARI mean (min) | Context ARI mean (min) | Least stable context cluster (Jaccard) |
|---|---|---|---|
| Irkutsk, auto k (T 4, C 6) | 0.995 (0.99) | 0.93 (0.87) | C4 green with organisations (0.61) |
| Irkutsk, context k = 4 | 0.995 (0.99) | 0.90 (0.56) | C3 green with commerce (0.65) |
| Wrocław, auto k (T 4, C 4) | 0.98 (0.94) | 0.88 (0.62) | C2 social (0.77) |

Every transport cluster is stable (Jaccard ≥ 0.98). Context clusters are stable
on average; the small mixed classes (green streets with shops or institutions)
are the least sharply delimited and should be read as transitions rather than
types.

### 9.3 Transferability between cities

`scripts/compare_runs.py` compares two labellings of the same segments. Each
city was labelled by its own model (local), by the other city's model
(`apply`) and by the pooled model (ARI; 1 = identical partitions):

| Labelling compared with the city's own | Transport | Context | Morphotype |
|---|---|---|---|
| Wrocław by the Irkutsk model, auto k | 0.91 | 0.44 | 0.57 |
| Irkutsk by the Wrocław model, auto k | 0.91 | 0.61 | 0.74 |
| Wrocław by the Irkutsk model, context k = 4 in both | 0.91 | 0.42 | 0.58 |
| Irkutsk by the Wrocław model, context k = 4 in both | 0.91 | 0.64 | 0.76 |
| Irkutsk by the pooled model, auto k | 0.97 | 0.32 | 0.61 |
| Wrocław by the pooled model, auto k | 0.91 | 0.36 | 0.57 |

- The **transport typology transfers almost perfectly**: under the other city's
  model 91–99 % of the segments of every class keep their class. Classes defined
  by space syntax and public transport describe the same street roles in a
  Siberian and a Central European city.
- The **context typology transfers only in part**, and fixing the same number
  of classes does not change that (0.42–0.64 with k = 4). Comparing the k = 4
  partitions class by class:
  - two types are shared: *built-up streets with little greenery* (Irkutsk C0
    and Wrocław C0 keep 99 % and 75 % of their segments under the other model)
    and *green, mostly non-residential streets* (90 % and 72 %);
  - *commercial* is relative: 73 % of Irkutsk's commercial streets are ordinary
    built-up streets by Wrocław's standards, while 96 % of Wrocław's commercial
    streets are commercial by Irkutsk's;
  - Wrocław's *social / institutional* type has no counterpart in Irkutsk and is
    split between the green classes.
- The **pooled** model with automatic k keeps only two context classes and
  therefore agrees with neither city's finer local partition (0.32–0.36).

Practical consequence: the transport typology can be defined once and applied
anywhere. Context types depend on what is ordinary in the training cities; a
typology that is to carry the same design guidance across cities should be a
pooled model trained on a diverse set of cities, with the number of context
classes fixed by the guidance rather than by the silhouette. All experiment
configs are in `configs/experiments/`, the scores in `docs/transfer/` and
`docs/stability/`; `scripts/reproduce_case_study.sh` recomputes them.

### 9.4 Unit tests

`pytest` covers: turn angles; the Brandes metric-radius search reproducing
igraph closeness and betweenness exactly when the radius is unbounded; the
metric cut-off; NAIN/NACH formulas; divided-road twins (opposite directions,
continuation of the same street, same-direction parallels); tag parsing and
precedence rules; pseudo-junction merging that keeps curved geometry; config merging, `extends` and validation; unique generated cluster names; scaler behaviour on constant,
near-constant and extreme features; block independence, ordering, C_null
handling and model save/load round trips.

## References

- Boeing, G. (2025). Topological graph simplification solutions to the street intersection miscount problem. *Transactions in GIS*, 29(3), e70037.
- Brandes, U. (2001). A faster algorithm for betweenness centrality. *Journal of Mathematical Sociology*, 25(2), 163–177.
- Hennig, C. (2007). Cluster-wise assessment of cluster stability. *Computational Statistics & Data Analysis*, 52(1), 258–271.
- Hillier, B., & Iida, S. (2005). Network and psychological effects in urban movement. *COSIT 2005*, LNCS 3693, 475–490.
- Hillier, B., Yang, T., & Turner, A. (2012). Normalising least angle choice in Depthmap and how it opens up new perspectives on the global and local analysis of city space. *Journal of Space Syntax*, 3(2), 155–193.
- Jones, P., Roberts, M., & Morris, L. (2007). *Rediscovering mixed-use streets: the contribution of local high streets to sustainable communities*. Policy Press.
- Marshall, S. (2005). *Streets and Patterns*. Spon Press.
- Turner, A. (2001). Angular analysis. *Proceedings of the 3rd International Space Syntax Symposium*, Atlanta.
