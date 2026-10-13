"""Command line interface.

    street-morphotypes fetch    configs/irkutsk.yaml     download OSM layers into the cache
    street-morphotypes features configs/irkutsk.yaml     network, space syntax, metrics -> features.gpkg
    street-morphotypes scan     configs/irkutsk.yaml     silhouette by k + correlated features
    street-morphotypes run      configs/irkutsk.yaml     full local run (also works with a pooled config)
    street-morphotypes apply    configs/city.yaml --model outputs/<run>/model.joblib
    street-morphotypes web      [--outputs outputs] [--web-dir web]   rebuild the web map data
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from .config import CityConfig, load_config
from .io.web import export_web
from .pipeline import CityPipeline, PooledPipeline


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s", datefmt="%H:%M:%S")
    for noisy in ("urllib3", "fiona", "pyogrio", "matplotlib", "PIL"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="street-morphotypes",
                                 description="Street segment morphotypes from OSM: space syntax + urban context.")
    ap.add_argument("-v", "--verbose", action="store_true")
    sub = ap.add_subparsers(dest="command", required=True)
    for name, help_ in [("fetch", "download OSM layers into the cache"),
                        ("features", "compute the per-segment feature table"),
                        ("scan", "silhouette by k for both blocks + correlated features"),
                        ("run", "full run: features, clustering, export"),
                        ("apply", "label a city with a saved model")]:
        p = sub.add_parser(name, help=help_)
        p.add_argument("config", type=Path, help="city or pooled YAML config")
        if name not in ("fetch", "features"):
            p.add_argument("--recompute", action="store_true", help="rebuild features even if saved")
        if name == "apply":
            p.add_argument("--model", type=Path, required=True, help="path to model.joblib")
    p = sub.add_parser("web", help="rebuild the web map data from the runs in the output folder")
    p.add_argument("--outputs", type=Path, default=Path("outputs"), help="folder with run outputs")
    p.add_argument("--web-dir", type=Path, default=Path("web"), help="web map folder")
    args = ap.parse_args(argv)
    _setup_logging(args.verbose)

    if args.command == "web":
        export_web(args.outputs, args.web_dir)
        return 0

    start = time.time()
    cfg = load_config(args.config)
    is_city = isinstance(cfg, CityConfig)
    if args.command in ("fetch", "features", "apply") and not is_city:
        ap.error(f"`{args.command}` needs a city config, {args.config} is a pooled config")

    pipeline = CityPipeline(cfg) if is_city else PooledPipeline(cfg)
    if args.command == "fetch":
        pipeline.fetch()
    elif args.command == "features":
        pipeline.features(recompute=True)
    elif args.command == "scan":
        pipeline.scan(recompute=args.recompute)
    elif args.command == "run":
        pipeline.run(recompute=args.recompute)
    elif args.command == "apply":
        pipeline.apply(args.model, recompute=args.recompute)
    logging.getLogger(__name__).info("Done in %.1f min", (time.time() - start) / 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
