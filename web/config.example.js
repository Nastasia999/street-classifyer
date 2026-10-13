// Web map settings. Copy this file to config.js and fill it in.
//
// config.js is ignored by git. On GitHub Pages it is written by
// .github/workflows/pages.yml from the repository secrets
// (Settings -> Secrets and variables -> Actions).
//
// Basemap, first match wins:
//   basemapTiles  raster XYZ template with your key, e.g. CARTO Positron:
//                 https://a.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}@2x.png?key=...
//   maptilerKey   a MapTiler key; the "positron" map is used
//   neither       the keyless CARTO Positron vector style
// A browser key is visible to every visitor: restrict it to your domains in the provider's console.
window.SM_CONFIG = {
  basemapTiles: "",
  maptilerKey: "",
  repoUrl: "", // e.g. https://github.com/<user>/street-morphotypes
};
