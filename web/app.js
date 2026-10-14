/* Street Morphotypes web map.
 *
 * Reads window.SM_MANIFEST (data/manifest.js, written by `street-morphotypes web`
 * or automatically after `street-morphotypes run`) and loads one data script per
 * city on demand. Nothing about the cities is hard-coded here: the page shows
 * exactly the cities and layers listed in the manifest.
 */
(() => {
  "use strict";

  const CFG = Object.assign({ basemapTiles: "", maptilerKey: "", basemap: "positron", repoUrl: "" }, window.SM_CONFIG || {});
  const MANIFEST = window.SM_MANIFEST || { cities: [] };
  const CARTO_POSITRON = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json";

  // Palette of src/street_morphotypes/viz/figures.py
  const CHANGED = { transport: "#1c5cab", context: "#c4501f" };  // streets that change class
  const MERGED = { transport: "#86b6ef", context: "#f2996f" };   // streets whose class merges into another
  const COL = { none: "#d9d8d1", cNull: "#b5b4ad", zero: "#d3d2cb", confident: "#a3a29b", borderline: "#e34948", dim: "#dcdbd4" };
  const SEQ_BLUE = ["#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#184f95", "#0d366b"];
  const SEQ_ORANGE = ["#f6c2a8", "#f2996f", "#eb6834", "#c4501f", "#933a12", "#6b2a0c"];
  const BLUE_ORDINAL = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281", "#0d366b"];
  const ORANGE_ORDINAL = SEQ_ORANGE;
  const GROUPS = [
    { id: "transport", title: "Transport" },
    { id: "context", title: "Context" },
    { id: "morphotypes", title: "Street morphotypes" },
    { id: "compare", title: "Difference from own typology" },
  ];
  const DEFAULT_LAYER = "morphotype";

  const $ = (id) => document.getElementById(id);
  const el = (tag, cls, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  };

  const GLOSSARY = {
    nain: "NAIN, normalised angular integration: how easy a street is to reach from everywhere within the radius.",
    nach: "NACH, normalised angular choice: how often a street lies on the simplest routes (through-movement).",
    silhouette: "Mean silhouette (−1…1): how well segments fit their own class rather than the nearest other one. "
      + "Above 0.25 is a usable structure, above 0.5 a clear one.",
    borderline: "Segments whose class is uncertain: low silhouette or low model confidence in either block.",
    defaults: "Share of segments where OpenStreetMap has no lanes / speed-limit tag, filled with defaults by road class.",
    unknown: "Floor area whose use could not be estimated from building tags, land use or points of interest.",
    classified: "Segments inside the study area that took part in clustering (very short or isolated ones do not).",
    k: "Number of transport and context classes of the typology shown.",
    ari: "Adjusted Rand index: agreement of two labellings of the same streets, 1 = identical, 0 = chance.",
  };
  /** A word with a dotted underline that explains itself on hover or focus. */
  function term(text, key) {
    const t = el("span", "term", text);
    t.dataset.tip = GLOSSARY[key] || key;
    t.tabIndex = 0;
    return t;
  }

  const state = { city: null, typology: null, typologyKind: null, data: null, byId: new Map(),
                  layerId: DEFAULT_LAYER, isolate: null, selected: null, hover: null };

  // ── Colours ────────────────────────────────────────────────────────────────

  function hexToRgb(h) { const n = parseInt(h.slice(1), 16); return [n >> 16, (n >> 8) & 255, n & 255]; }
  function rgbToHex(c) { return "#" + c.map((v) => Math.round(v).toString(16).padStart(2, "0")).join(""); }
  function lerpRamp(ramp, t) {
    const x = t * (ramp.length - 1), i = Math.min(Math.floor(x), ramp.length - 2), f = x - i;
    const a = hexToRgb(ramp[i]), b = hexToRgb(ramp[i + 1]);
    return rgbToHex(a.map((v, j) => v + (b[j] - v) * f));
  }
  /** k evenly spaced steps of a ramp, light -> dark (same rule as figures._ordinal). */
  function sample(ramp, k) {
    if (k <= 0) return [];
    if (k === 1) return [ramp[Math.floor(ramp.length / 2)]];
    if (k <= ramp.length) return Array.from({ length: k }, (_, i) => ramp[Math.round((i * (ramp.length - 1)) / (k - 1))]);
    return Array.from({ length: k }, (_, i) => lerpRamp(ramp, i / (k - 1)));
  }
  function rgba(hex, a) { const [r, g, b] = hexToRgb(hex); return `rgba(${r},${g},${b},${a})`; }

  // ── Layer model ────────────────────────────────────────────────────────────

  const city = () => MANIFEST.cities.find((c) => c.id === state.city);
  const allLayers = () => (city() ? [...city().layers, ...changeLayers()] : []);
  const layerDef = (id = state.layerId) => allLayers().find((l) => l.id === id) || null;
  /** The active labelling of the city: its own typology, another city's model or a pooled one. */
  const typo = () => {
    const c = city();
    return c ? c.typologies.find((t) => t.id === state.typology) || c.typologies[0] : null;
  };
  const ownTypo = () => city().typologies.find((t) => t.kind === "own") || null;
  /** Name of a label column (T_cluster, borderline, …) in a typology, by default the active one. */
  const lab = (name, t = typo()) => name + (t ? t.key : "");
  const blockCol = (block) => (block === "transport" ? "T_cluster" : "C_cluster");
  const clusterList = (block, t = typo()) => t.clusters[block];

  /** Layers that show, for another typology, which streets change class against the own one. */
  function changeLayers() {
    const t = typo();
    if (!t || !t.compare || !ownTypo()) return [];
    const by = t.kind === "pooled" ? "the pooled typology" : `the ${typoShort(t)}`;
    return ["transport", "context"].map((block) => ({
      id: block === "transport" ? "T_change" : "C_change", group: "compare", kind: "change", block,
      label: `${block === "transport" ? "Transport" : "Context"} class: own vs ${typoShort(t).toLowerCase() === "pooled" ? "pooled" : typoShort(t)}`,
      short: block === "transport" ? "Transport class" : "Context class",
      note: `Grey: the street lands where most streets of its own class land under ${by}. Dark: it lands in another class.`
        + (mergedClasses(block, t).size ? " Light: its class merges with a larger one, so the distinction is lost." : ""),
    }));
  }
  /** Own class -> the class of typology t where most of its streets land. */
  function classMap(block, t = typo()) {
    const cw = t.compare[block].crosswalk;
    const m = new Map();
    cw.rows.forEach((r, i) => {
      const counts = cw.counts[i];
      m.set(r, cw.cols[counts.indexOf(Math.max(...counts))]);
    });
    return m;
  }
  /** MapLibre pieces of a change layer: own class, new class, whether both exist, whether it moved. */
  /** Own classes that land, with most of their streets, in a class that a larger own class leads. */
  function mergedClasses(block, t = typo()) {
    const cw = t.compare[block].crosswalk, map = classMap(block, t);
    const lead = new Map();  // class of t -> own class bringing it most streets
    cw.rows.forEach((r, i) => {
      const to = map.get(r), n = cw.counts[i][cw.cols.indexOf(to)];
      if (!lead.has(to) || n > lead.get(to)[1]) lead.set(to, [r, n]);
    });
    return new Map(cw.rows.filter((r) => lead.get(map.get(r))[0] !== r).map((r) => [r, lead.get(map.get(r))[0]]));
  }
  function changeExpr(block) {
    const col = blockCol(block);
    const own = num(lab(col, ownTypo())), now = num(lab(col));
    const expected = ["match", own, ...[...classMap(block)].flat(), -99];
    const valid = ["all", [">=", own, 0], [">=", now, 0]];
    const merged = [...mergedClasses(block).keys()];
    const isMerged = merged.length ? ["match", own, merged, true, false] : false;
    const landed = ["all", valid, ["==", now, expected]];
    return { own, now, valid, changed: ["all", valid, ["!=", now, expected]],
             merged: ["all", landed, isMerged], same: ["all", landed, ["!", isMerged]] };
  }
  const clusterColors = (block, t = typo()) => {
    const list = clusterList(block, t).filter((c) => c.id >= 0);
    const colors = sample(block === "transport" ? BLUE_ORDINAL : ORANGE_ORDINAL, list.length);
    const map = new Map(list.map((c, i) => [c.id, colors[i]]));
    map.set(-1, COL.cNull);
    return map;
  };
  const transportWidths = (t = typo()) => {
    const list = clusterList("transport", t).filter((c) => c.id >= 0);
    const k = list.length;
    return new Map(list.map((c, i) => [c.id, k > 1 ? 0.7 + (1.7 * i) / (k - 1) : 1]));
  };
  function classColors(layer) {
    const ramp = layer.group === "context" ? SEQ_ORANGE : SEQ_BLUE;
    const n = layer.classes.length;
    if (n && layer.classes[0].label === "0") return [COL.zero, ...sample(ramp, n - 1)];
    return sample(ramp, n);
  }

  /** Legend entries of the active layer: {key, label, color, count, match(props)}. */
  function legendEntries(layer) {
    if (layer.kind === "numeric") {
      const colors = classColors(layer);
      return layer.classes.map((c, i) => {
        const hi = i + 1 < layer.classes.length ? layer.classes[i + 1].min : Infinity;
        return { key: i, label: c.label, color: colors[i], min: c.min, max: hi,
                 test: (p) => typeof p[layer.id] === "number" && p[layer.id] >= c.min && p[layer.id] < hi };
      });
    }
    if (layer.kind === "cluster") {
      const col = lab(blockCol(layer.block));
      const colors = clusterColors(layer.block);
      return clusterList(layer.block).map((c) => ({ key: c.id, label: c.name, color: colors.get(c.id), count: c.count,
                                                     profile: c.profile,
                                                     test: (p) => p[col] === c.id }));
    }
    if (layer.kind === "change") {
      const t = typo(), own = ownTypo(), col = blockCol(layer.block);
      const map = classMap(layer.block), cw = t.compare[layer.block].crosswalk;
      const ownOf = (p) => p[lab(col, own)], nowOf = (p) => p[lab(col, t)];
      const valid = (p) => ownOf(p) != null && nowOf(p) != null && ownOf(p) >= 0 && nowOf(p) >= 0;
      const merged = mergedClasses(layer.block, t);
      const same = { key: "same", label: "Same class", color: COL.confident, count: 0,
                     test: (p) => valid(p) && map.get(ownOf(p)) === nowOf(p) && !merged.has(ownOf(p)) };
      const merges = [], moves = [];
      cw.rows.forEach((r, i) => cw.cols.forEach((c, j) => {
        const n = cw.counts[i][j];
        if (!n) return;
        const [oc, on] = splitName(clusterName(layer.block, r, own));
        const [nc, nn] = splitName(clusterName(layer.block, c, t));
        const test = (p) => valid(p) && ownOf(p) === r && nowOf(p) === c;
        if (map.get(r) !== c) {
          moves.push({ key: `${r}>${c}`, label: `${oc} → ${nc}`, profile: `${on} → ${nn}`,
                       color: CHANGED[layer.block], count: n, test });
        } else if (merged.has(r)) {
          const lc = splitName(clusterName(layer.block, merged.get(r), own))[0];
          merges.push({ key: `${r}>${c}`, label: `${oc} merges with ${lc}`, profile: `${on} → ${nn}`,
                        color: MERGED[layer.block], count: n, test, kind: "merge" });
        } else {
          same.count += n;
        }
      }));
      const byCount = (a, b) => b.count - a.count;
      return [same, ...merges.sort(byCount), ...moves.sort(byCount)];
    }
    if (layer.kind === "borderline") {
      return [
        { key: true, label: "Borderline", color: COL.borderline, test: (p) => p[lab("borderline")] === true },
        { key: false, label: "Confident", color: COL.confident, test: (p) => p[lab("borderline")] === false },
      ];
    }
    return [];
  }

  // ── Map styling (MapLibre expressions) ─────────────────────────────────────

  const zoomWidth = (f) => {
    const m = (a) => (typeof f === "number" ? a * f : ["*", a, f]);
    return ["interpolate", ["exponential", 1.4], ["zoom"], 9, m(0.4), 12, m(1.1), 15, m(2.6), 18, m(7)];
  };
  const num = (col) => ["coalesce", ["get", col], -1];

  function isolateExpr(layer) {
    const iso = state.isolate;
    if (!iso) return null;
    if (layer.kind === "morphotype") {
      const parts = [];
      if (iso.T != null) parts.push(["==", num(lab("T_cluster")), iso.T]);
      if (iso.C != null) parts.push(["==", num(lab("C_cluster")), iso.C]);
      return ["all", ...parts];
    }
    if (layer.kind === "cluster") return ["==", num(lab(blockCol(layer.block))), iso.key];
    if (layer.kind === "borderline") return ["==", ["get", lab("borderline")], iso.key];
    if (layer.kind === "change") {
      const x = changeExpr(layer.block);
      if (iso.key === "same") return x.same;
      const [o, n] = iso.key.split(">").map(Number);
      return ["all", ["==", x.own, o], ["==", x.now, n]];
    }
    if (layer.kind === "numeric") {
      const e = legendEntries(layer)[iso.key];
      const v = ["get", layer.id];
      const conds = [["==", ["typeof", v], "number"], [">=", v, e.min]];
      if (Number.isFinite(e.max)) conds.push(["<", v, e.max]);
      return ["all", ...conds];
    }
    return null;
  }

  function layerStyle(layer) {
    let color, width, sort;
    if (layer.kind === "numeric") {
      const colors = classColors(layer);
      const steps = layer.classes.slice(1).flatMap((c, i) => [c.min, colors[i + 1]]);
      const v = ["get", layer.id];
      color = ["case", ["==", ["typeof", v], "number"], steps.length ? ["step", v, colors[0], ...steps] : colors[0], COL.none];
      width = zoomWidth(["case", ["==", ["typeof", v], "number"], 1, 0.6]);
      sort = num(layer.id);
    } else if (layer.kind === "cluster") {
      const col = lab(blockCol(layer.block));
      const colors = clusterColors(layer.block);
      color = ["match", num(col), ...[...colors].flat(), COL.none];
      width = zoomWidth(["case", ["has", col], 1, 0.6]);
      sort = num(col);
    } else if (layer.kind === "morphotype") {
      const colors = clusterColors("context");
      const widths = transportWidths();
      color = ["match", num(lab("C_cluster")), ...[...colors].flat(), COL.none];
      width = zoomWidth(["match", num(lab("T_cluster")), ...[...widths].flat(), 0.5]);
      sort = num(lab("T_cluster"));
    } else if (layer.kind === "change") {
      const x = changeExpr(layer.block);
      color = ["case", ["!", x.valid], COL.none, x.changed, CHANGED[layer.block], x.merged, MERGED[layer.block], COL.confident];
      width = zoomWidth(["case", x.changed, 1.7, x.merged, 1.3, 0.7]);
      sort = ["case", x.changed, 2, x.merged, 1, 0];
    } else {
      const b = lab("borderline");
      color = ["case", ["==", ["get", b], true], COL.borderline, ["has", b], COL.confident, COL.none];
      width = zoomWidth(["case", ["==", ["get", b], true], 1.3, 0.8]);
      sort = ["case", ["==", ["get", b], true], 1, 0];
    }
    const iso = isolateExpr(layer);
    let opacity = 0.95;
    if (iso) {
      color = ["case", iso, color, COL.dim];
      opacity = ["case", iso, 1, 0.55];
      sort = ["+", sort, ["case", iso, 10000, 0]];
    }
    return { color, width, sort, opacity };
  }

  // ── Map ────────────────────────────────────────────────────────────────────

  /** Raster XYZ basemap (e.g. CARTO Positron with a key): base tiles, and labels drawn above the data. */
  function rasterStyle(template) {
    const tpl = template.replace(/%7B/gi, "{").replace(/%7D/gi, "}");
    const tiles = (t) => (/^https:\/\/a\./.test(t) ? ["a", "b", "c", "d"].map((d) => t.replace("https://a.", `https://${d}.`)) : [t]);
    const attribution = '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors © <a href="https://carto.com/attributions">CARTO</a>';
    const style = {
      version: 8,
      sources: { base: { type: "raster", tiles: tiles(tpl), tileSize: 256, attribution, maxzoom: 20 } },
      layers: [{ id: "background", type: "background", paint: { "background-color": "#fafaf8" } },
               { id: "basemap", type: "raster", source: "base" }],
    };
    return style;
  }

  let usingFallback = !CFG.basemapTiles && !CFG.maptilerKey;
  const basemapStyle = () => {
    if (usingFallback) return CARTO_POSITRON;
    if (CFG.basemapTiles) return rasterStyle(CFG.basemapTiles);
    return `https://api.maptiler.com/maps/${encodeURIComponent(CFG.basemap)}/style.json?key=${encodeURIComponent(CFG.maptilerKey)}`;
  };

  const first = MANIFEST.cities[0];
  const map = new maplibregl.Map({
    container: "map",
    style: basemapStyle(),
    center: first ? [(first.bounds[0] + first.bounds[2]) / 2, (first.bounds[1] + first.bounds[3]) / 2] : [20, 45],
    zoom: first ? 10 : 2,
    attributionControl: { compact: true },
    dragRotate: false,
    pitchWithRotate: false,
  });
  map.touchZoomRotate.disableRotation();
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
  map.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-left");

  const isLocal = location.protocol === "file:" || ["localhost", "127.0.0.1", ""].includes(location.hostname);
  function showBasemapNote() {
    const note = $("basemap-note");
    const configured = CFG.basemapTiles || CFG.maptilerKey;
    if (usingFallback) console.warn("Street Morphotypes: basemap key missing or rejected, using the keyless CARTO Positron.");
    note.hidden = !(usingFallback && isLocal);
    note.textContent = configured
      ? "Basemap key rejected: showing the keyless CARTO Positron. Check web/config.js."
      : "No basemap key: showing the keyless CARTO Positron. Add it in web/config.js.";
  }
  showBasemapNote();

  map.on("error", (e) => {
    const status = e && e.error && e.error.status;
    if (!usingFallback && (status === 401 || status === 403)) {
      usingFallback = true;
      map.setStyle(CARTO_POSITRON);
      showBasemapNote();
    }
  });

  /** (Re)create sources and layers: on first load and after every basemap change. */
  map.on("style.load", () => {
    const empty = { type: "FeatureCollection", features: [] };
    map.addSource("area", { type: "geojson", data: (state.data && state.data.area) || empty });
    map.addSource("segments", { type: "geojson", data: (state.data && state.data.segments) || empty });
    // No basemap labels: the streets are the subject (vector fallback styles carry them as symbol layers).
    for (const l of map.getStyle().layers) {
      if (l.type === "symbol") map.setLayoutProperty(l.id, "visibility", "none");
    }
    const before = undefined;
    map.addLayer({ id: "area-line", type: "line", source: "area",
                   paint: { "line-color": "#898781", "line-width": 1.2, "line-dasharray": [3, 2], "line-opacity": 0.7 } }, before);
    map.addLayer({ id: "segments", type: "line", source: "segments", layout: { "line-cap": "round", "line-join": "round" } }, before);
    map.addLayer({ id: "seg-hover", type: "line", source: "segments", filter: ["==", ["id"], -1],
                   layout: { "line-cap": "round" }, paint: { "line-color": "#0b0b0b", "line-width": zoomWidth(2.2), "line-opacity": 0.45 } }, before);
    map.addLayer({ id: "seg-select", type: "line", source: "segments", filter: ["==", ["id"], -1],
                   layout: { "line-cap": "round" }, paint: { "line-color": "#0b0b0b", "line-width": zoomWidth(2.6) } }, before);
    paintMap();
    setFilters();
  });

  function paintMap() {
    const layer = layerDef();
    if (!layer || !map.getLayer("segments")) return;
    const s = layerStyle(layer);
    map.setPaintProperty("segments", "line-color", s.color);
    map.setPaintProperty("segments", "line-width", s.width);
    map.setPaintProperty("segments", "line-opacity", s.opacity);
    map.setLayoutProperty("segments", "line-sort-key", s.sort);
  }
  function setFilters() {
    if (!map.getLayer("seg-hover")) return;
    map.setFilter("seg-hover", ["==", ["id"], state.hover == null ? -1 : state.hover]);
    map.setFilter("seg-select", ["==", ["id"], state.selected == null ? -1 : state.selected]);
  }

  const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 10, maxWidth: "280px" });
  map.on("mousemove", "segments", (e) => {
    const f = e.features[0];
    map.getCanvas().style.cursor = "pointer";
    if (state.hover !== f.id) { state.hover = f.id; setFilters(); }
    const p = state.byId.get(f.id) || f.properties;
    const box = el("div");
    box.append(el("div", "tip-name", p.name || "Unnamed street"), el("div", "tip-val", hoverValue(p)));
    popup.setLngLat(e.lngLat).setDOMContent(box).addTo(map);
  });
  map.on("mouseleave", "segments", () => {
    map.getCanvas().style.cursor = "";
    state.hover = null;
    setFilters();
    popup.remove();
  });
  map.on("click", (e) => {
    const hit = map.getLayer("segments") ? map.queryRenderedFeatures(e.point, { layers: ["segments"] })[0] : null;
    state.selected = hit ? hit.id : null;
    setFilters();
    renderDetails();
  });

  // ── Formatting ─────────────────────────────────────────────────────────────

  function fmt(v, kind) {
    if (typeof v !== "number") return "—";
    if (kind === "pct") return `${Math.round(v * 100)}%`;
    if (kind === "int" || Math.abs(v) >= 100) return Math.round(v).toLocaleString("en-US").replace(/,/g, " ");
    return Number(v.toPrecision(3)).toString();
  }
  const pct = (v) => (typeof v === "number" ? `${Math.round(v * 100)}%` : "—");
  const splitName = (name) => {
    const i = name.indexOf(" · ");
    return i < 0 ? [name, ""] : [name.slice(0, i), name.slice(i + 3)];
  };
  const clusterName = (block, id, t = typo()) => {
    const c = clusterList(block, t).find((x) => x.id === id);
    return c ? c.name : "—";
  };

  function hoverValue(p) {
    const layer = layerDef();
    if (!layer) return "";
    if (layer.kind === "numeric") return `${layer.short}: ${fmt(p[layer.id], layer.format)}`;
    if (layer.kind === "cluster") {
      const col = lab(blockCol(layer.block));
      return p[col] == null ? "not classified" : clusterName(layer.block, p[col]);
    }
    if (layer.kind === "change") {
      const col = blockCol(layer.block), o = p[lab(col, ownTypo())], n = p[lab(col)];
      if (o == null || n == null || o < 0 || n < 0) return "not classified";
      const own = clusterName(layer.block, o, ownTypo()), now = clusterName(layer.block, n);
      if (classMap(layer.block).get(o) !== n) return `${own} → ${now}`;
      return mergedClasses(layer.block).has(o) ? `merged: ${own} → ${now}` : `same class: ${now}`;
    }
    const b = p[lab("borderline")];
    if (layer.kind === "borderline") return b == null ? "not classified" : b ? "borderline" : "confident";
    return p[lab("morphotype")] || "not classified";
  }

  // ── Sidebar: cities ────────────────────────────────────────────────────────

  function renderCities() {
    const box = $("cities");
    box.replaceChildren();
    if (!MANIFEST.cities.length) {
      const p = el("p", "empty");
      p.append("No results yet. Run ", el("code", null, "street-morphotypes run configs/<city>.yaml"),
               " and reload: the map picks up every run in ", el("code", null, "outputs/"), ".");
      box.append(p);
      return;
    }
    for (const c of MANIFEST.cities) {
      const b = el("button", "city");
      b.type = "button";
      b.setAttribute("role", "radio");
      b.setAttribute("aria-checked", String(c.id === state.city));
      b.append(el("span", "city-name", c.label));
      b.title = `${c.label}: ${c.stats.segments.toLocaleString("en-US")} street segments`;
      b.addEventListener("click", () => selectCity(c.id));
      box.append(b);
    }
  }

  // ── Sidebar: typology ──────────────────────────────────────────────────────

  const TYPO_SHORT = { own: "Own", pooled: "Pooled" };
  function typoShort(t) {
    return t.kind === "model" ? `${t.trained_on_labels.join(" + ")} model` : TYPO_SHORT[t.kind];
  }
  function typoDescription(t) {
    const c = city();
    if (t.kind === "own") return `Classes found in ${c.label} itself: what is typical for this city.`;
    if (t.kind === "model") {
      return `${c.label} measured by ${t.trained_on_labels.join(" + ")}'s classes: does the typology carry over?`;
    }
    return `One set of classes fitted on ${t.trained_on_labels.join(" + ")} together, the same in every city.`;
  }

  function renderTypologies() {
    const block = $("typology-block");
    const c = city();
    block.hidden = !c || c.typologies.length < 2;
    if (block.hidden) return;
    const box = $("typologies");
    box.replaceChildren();
    for (const t of c.typologies) {
      const b = el("button", "seg-btn", typoShort(t));
      b.type = "button";
      b.setAttribute("role", "radio");
      b.setAttribute("aria-checked", String(t === typo()));
      b.title = t.label;
      b.addEventListener("click", () => selectTypology(t.id));
      box.append(b);
    }
    $("typology-note").textContent = typoDescription(typo());
  }

  // ── Sidebar: layers ────────────────────────────────────────────────────────

  function renderLayers() {
    const nav = $("layers");
    nav.replaceChildren();
    const c = city();
    if (!c) return;
    for (const g of GROUPS) {
      const layers = allLayers().filter((l) => l.group === g.id);
      if (!layers.length) continue;
      const sec = el("section", `layer-group grp-${g.id}`);
      sec.append(el("h2", "block-title", g.title));

      for (let i = 0; i < layers.length; i++) {
        const l = layers[i];
        if (l.family === "fn") {  // floor-area shares: a sub-heading and one row per function
          const fam = layers.filter((x) => x.family === "fn");
          i += fam.length - 1;
          sec.append(el("div", "subhead", l.family_label));
          for (const x of fam) sec.append(layerRow(x, x.chip.charAt(0).toUpperCase() + x.chip.slice(1), "indent"));
        } else if (l.chip) {
          const fam = layers.filter((x) => x.family === l.family && x.chip);
          i += fam.length - 1;
          const row = el("div", "family");
          const dot = el("span", "model-dot" + (fam.some((x) => x.in_model) ? "" : " off"));
          const chips = el("div", "chips");
          for (const x of fam) {
            const chip = el("button", "chip" + (x.in_model ? "" : " off"), x.chip);
            chip.type = "button";
            chip.title = x.label + (x.in_model ? " — used in clustering" : " — not used in clustering");
            chip.setAttribute("aria-pressed", String(x.id === state.layerId));
            chip.addEventListener("click", () => selectLayer(x.id));
            chips.append(chip);
          }
          const tipKey = { ss_nain: "nain", ss_nach: "nach" }[l.family];
          const lbl = el("span", "lbl");
          lbl.append(tipKey ? term(l.family_label.split(" · ")[0], tipKey) : l.family_label.split(" · ")[0]);
          row.append(dot, lbl, chips);
          sec.append(row);
        } else {
          sec.append(layerRow(l, l.short || l.label));
        }
      }
      nav.append(sec);
    }
  }

  function layerRow(l, text, cls = "") {
    const b = el("button", `layer-row ${cls}`.trim());
    b.type = "button";
    b.setAttribute("aria-pressed", String(l.id === state.layerId));
    b.title = l.kind === "numeric" ? l.label + (l.in_model ? " — used in clustering" : " — not used in clustering") : l.label;
    if (l.kind === "numeric") b.append(el("span", "model-dot" + (l.in_model ? "" : " off")));
    b.append(el("span", "lbl", text));
    b.addEventListener("click", () => selectLayer(l.id));
    return b;
  }

  // ── Right panel: legend ────────────────────────────────────────────────────

  function lineSwatch(color, h = 4) {
    const s = el("span", "line-swatch");
    s.style.background = color;
    s.style.height = `${h}px`;
    return s;
  }

  function renderLegend() {
    const layer = layerDef();
    const box = $("legend");
    box.replaceChildren();
    $("legend-reset").hidden = !state.isolate;
    if (!layer) {
      $("legend-title").textContent = "No data";
      $("legend-note").textContent = "";
      return;
    }
    $("legend-title").textContent = layer.label;
    const note = $("legend-note");
    note.className = `legend-note grp-${layer.group}`;
    note.replaceChildren(layer.note || "");
    if (layer.group === "morphotypes" && typo().kind !== "own") {
      note.append(el("span", "typo-badge", typo().kind === "pooled" ? "Classes of the pooled typology."
                                                                       : `Classes of the ${typoShort(typo())}.`));
    }
    if (layer.kind === "numeric") {
      const badge = el("span", "badge" + (layer.in_model ? "" : " off"),
                       layer.in_model ? "Used in clustering" : layer.excluded_reason);
      note.append(badge);
    }
    if (layer.kind === "change") {
      const entries = legendEntries(layer);
      const total = entries.reduce((n, e) => n + e.count, 0) || 1;
      const sum = (pred) => entries.filter(pred).reduce((n, e) => n + e.count, 0);
      const moved = sum((e) => e.key !== "same" && e.kind !== "merge"), merged = sum((e) => e.kind === "merge");
      const stat = el("span", "change-stat");
      stat.append(el("b", null, pct(moved / total)), " of the classified streets change class");
      if (merged) stat.append(", ", el("b", null, pct(merged / total)), " lose their own class in a merge");
      stat.append(" · ", term("agreement", "ari"), " ", el("b", null, typo().compare[layer.block].ari.toFixed(2)));
      note.append(stat);
    }
    if (layer.kind === "morphotype") return renderMatrix(box);

    const entries = legendEntries(layer);
    const feats = state.data ? state.data.segments.features : [];
    const list = el("div", "legend-items");
    for (const e of entries) {
      const count = e.count != null ? e.count : feats.reduce((n, f) => n + (e.test(f.properties) ? 1 : 0), 0);
      const item = el("button", "legend-item");
      item.type = "button";
      if (state.isolate && state.isolate.key !== e.key) item.classList.add("dim");
      const [code, rest] = layer.kind === "cluster" ? splitName(e.label) : [e.label, ""];
      const name = el("span", "name");
      if (rest) name.append(el("span", "code", code), ` ${rest}`);
      else if (layer.kind === "change") name.append(el("span", "code", code));
      else name.append(code);
      if (e.profile) name.append(el("span", "profile", e.profile));
      item.append(lineSwatch(e.color), name, el("span", "count", count.toLocaleString("en-US")));
      item.title = layer.kind === "change" ? "Show only these streets" : "Show only this class";
      item.addEventListener("click", () => toggleIsolate({ key: e.key }));
      list.append(item);
    }
    const missing = feats.filter((f) => !entries.some((e) => e.test(f.properties))).length;
    if (missing) {
      const item = el("div", "legend-item");
      item.append(lineSwatch(COL.none), el("span", "name", "No data / not classified"),
                  el("span", "count", missing.toLocaleString("en-US")));
      list.append(item);
    }
    box.append(list);
  }

  function renderMatrix(box) {
    const tList = clusterList("transport").filter((x) => x.id >= 0);
    const cList = clusterList("context");
    const cColors = clusterColors("context");
    const widths = transportWidths();
    const morph = typo().morphotypes;
    const max = Math.max(1, ...Object.values(morph).map((m) => m.count));
    const iso = state.isolate || {};
    const grid = el("div", "matrix");
    grid.style.gridTemplateColumns = `48px repeat(${cList.length}, minmax(0, 1fr))`;

    grid.append(el("span"));
    for (const cc of cList) {
      const h = el("button", "hdr");
      h.type = "button";
      const code = cc.id < 0 ? "null" : `C${cc.id}`;
      h.append(lineSwatch(cColors.get(cc.id)), code);
      h.title = `${cc.name} — show this context class`;
      if (iso.C != null && iso.C !== cc.id) h.classList.add("dim");
      h.addEventListener("click", () => toggleIsolate({ C: cc.id }));
      h.addEventListener("mouseenter", () => setCaption(null, null, cc));
      h.addEventListener("mouseleave", () => setCaption());
      grid.append(h);
    }
    for (const t of tList) {
      const h = el("button", "hdr row-hdr");
      h.type = "button";
      h.append(lineSwatch("#52514e", 1.5 * widths.get(t.id) + 1), `T${t.id}`);
      h.title = `${t.name} — show this transport class`;
      if (iso.T != null && iso.T !== t.id) h.classList.add("dim");
      h.addEventListener("click", () => toggleIsolate({ T: t.id }));
      h.addEventListener("mouseenter", () => setCaption(null, null, t));
      h.addEventListener("mouseleave", () => setCaption());
      grid.append(h);
      for (const cc of cList) {
        const code = `T${t.id}-${cc.id < 0 ? "C_null" : `C${cc.id}`}`;
        const m = morph[code];
        const cell = el("button", "cell", m ? m.count.toLocaleString("en-US") : "·");
        cell.type = "button";
        if (!m) {
          cell.classList.add("empty-cell");
          cell.disabled = true;
        } else {
          const a = 0.12 + 0.88 * Math.sqrt(m.count / max);
          cell.style.background = rgba(cColors.get(cc.id), a);
          cell.style.color = a > 0.6 && cc.id >= 2 ? "#fff" : "#0b0b0b";
          cell.title = `${code} · ${m.count} segments\n${m.name}`;
          cell.addEventListener("click", () => toggleIsolate({ T: t.id, C: cc.id }));
          cell.addEventListener("mouseenter", () => setCaption(code, m));
          cell.addEventListener("mouseleave", () => setCaption());
        }
        const isActive = iso.T === t.id && iso.C === cc.id;
        if (isActive) cell.classList.add("active");
        else if ((iso.T != null && iso.T !== t.id) || (iso.C != null && iso.C !== cc.id)) cell.classList.add("dim");
        grid.append(cell);
      }
    }
    const caption = el("p", "matrix-caption");
    caption.id = "matrix-caption";
    box.append(grid, caption);
    setCaption();

  }

  /** Text under the matrix: a hovered morphotype or class, else the isolated one, else a hint. */
  function setCaption(code, m, cls) {
    const cap = $("matrix-caption");
    if (!cap) return;
    cap.replaceChildren();
    const iso = state.isolate;
    if (!code && !cls && iso) {
      if (iso.T != null && iso.C != null) {
        code = `T${iso.T}-${iso.C < 0 ? "C_null" : `C${iso.C}`}`;
        m = typo().morphotypes[code];
      } else {
        cls = iso.T != null ? clusterList("transport").find((x) => x.id === iso.T)
                            : clusterList("context").find((x) => x.id === iso.C);
      }
    }
    if (cls) {
      const [head, rest] = splitName(cls.name);
      cap.append(el("b", null, `${head} · ${rest}`), el("br"),
                 `${cls.count.toLocaleString("en-US")} segments` + (cls.profile ? ` · ${cls.profile}` : ""));
    } else if (code && m) {
      cap.append(el("b", null, `${code} · ${m.count.toLocaleString("en-US")} segments`), el("br"), m.name);
    }
  }

  function toggleIsolate(next) {
    const same = state.isolate && JSON.stringify(state.isolate) === JSON.stringify(next);
    state.isolate = same ? null : next;
    paintMap();
    renderLegend();
  }

  // ── Right panel: segment details ───────────────────────────────────────────

  function renderDetails() {
    const box = $("details");
    box.replaceChildren();
    const p = state.selected != null ? state.byId.get(state.selected) : null;
    if (!p) {
      box.append(el("p", "placeholder", "Click a street segment to see its values."));
      return;
    }
    box.append(el("h2", "seg-name", p.name || "Unnamed street"));
    const sub = [p.highway ? `highway=${p.highway}` : null, typeof p.length === "number" ? `${Math.round(p.length)} m` : null, `segment ${p.seg_id}`];
    box.append(el("p", "seg-sub", sub.filter(Boolean).join(" · ")));

    const types = el("div", "seg-types");
    const own = ownTypo();
    const shown = own && own !== typo() ? [typo(), own] : [typo()];
    for (const t of shown) {
      if (shown.length > 1) types.append(el("p", "seg-typo", t === own ? "Own typology" : t.label));
      const tc = p[lab("T_cluster", t)], cc = p[lab("C_cluster", t)];
      if (tc != null) {
        const row = el("div", "seg-type");
        row.append(lineSwatch(clusterColors("transport", t).get(tc), 1.5 * transportWidths(t).get(tc) + 1),
                   el("span", null, clusterName("transport", tc, t)), el("span", "conf", confidence(p[lab("T_confidence", t)])));
        types.append(row);
      }
      if (cc != null) {
        const row = el("div", "seg-type");
        row.append(lineSwatch(clusterColors("context", t).get(cc)),
                   el("span", null, clusterName("context", cc, t)), el("span", "conf", confidence(p[lab("C_confidence", t)])));
        types.append(row);
      }
      if (tc == null) {
        types.append(el("p", "placeholder", "Not classified (outside the clustered network)."));
        break;
      }
    }
    box.append(types);

    const dl = el("dl", "values");
    for (const g of GROUPS.slice(0, 2)) {
      const layers = city().layers.filter((l) => l.group === g.id && l.kind === "numeric");
      if (!layers.length) continue;
      dl.append(el("dt", "sub", g.title));
      for (const l of layers) {
        const dt = el("dt", null, l.chip ? `${l.family_label.split(" · ")[0]} ${l.family === "fn" ? l.chip : l.chip === "Rn" ? "Rn" : `${l.chip} m`}` : l.short);
        const dd = el("dd", null, fmt(p[l.id], l.format));
        if (p[`${l.id}_imputed`]) dd.append(el("span", "imp", " (default)"));
        if (l.id === state.layerId) { dt.classList.add("active", `grp-${g.id}`); dd.classList.add("active", `grp-${g.id}`); }
        dl.append(dt, dd);
      }
    }
    box.append(dl);
  }
  const confidence = (v) => (typeof v === "number" ? `${Math.round(v * 100)}%` : "");

  // ── Right panel: city facts ────────────────────────────────────────────────

  function renderFacts() {
    const c = city();
    const dl = $("facts");
    dl.replaceChildren();
    if (!c) { $("facts-title").textContent = "City"; return; }
    const s = { ...c.stats, ...typo().stats };
    $("facts-title").textContent = `${c.label} · ${typo().kind === "own" ? "own typology" : typo().label}`;
    const sil = (b) => (s.mean_silhouette[b] != null ? s.mean_silhouette[b].toFixed(2) : "—");
    const facts = [
      ["Segments classified", "classified", `${s.classified.toLocaleString("en-US")}`, ` / ${s.segments.toLocaleString("en-US")}`],
      ["Classes T × C", "k", `${s.k.transport ?? "—"} × ${s.k.context ?? "—"}`, ""],
      ["Silhouette T / C", "silhouette", `${sil("transport")} / ${sil("context")}`, ""],
      ["Borderline", "borderline", pct(s.borderline / Math.max(1, s.classified)), ` · ${s.borderline.toLocaleString("en-US")}`],
      ["Lanes / speed from defaults", "defaults", `${pct(s.lanes_imputed_share)} / ${pct(s.maxspeed_imputed_share)}`, ""],
      ["Floor area, unknown use", "unknown", pct(s.unknown_function_share), ""],
    ];
    for (const [k, tip, v, small] of facts) {
      const d = el("div");
      const dd = el("dd", null, v);
      if (small) dd.append(el("small", null, small));
      const dt = el("dt");
      dt.append(term(k, tip));
      d.append(dt, dd);
      dl.append(d);
    }
  }

  // ── Selection & URL ────────────────────────────────────────────────────────

  function selectTypology(id) {
    const wasOwn = typo().kind === "own";
    state.typology = id;
    state.isolate = null;
    // the point of another typology is the difference: show it, unless a metric layer is open
    if (typo().kind !== "own" && wasOwn && (!layerDef() || layerDef().kind !== "numeric")) state.layerId = "C_change";
    if (!layerDef()) state.layerId = DEFAULT_LAYER;
    paintMap();
    renderTypologies();
    renderLayers();
    renderLegend();
    renderDetails();
    renderFacts();
    writeHash();
  }

  function selectLayer(id) {
    if (!layerDef(id)) id = DEFAULT_LAYER;
    state.layerId = id;
    state.isolate = null;
    paintMap();
    renderLayers();
    renderLegend();
    renderDetails();
    writeHash();
  }

  function loadCityData(c) {
    if (window.SM_DATA && window.SM_DATA[c.id]) return Promise.resolve(window.SM_DATA[c.id]);
    return new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = `${c.file}?v=${c.version}`;
      s.onload = () => (window.SM_DATA && window.SM_DATA[c.id] ? resolve(window.SM_DATA[c.id]) : reject(new Error("empty")));
      s.onerror = () => reject(new Error(`cannot load ${c.file}`));
      document.head.append(s);
    });
  }

  let loading = 0;
  async function selectCity(id, { fit = true } = {}) {
    const c = MANIFEST.cities.find((x) => x.id === id) || MANIFEST.cities[0];
    if (!c) return;
    const ticket = ++loading;
    const kind = state.typologyKind || (typo() ? typo().kind : "own");  // keep own / model / pooled across cities
    state.typologyKind = null;
    state.city = c.id;
    state.typology = (c.typologies.find((t) => t.kind === kind) || c.typologies[0]).id;
    state.selected = state.hover = null;
    state.isolate = null;
    renderCities();
    const status = $("map-status");
    status.hidden = false;
    status.textContent = `Loading ${c.label}…`;
    let data;
    try {
      data = await loadCityData(c);
    } catch (err) {
      status.textContent = `Could not load ${c.label}: run \`street-morphotypes web\` again.`;
      return;
    }
    if (ticket !== loading) return; // another city was chosen meanwhile
    status.hidden = true;
    state.data = data;
    state.byId = new Map(data.segments.features.map((f) => [f.id, f.properties]));
    if (map.getSource("segments")) {
      map.getSource("segments").setData(data.segments);
      map.getSource("area").setData(data.area || { type: "FeatureCollection", features: [] });
    }
    if (fit) fitCity(c);
    if (!layerDef(state.layerId)) state.layerId = DEFAULT_LAYER;
    paintMap();
    setFilters();
    renderTypologies();
    renderLayers();
    renderLegend();
    renderDetails();
    renderFacts();
    writeHash();
  }

  let mapReady = false;
  map.once("load", () => { mapReady = true; });
  function fitCity(c) {
    const go = () => map.fitBounds(c.bounds, { padding: 30, duration: 0 });
    if (mapReady) go(); else map.once("load", go);
  }

  function readHash() {
    const h = new URLSearchParams(location.hash.slice(1));
    return { city: h.get("city"), layer: h.get("layer"), typology: h.get("typology") };
  }
  function writeHash() {
    if (!state.city) return;
    const t = typo();
    const extra = t && t.kind !== "own" ? `&typology=${t.kind}` : "";
    history.replaceState(null, "", `#city=${encodeURIComponent(state.city)}&layer=${encodeURIComponent(state.layerId)}${extra}`);
  }

  // ── Start ──────────────────────────────────────────────────────────────────

  // The author's byline and the Irkutsk-Wrocław findings describe that study only: with other runs they go.
  const CASE_STUDY = ["irkutsk", "wroclaw"];
  if (!CASE_STUDY.every((id) => MANIFEST.cities.some((c) => c.id === id))) {
    document.querySelectorAll("[data-case-study]").forEach((n) => n.remove());
  }

  $("legend-reset").addEventListener("click", () => toggleIsolate(state.isolate));
  const repo = document.getElementById("repo-link");
  if (CFG.repoUrl) {
    repo.href = CFG.repoUrl;
    const a = el("a", null, "on GitHub");
    a.href = `${CFG.repoUrl.replace(/\/$/, "")}/blob/main/docs/METHODOLOGY.md`;
    a.target = "_blank";
    a.rel = "noopener";
    $("about-repo").append(" (", a, ")");
  } else {
    repo.closest("footer").remove();
  }

  // About dialog: "?" opens it; the close button, Esc or a click outside closes it; #about opens it directly.
  const about = $("about");
  let lastFocus = null;
  function openAbout() {
    lastFocus = document.activeElement;
    about.hidden = false;
    toggleTip(null);
    about.querySelector(".about-inner").focus();
  }
  function closeAbout() {
    about.hidden = true;
    if (lastFocus) lastFocus.focus();
  }
  $("about-open").addEventListener("click", openAbout);
  $("about-close").addEventListener("click", closeAbout);
  about.addEventListener("click", (e) => { if (e.target === about) closeAbout(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !about.hidden) closeAbout(); });

  // One floating tooltip for every glossary term (the panels would clip a CSS-only tooltip).
  const tip = $("tip");
  function showTip(t) {
    tip.textContent = t.dataset.tip;
    tip.hidden = false;
    const r = t.getBoundingClientRect(), w = tip.offsetWidth, h = tip.offsetHeight;
    tip.style.left = `${Math.min(Math.max(8, r.left), window.innerWidth - w - 8)}px`;
    tip.style.top = `${r.bottom + 6 + h > window.innerHeight ? r.top - h - 6 : r.bottom + 6}px`;
  }
  let tipFor = null;
  const tipTarget = (e) => (e.target.closest ? e.target.closest("[data-tip]") : null);
  function toggleTip(t) {
    if (t && t !== tipFor) { showTip(t); tipFor = t; } else { tip.hidden = true; tipFor = null; }
  }
  document.addEventListener("click", (e) => toggleTip(tipTarget(e)));
  document.addEventListener("keydown", (e) => {
    const t = tipTarget(e);
    if (t && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); toggleTip(t); }
    if (e.key === "Escape") toggleTip(null);
  });
  window.addEventListener("resize", () => toggleTip(null));
  if (location.hash === "#about") openAbout();

  const initial = readHash();
  if (initial.layer) state.layerId = initial.layer;
  if (initial.typology) state.typologyKind = initial.typology;
  renderCities();
  renderLegend();
  renderFacts();
  if (MANIFEST.cities.length) {
    const startCity = MANIFEST.cities.some((c) => c.id === initial.city) ? initial.city : MANIFEST.cities[0].id;
    selectCity(startCity);
  }
})();
