"""Overpass access with endpoint fallback (some mirrors are unreachable in some networks)."""
from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

import osmnx as ox
import requests
from osmnx._errors import InsufficientResponseError

from ..config import OverpassConfig

log = logging.getLogger(__name__)
T = TypeVar("T")


class EmptyResponse(Exception):
    """The query succeeded but matched nothing."""


class OverpassClient:
    """Runs OSMnx calls and raw Overpass QL queries, falling back across endpoints."""

    _PROBE_QL = "[out:json][timeout:10];node(1);out ids;"
    _PROBE_TIMEOUT_S = 60
    _BUSY_RETRIES = 6
    _BUSY_PAUSE_S = 30

    def __init__(self, cfg: OverpassConfig, http_cache_dir: str | None = None) -> None:
        self.cfg = cfg
        ox.settings.requests_timeout = cfg.timeout_s
        ox.settings.log_console = False
        # The /status rate-limit check hangs on some mirrors; endpoints are probed instead.
        ox.settings.overpass_rate_limit = False
        if http_cache_dir:
            ox.settings.cache_folder = http_cache_dir
        self._working_url: str | None = None
        self._probed = False

    def _probe(self) -> None:
        """Find the first endpoint that answers a tiny query (unreachable ones would hang for minutes)."""
        self._probed = True
        busy = None
        for url in self.cfg.urls:
            try:
                resp = requests.post(url.rstrip("/") + "/interpreter", data={"data": self._PROBE_QL},
                                     timeout=self._PROBE_TIMEOUT_S, headers=self._headers())
                if resp.status_code in (429, 504):  # reachable but busy: keep as a fallback
                    busy = busy or url
                    log.info("Overpass endpoint %s is busy (%d)", url, resp.status_code)
                    continue
                resp.raise_for_status()
                resp.json()
                self._working_url = url
                log.info("Overpass endpoint: %s", url)
                return
            except Exception as exc:
                log.info("Overpass endpoint %s unavailable (%s)", url, type(exc).__name__)
        if busy:
            self._working_url = busy
            log.info("Overpass endpoint: %s (busy, requests will wait and retry)", busy)
        else:
            log.warning("No Overpass endpoint answered the probe; trying all of them anyway")

    @staticmethod
    def _headers() -> dict:
        return {"User-Agent": ox.settings.http_user_agent, "Referer": ox.settings.http_referer}

    def _urls(self) -> list[str]:
        if not self._probed:
            self._probe()
        urls = list(self.cfg.urls)
        if self._working_url in urls:  # the endpoint that answered goes first
            urls.remove(self._working_url)
            urls.insert(0, self._working_url)
        return urls

    def call(self, fn: Callable[..., T], *args, **kwargs) -> T:
        """Run an OSMnx download function; raises ``EmptyResponse`` if nothing matched."""
        errors = []
        for url in self._urls():
            ox.settings.overpass_url = url
            for attempt in range(1, self.cfg.retries + 1):
                try:
                    result = fn(*args, **kwargs)
                    self._working_url = url
                    return result
                except InsufficientResponseError as exc:
                    raise EmptyResponse(str(exc)) from exc
                except Exception as exc:  # network errors, HTTP 429/504, broken JSON
                    errors.append(f"{url} (attempt {attempt}): {type(exc).__name__}: {exc}")
                    log.warning("Overpass request failed: %s", errors[-1])
                    time.sleep(2 * attempt)
        raise ConnectionError("All Overpass endpoints failed:\n  " + "\n  ".join(errors))

    def query(self, ql: str) -> dict:
        """Run a raw Overpass QL query (JSON output) with the same fallback."""

        def _post() -> dict:
            url = ox.settings.overpass_url.rstrip("/") + "/interpreter"
            for _ in range(self._BUSY_RETRIES):  # busy server: wait, as OSMnx does
                resp = requests.post(url, data={"data": ql}, timeout=self.cfg.timeout_s,
                                     headers=self._headers())
                if resp.status_code not in (429, 504):
                    break
                log.info("Overpass busy (%d), retrying in %d s", resp.status_code, self._BUSY_PAUSE_S)
                time.sleep(self._BUSY_PAUSE_S)
            resp.raise_for_status()
            return resp.json()

        return self.call(_post)
