#!/usr/bin/env bash
# Reproduces every number of the Irkutsk–Wrocław case study in README.md and
# docs/METHODOLOGY.md § 9: local, pooled and cross-applied runs, the k = 4
# context experiment, bootstrap stability and run comparisons.
#
#   bash scripts/reproduce_case_study.sh            # reuses downloaded OSM layers
#   RECOMPUTE=1 bash scripts/reproduce_case_study.sh  # also rebuilds the feature tables
set -euo pipefail

SM=${SM:-street-morphotypes}
PY=${PY:-python}
RECOMPUTE_FLAG=${RECOMPUTE:+--recompute}
E=outputs/experiments/context_k4

echo "== local runs"
$SM run configs/irkutsk.yaml $RECOMPUTE_FLAG
$SM run configs/wroclaw.yaml $RECOMPUTE_FLAG

echo "== pooled typology and cross-application"
$SM run configs/irkutsk_wroclaw_pooled.yaml
$SM apply configs/wroclaw.yaml --model outputs/irkutsk/model.joblib
$SM apply configs/irkutsk.yaml --model outputs/wroclaw/model.joblib

echo "== experiment: four context classes everywhere (features reused)"
for c in irkutsk wroclaw; do
  mkdir -p "$E/$c"
  cp "outputs/$c/features.gpkg" "outputs/$c/features_meta.json" "$E/$c/"
  $SM run "configs/experiments/${c}_context_k4.yaml"
done
$SM run configs/experiments/irkutsk_wroclaw_pooled_context_k4.yaml
$SM apply configs/experiments/wroclaw_context_k4.yaml --model "$E/irkutsk/model.joblib"
$SM apply configs/experiments/irkutsk_context_k4.yaml --model "$E/wroclaw/model.joblib"

echo "== bootstrap stability"
$PY scripts/stability.py configs/irkutsk.yaml --runs 30
$PY scripts/stability.py configs/wroclaw.yaml --runs 30
$PY scripts/stability.py configs/experiments/irkutsk_context_k4.yaml --runs 30

echo "== transferability"
compare() { $PY scripts/compare_runs.py "$1" "$2" --names "$3" "$4" --json "docs/transfer/$5.json" > /dev/null; }
for prefix in "" "k4_"; do
  root=$([ -z "$prefix" ] && echo outputs || echo "$E")
  compare "$root/wroclaw/morphotypes.gpkg" "$root/wroclaw/applied_irkutsk/morphotypes.gpkg" \
          wroclaw_local irkutsk_model "${prefix}wroclaw_local_vs_irkutsk_model"
  compare "$root/irkutsk/morphotypes.gpkg" "$root/irkutsk/applied_wroclaw/morphotypes.gpkg" \
          irkutsk_local wroclaw_model "${prefix}irkutsk_local_vs_wroclaw_model"
  compare "$root/irkutsk/morphotypes.gpkg" "$root/irkutsk_wroclaw/morphotypes_irkutsk.gpkg" \
          irkutsk_local pooled "${prefix}irkutsk_local_vs_pooled"
  compare "$root/wroclaw/morphotypes.gpkg" "$root/irkutsk_wroclaw/morphotypes_wroclaw.gpkg" \
          wroclaw_local pooled "${prefix}wroclaw_local_vs_pooled"
done
echo "== done: scores in docs/transfer/ and docs/stability/"
