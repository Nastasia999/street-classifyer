window.SM_MANIFEST = {
 "generated": "2026-10-13T21:50:07+00:00",
 "output_root": "outputs",
 "cities": [
  {
   "id": "irkutsk",
   "label": "Irkutsk",
   "run": "irkutsk",
   "mode": "local",
   "trained_on": [
    "irkutsk"
   ],
   "file": "data/cities/irkutsk.js",
   "version": 1791926913,
   "bounds": [
    104.0667,
    52.20975,
    104.44439,
    52.40725
   ],
   "stats": {
    "segments": 4385,
    "classified": 4186,
    "borderline": 750,
    "k": {
     "transport": 4,
     "context": 6
    },
    "mean_silhouette": {
     "transport": 0.4134,
     "context": 0.5859
    },
    "lanes_imputed_share": 0.582,
    "maxspeed_imputed_share": 0.605,
    "unknown_function_share": 0.076
   },
   "clusters": {
    "transport": [
     {
      "id": 0,
      "name": "T0 · Local access street",
      "count": 711,
      "profile": "low through-movement Rn, low integration R800 m"
     },
     {
      "id": 1,
      "name": "T1 · Ordinary street",
      "count": 2537,
      "profile": "close to the city median on every feature"
     },
     {
      "id": 2,
      "name": "T2 · Public transport street with stops",
      "count": 291,
      "profile": "high PT stops, high PT routes"
     },
     {
      "id": 3,
      "name": "T3 · Public transport arterial",
      "count": 647,
      "profile": "high PT routes, high lanes"
     }
    ],
    "context": [
     {
      "id": 0,
      "name": "C0 · Residential street without services",
      "count": 2322,
      "profile": "close to the city median on every feature"
     },
     {
      "id": 1,
      "name": "C1 · Commercial roadside with set-back buildings",
      "count": 180,
      "profile": "high commercial, high greenery"
     },
     {
      "id": 2,
      "name": "C2 · Green street with sparse buildings",
      "count": 570,
      "profile": "high greenery, low residential"
     },
     {
      "id": 3,
      "name": "C3 · Residential street with services",
      "count": 309,
      "profile": "high organisations, high commercial, high social"
     },
     {
      "id": 4,
      "name": "C4 · Green mixed-use street",
      "count": 307,
      "profile": "high greenery, high organisations"
     },
     {
      "id": 5,
      "name": "C5 · Commercial high street",
      "count": 262,
      "profile": "high commercial, high organisations, low residential"
     },
     {
      "id": -1,
      "name": "C_null · no reliable building data",
      "count": 236
     }
    ]
   },
   "order_by": {
    "transport": {
     "id": "ss_nach_n",
     "label": "through-movement Rn"
    },
    "context": {
     "id": "poi_per_100m",
     "label": "organisations"
    }
   },
   "morphotypes": {
    "T0-C0": {
     "count": 458,
     "name": "Local access street | Residential street without services"
    },
    "T0-C1": {
     "count": 15,
     "name": "Local access street | Commercial roadside with set-back buildings"
    },
    "T0-C2": {
     "count": 93,
     "name": "Local access street | Green street with sparse buildings"
    },
    "T0-C3": {
     "count": 41,
     "name": "Local access street | Residential street with services"
    },
    "T0-C4": {
     "count": 30,
     "name": "Local access street | Green mixed-use street"
    },
    "T0-C5": {
     "count": 22,
     "name": "Local access street | Commercial high street"
    },
    "T0-C_null": {
     "count": 52,
     "name": "Local access street | no reliable building data"
    },
    "T1-C0": {
     "count": 1633,
     "name": "Ordinary street | Residential street without services"
    },
    "T1-C1": {
     "count": 72,
     "name": "Ordinary street | Commercial roadside with set-back buildings"
    },
    "T1-C2": {
     "count": 291,
     "name": "Ordinary street | Green street with sparse buildings"
    },
    "T1-C3": {
     "count": 172,
     "name": "Ordinary street | Residential street with services"
    },
    "T1-C4": {
     "count": 138,
     "name": "Ordinary street | Green mixed-use street"
    },
    "T1-C5": {
     "count": 108,
     "name": "Ordinary street | Commercial high street"
    },
    "T1-C_null": {
     "count": 123,
     "name": "Ordinary street | no reliable building data"
    },
    "T2-C0": {
     "count": 86,
     "name": "Public transport street with stops | Residential street without services"
    },
    "T2-C1": {
     "count": 20,
     "name": "Public transport street with stops | Commercial roadside with set-back buildings"
    },
    "T2-C2": {
     "count": 29,
     "name": "Public transport street with stops | Green street with sparse buildings"
    },
    "T2-C3": {
     "count": 44,
     "name": "Public transport street with stops | Residential street with services"
    },
    "T2-C4": {
     "count": 53,
     "name": "Public transport street with stops | Green mixed-use street"
    },
    "T2-C5": {
     "count": 48,
     "name": "Public transport street with stops | Commercial high street"
    },
    "T2-C_null": {
     "count": 11,
     "name": "Public transport street with stops | no reliable building data"
    },
    "T3-C0": {
     "count": 145,
     "name": "Public transport arterial | Residential street without services"
    },
    "T3-C1": {
     "count": 73,
     "name": "Public transport arterial | Commercial roadside with set-back buildings"
    },
    "T3-C2": {
     "count": 157,
     "name": "Public transport arterial | Green street with sparse buildings"
    },
    "T3-C3": {
     "count": 52,
     "name": "Public transport arterial | Residential street with services"
    },
    "T3-C4": {
     "count": 86,
     "name": "Public transport arterial | Green mixed-use street"
    },
    "T3-C5": {
     "count": 84,
     "name": "Public transport arterial | Commercial high street"
    },
    "T3-C_null": {
     "count": 50,
     "name": "Public transport arterial | no reliable building data"
    }
   },
   "layers": [
    {
     "id": "ss_nain_n",
     "group": "transport",
     "kind": "numeric",
     "format": "num",
     "family": "ss_nain",
     "family_label": "Integration · NAIN",
     "chip": "Rn",
     "label": "NAIN (normalised angular integration), Rn",
     "short": "Integration Rn",
     "note": "Normalised angular integration: how easy the segment is to reach from everywhere within the radius (to-movement).",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.61931270728794,
       "label": "< 1.01"
      },
      {
       "min": 1.01,
       "label": "1.01 – 1.1"
      },
      {
       "min": 1.1,
       "label": "1.1 – 1.19"
      },
      {
       "min": 1.19,
       "label": "1.19 – 1.29"
      },
      {
       "min": 1.29,
       "label": "≥ 1.29"
      }
     ]
    },
    {
     "id": "ss_nain_800",
     "group": "transport",
     "kind": "numeric",
     "format": "num",
     "family": "ss_nain",
     "family_label": "Integration · NAIN",
     "chip": "800",
     "label": "NAIN (normalised angular integration), R800 m",
     "short": "Integration R800 m",
     "note": "Normalised angular integration: how easy the segment is to reach from everywhere within the radius (to-movement).",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.5,
       "label": "< 1.34"
      },
      {
       "min": 1.34,
       "label": "1.34 – 1.59"
      },
      {
       "min": 1.59,
       "label": "1.59 – 1.79"
      },
      {
       "min": 1.79,
       "label": "1.79 – 2.07"
      },
      {
       "min": 2.07,
       "label": "≥ 2.07"
      }
     ]
    },
    {
     "id": "ss_nain_2000",
     "group": "transport",
     "kind": "numeric",
     "format": "num",
     "family": "ss_nain",
     "family_label": "Integration · NAIN",
     "chip": "2000",
     "label": "NAIN (normalised angular integration), R2000 m",
     "short": "Integration R2000 m",
     "note": "Normalised angular integration: how easy the segment is to reach from everywhere within the radius (to-movement).",
     "in_model": false,
     "excluded_reason": "Not used in clustering: the model takes Rn and 800 m. This radius lies between them (Spearman ρ up to 0.69) and is shown for interpretation.",
     "classes": [
      {
       "min": 0.5,
       "label": "< 1.26"
      },
      {
       "min": 1.26,
       "label": "1.26 – 1.49"
      },
      {
       "min": 1.49,
       "label": "1.49 – 1.72"
      },
      {
       "min": 1.72,
       "label": "1.72 – 2.01"
      },
      {
       "min": 2.01,
       "label": "≥ 2.01"
      }
     ]
    },
    {
     "id": "ss_nach_n",
     "group": "transport",
     "kind": "numeric",
     "format": "num",
     "family": "ss_nach",
     "family_label": "Through-movement · NACH",
     "chip": "Rn",
     "label": "NACH (normalised angular choice), Rn",
     "short": "Through-movement Rn",
     "note": "Normalised angular choice: how often the segment lies on the simplest routes within the radius (through-movement).",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "< 0.65"
      },
      {
       "min": 0.647,
       "label": "0.65 – 0.9"
      },
      {
       "min": 0.903,
       "label": "0.9 – 1.01"
      },
      {
       "min": 1.01,
       "label": "1.01 – 1.16"
      },
      {
       "min": 1.16,
       "label": "≥ 1.16"
      }
     ]
    },
    {
     "id": "ss_nach_800",
     "group": "transport",
     "kind": "numeric",
     "format": "num",
     "family": "ss_nach",
     "family_label": "Through-movement · NACH",
     "chip": "800",
     "label": "NACH (normalised angular choice), R800 m",
     "short": "Through-movement R800 m",
     "note": "Normalised angular choice: how often the segment lies on the simplest routes within the radius (through-movement).",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "< 0.62"
      },
      {
       "min": 0.625,
       "label": "0.62 – 0.88"
      },
      {
       "min": 0.875,
       "label": "0.88 – 1.01"
      },
      {
       "min": 1.01,
       "label": "1.01 – 1.14"
      },
      {
       "min": 1.14,
       "label": "≥ 1.14"
      }
     ]
    },
    {
     "id": "ss_nach_2000",
     "group": "transport",
     "kind": "numeric",
     "format": "num",
     "family": "ss_nach",
     "family_label": "Through-movement · NACH",
     "chip": "2000",
     "label": "NACH (normalised angular choice), R2000 m",
     "short": "Through-movement R2000 m",
     "note": "Normalised angular choice: how often the segment lies on the simplest routes within the radius (through-movement).",
     "in_model": false,
     "excluded_reason": "Not used in clustering: the model takes Rn and 800 m. This radius lies between them (Spearman ρ up to 0.74) and is shown for interpretation.",
     "classes": [
      {
       "min": 0.0,
       "label": "< 0.81"
      },
      {
       "min": 0.808,
       "label": "0.81 – 1.01"
      },
      {
       "min": 1.01,
       "label": "1.01 – 1.12"
      },
      {
       "min": 1.12,
       "label": "1.12 – 1.22"
      },
      {
       "min": 1.22,
       "label": "≥ 1.22"
      }
     ]
    },
    {
     "id": "lanes",
     "group": "transport",
     "kind": "numeric",
     "format": "int",
     "family": "lanes",
     "family_label": "Lanes across the street",
     "chip": null,
     "label": "Lanes across the street",
     "short": "Lanes",
     "note": "Lanes across the street, both carriageways of a divided road.",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "1"
      },
      {
       "min": 1.5,
       "label": "2"
      },
      {
       "min": 2.5,
       "label": "3"
      },
      {
       "min": 3.5,
       "label": "4–5"
      },
      {
       "min": 5.5,
       "label": "6 and more"
      }
     ]
    },
    {
     "id": "maxspeed",
     "group": "transport",
     "kind": "numeric",
     "format": "int",
     "family": "maxspeed",
     "family_label": "Speed limit, km/h",
     "chip": null,
     "label": "Speed limit, km/h",
     "short": "Speed limit",
     "note": "Speed limit; missing OSM tags are filled with national defaults by road class.",
     "in_model": false,
     "excluded_reason": "Not used in clustering: 96% of the segments have the same value (60), so it cannot tell streets apart.",
     "classes": [
      {
       "min": 0.0,
       "label": "< 30"
      },
      {
       "min": 30.0,
       "label": "30–40"
      },
      {
       "min": 45.0,
       "label": "50"
      },
      {
       "min": 55.0,
       "label": "60–70"
      },
      {
       "min": 75.0,
       "label": "80 and more"
      }
     ]
    },
    {
     "id": "pt_routes",
     "group": "transport",
     "kind": "numeric",
     "format": "int",
     "family": "pt_routes",
     "family_label": "Public transport routes",
     "chip": null,
     "label": "Public transport routes",
     "short": "PT routes",
     "note": "Public transport routes running along the segment.",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "0"
      },
      {
       "min": 1.0,
       "label": "1"
      },
      {
       "min": 2.0,
       "label": "2–7"
      },
      {
       "min": 8.0,
       "label": "8–20"
      },
      {
       "min": 21.0,
       "label": "≥ 21"
      }
     ]
    },
    {
     "id": "pt_stops_per_100m",
     "group": "transport",
     "kind": "numeric",
     "format": "num",
     "family": "pt_stops_per_100m",
     "family_label": "PT stops per 100 m",
     "chip": null,
     "label": "PT stops per 100 m",
     "short": "PT stops",
     "note": "Public transport stops per 100 m of street.",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "0"
      },
      {
       "min": 0.02394914985723717,
       "label": "< 0.32"
      },
      {
       "min": 0.321,
       "label": "0.32 – 0.51"
      },
      {
       "min": 0.514,
       "label": "0.51 – 0.89"
      },
      {
       "min": 0.885,
       "label": "≥ 0.89"
      }
     ]
    },
    {
     "id": "frontage",
     "group": "context",
     "kind": "numeric",
     "format": "pct",
     "family": "frontage",
     "family_label": "Street-wall continuity (share of length)",
     "chip": null,
     "label": "Street-wall continuity (share of length)",
     "short": "Frontage",
     "note": "Share of the segment length lined by buildings (street wall).",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "0"
      },
      {
       "min": 1e-09,
       "label": "< 25%"
      },
      {
       "min": 0.25,
       "label": "25–50%"
      },
      {
       "min": 0.5,
       "label": "50–75%"
      },
      {
       "min": 0.75,
       "label": "≥ 75%"
      }
     ]
    },
    {
     "id": "poi_per_100m",
     "group": "context",
     "kind": "numeric",
     "format": "num",
     "family": "poi_per_100m",
     "family_label": "Organisations per 100 m",
     "chip": null,
     "label": "Organisations per 100 m",
     "short": "Organisations",
     "note": "Shops, services and other organisations per 100 m.",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "0"
      },
      {
       "min": 0.033341256294153694,
       "label": "< 0.53"
      },
      {
       "min": 0.534,
       "label": "0.53 – 1.01"
      },
      {
       "min": 1.01,
       "label": "1.01 – 1.94"
      },
      {
       "min": 1.94,
       "label": "≥ 1.94"
      }
     ]
    },
    {
     "id": "green_m2_per_100m",
     "group": "context",
     "kind": "numeric",
     "format": "num",
     "family": "green_m2_per_100m",
     "family_label": "Green area, m2 per 100 m",
     "chip": null,
     "label": "Green area, m2 per 100 m",
     "short": "Greenery",
     "note": "Green area in the side strips per 100 m of street.",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "0"
      },
      {
       "min": 0.010326833615911576,
       "label": "< 412"
      },
      {
       "min": 412.0,
       "label": "412 – 1,610"
      },
      {
       "min": 1610.0,
       "label": "1,610 – 4,520"
      },
      {
       "min": 4520.0,
       "label": "≥ 4,520"
      }
     ]
    },
    {
     "id": "fn_residential",
     "group": "context",
     "kind": "numeric",
     "format": "pct",
     "family": "fn",
     "family_label": "Floor-area function",
     "chip": "residential",
     "label": "Residential floor-area share",
     "short": "Residential",
     "note": "Share of floor area along the street by function.",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "0"
      },
      {
       "min": 1e-09,
       "label": "< 25%"
      },
      {
       "min": 0.25,
       "label": "25–50%"
      },
      {
       "min": 0.5,
       "label": "50–75%"
      },
      {
       "min": 0.75,
       "label": "≥ 75%"
      }
     ]
    },
    {
     "id": "fn_commercial",
     "group": "context",
     "kind": "numeric",
     "format": "pct",
     "family": "fn",
     "family_label": "Floor-area function",
     "chip": "commercial",
     "label": "Commercial floor-area share",
     "short": "Commercial",
     "note": "Share of floor area along the street by function.",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "0"
      },
      {
       "min": 1e-09,
       "label": "< 25%"
      },
      {
       "min": 0.25,
       "label": "25–50%"
      },
      {
       "min": 0.5,
       "label": "50–75%"
      },
      {
       "min": 0.75,
       "label": "≥ 75%"
      }
     ]
    },
    {
     "id": "fn_social",
     "group": "context",
     "kind": "numeric",
     "format": "pct",
     "family": "fn",
     "family_label": "Floor-area function",
     "chip": "social",
     "label": "Social floor-area share",
     "short": "Social",
     "note": "Share of floor area along the street by function.",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "0"
      },
      {
       "min": 1e-09,
       "label": "< 25%"
      },
      {
       "min": 0.25,
       "label": "25–50%"
      },
      {
       "min": 0.5,
       "label": "50–75%"
      },
      {
       "min": 0.75,
       "label": "≥ 75%"
      }
     ]
    },
    {
     "id": "fn_industrial",
     "group": "context",
     "kind": "numeric",
     "format": "pct",
     "family": "fn",
     "family_label": "Floor-area function",
     "chip": "industrial",
     "label": "Industrial floor-area share",
     "short": "Industrial",
     "note": "Share of floor area along the street by function.",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "0"
      },
      {
       "min": 1e-09,
       "label": "< 25%"
      },
      {
       "min": 0.25,
       "label": "25–50%"
      },
      {
       "min": 0.5,
       "label": "50–75%"
      },
      {
       "min": 0.75,
       "label": "≥ 75%"
      }
     ]
    },
    {
     "id": "morphotype",
     "group": "morphotypes",
     "kind": "morphotype",
     "label": "Morphotypes T × C",
     "note": "Every street segment is a pair of classes: transport (line width) × context (colour)."
    },
    {
     "id": "T_cluster",
     "group": "morphotypes",
     "kind": "cluster",
     "block": "transport",
     "label": "Transport clusters",
     "note": "Classes of the street as a link in the movement network."
    },
    {
     "id": "C_cluster",
     "group": "morphotypes",
     "kind": "cluster",
     "block": "context",
     "label": "Context clusters",
     "note": "Classes of the street as a place: buildings, uses, greenery."
    },
    {
     "id": "borderline",
     "group": "morphotypes",
     "kind": "borderline",
     "label": "Borderline segments",
     "note": "Segments whose class is uncertain: low silhouette or low model confidence in either block."
    }
   ]
  },
  {
   "id": "wroclaw",
   "label": "Wrocław",
   "run": "wroclaw",
   "mode": "local",
   "trained_on": [
    "wroclaw"
   ],
   "file": "data/cities/wroclaw.js",
   "version": 1791927029,
   "bounds": [
    16.80291,
    51.04261,
    17.17579,
    51.20846
   ],
   "stats": {
    "segments": 7109,
    "classified": 6632,
    "borderline": 1550,
    "k": {
     "transport": 4,
     "context": 4
    },
    "mean_silhouette": {
     "transport": 0.3428,
     "context": 0.4415
    },
    "lanes_imputed_share": 0.454,
    "maxspeed_imputed_share": 0.206,
    "unknown_function_share": 0.038
   },
   "clusters": {
    "transport": [
     {
      "id": 0,
      "name": "T0 · Local access street",
      "count": 1130,
      "profile": "low through-movement Rn, low speed limit"
     },
     {
      "id": 1,
      "name": "T1 · Ordinary street",
      "count": 3327,
      "profile": "low speed limit"
     },
     {
      "id": 2,
      "name": "T2 · Public transport street with stops",
      "count": 748,
      "profile": "high PT stops, high PT routes"
     },
     {
      "id": 3,
      "name": "T3 · Public transport arterial",
      "count": 1427,
      "profile": "high lanes, high PT routes"
     }
    ],
    "context": [
     {
      "id": 0,
      "name": "C0 · Dense residential street, little greenery",
      "count": 993,
      "profile": "low greenery"
     },
     {
      "id": 1,
      "name": "C1 · Green residential street",
      "count": 4039,
      "profile": "close to the city median on every feature"
     },
     {
      "id": 2,
      "name": "C2 · Institutional street (schools, health, campuses)",
      "count": 416,
      "profile": "high social, low residential"
     },
     {
      "id": 3,
      "name": "C3 · Commercial street",
      "count": 990,
      "profile": "high commercial, high organisations"
     },
     {
      "id": -1,
      "name": "C_null · no reliable building data",
      "count": 194
     }
    ]
   },
   "order_by": {
    "transport": {
     "id": "ss_nach_n",
     "label": "through-movement Rn"
    },
    "context": {
     "id": "poi_per_100m",
     "label": "organisations"
    }
   },
   "morphotypes": {
    "T0-C0": {
     "count": 239,
     "name": "Local access street | Dense residential street, little greenery"
    },
    "T0-C1": {
     "count": 715,
     "name": "Local access street | Green residential street"
    },
    "T0-C2": {
     "count": 54,
     "name": "Local access street | Institutional street (schools, health, campuses)"
    },
    "T0-C3": {
     "count": 89,
     "name": "Local access street | Commercial street"
    },
    "T0-C_null": {
     "count": 33,
     "name": "Local access street | no reliable building data"
    },
    "T1-C0": {
     "count": 631,
     "name": "Ordinary street | Dense residential street, little greenery"
    },
    "T1-C1": {
     "count": 2087,
     "name": "Ordinary street | Green residential street"
    },
    "T1-C2": {
     "count": 191,
     "name": "Ordinary street | Institutional street (schools, health, campuses)"
    },
    "T1-C3": {
     "count": 348,
     "name": "Ordinary street | Commercial street"
    },
    "T1-C_null": {
     "count": 70,
     "name": "Ordinary street | no reliable building data"
    },
    "T2-C0": {
     "count": 50,
     "name": "Public transport street with stops | Dense residential street, little greenery"
    },
    "T2-C1": {
     "count": 460,
     "name": "Public transport street with stops | Green residential street"
    },
    "T2-C2": {
     "count": 68,
     "name": "Public transport street with stops | Institutional street (schools, health, campuses)"
    },
    "T2-C3": {
     "count": 151,
     "name": "Public transport street with stops | Commercial street"
    },
    "T2-C_null": {
     "count": 19,
     "name": "Public transport street with stops | no reliable building data"
    },
    "T3-C0": {
     "count": 73,
     "name": "Public transport arterial | Dense residential street, little greenery"
    },
    "T3-C1": {
     "count": 777,
     "name": "Public transport arterial | Green residential street"
    },
    "T3-C2": {
     "count": 103,
     "name": "Public transport arterial | Institutional street (schools, health, campuses)"
    },
    "T3-C3": {
     "count": 402,
     "name": "Public transport arterial | Commercial street"
    },
    "T3-C_null": {
     "count": 72,
     "name": "Public transport arterial | no reliable building data"
    }
   },
   "layers": [
    {
     "id": "ss_nain_n",
     "group": "transport",
     "kind": "numeric",
     "format": "num",
     "family": "ss_nain",
     "family_label": "Integration · NAIN",
     "chip": "Rn",
     "label": "NAIN (normalised angular integration), Rn",
     "short": "Integration Rn",
     "note": "Normalised angular integration: how easy the segment is to reach from everywhere within the radius (to-movement).",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.8059340950431177,
       "label": "< 1.24"
      },
      {
       "min": 1.24,
       "label": "1.24 – 1.38"
      },
      {
       "min": 1.38,
       "label": "1.38 – 1.52"
      },
      {
       "min": 1.52,
       "label": "1.52 – 1.68"
      },
      {
       "min": 1.68,
       "label": "≥ 1.68"
      }
     ]
    },
    {
     "id": "ss_nain_800",
     "group": "transport",
     "kind": "numeric",
     "format": "num",
     "family": "ss_nain",
     "family_label": "Integration · NAIN",
     "chip": "800",
     "label": "NAIN (normalised angular integration), R800 m",
     "short": "Integration R800 m",
     "note": "Normalised angular integration: how easy the segment is to reach from everywhere within the radius (to-movement).",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.5,
       "label": "< 1.29"
      },
      {
       "min": 1.29,
       "label": "1.29 – 1.54"
      },
      {
       "min": 1.54,
       "label": "1.54 – 1.8"
      },
      {
       "min": 1.8,
       "label": "1.8 – 2.11"
      },
      {
       "min": 2.11,
       "label": "≥ 2.11"
      }
     ]
    },
    {
     "id": "ss_nain_2000",
     "group": "transport",
     "kind": "numeric",
     "format": "num",
     "family": "ss_nain",
     "family_label": "Integration · NAIN",
     "chip": "2000",
     "label": "NAIN (normalised angular integration), R2000 m",
     "short": "Integration R2000 m",
     "note": "Normalised angular integration: how easy the segment is to reach from everywhere within the radius (to-movement).",
     "in_model": false,
     "excluded_reason": "Not used in clustering: the model takes Rn and 800 m. This radius lies between them (Spearman ρ up to 0.78) and is shown for interpretation.",
     "classes": [
      {
       "min": 0.5,
       "label": "< 1.22"
      },
      {
       "min": 1.22,
       "label": "1.22 – 1.45"
      },
      {
       "min": 1.45,
       "label": "1.45 – 1.69"
      },
      {
       "min": 1.69,
       "label": "1.69 – 1.98"
      },
      {
       "min": 1.98,
       "label": "≥ 1.98"
      }
     ]
    },
    {
     "id": "ss_nach_n",
     "group": "transport",
     "kind": "numeric",
     "format": "num",
     "family": "ss_nach",
     "family_label": "Through-movement · NACH",
     "chip": "Rn",
     "label": "NACH (normalised angular choice), Rn",
     "short": "Through-movement Rn",
     "note": "Normalised angular choice: how often the segment lies on the simplest routes within the radius (through-movement).",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "< 0.64"
      },
      {
       "min": 0.639,
       "label": "0.64 – 0.92"
      },
      {
       "min": 0.918,
       "label": "0.92 – 1.03"
      },
      {
       "min": 1.03,
       "label": "1.03 – 1.17"
      },
      {
       "min": 1.17,
       "label": "≥ 1.17"
      }
     ]
    },
    {
     "id": "ss_nach_800",
     "group": "transport",
     "kind": "numeric",
     "format": "num",
     "family": "ss_nach",
     "family_label": "Through-movement · NACH",
     "chip": "800",
     "label": "NACH (normalised angular choice), R800 m",
     "short": "Through-movement R800 m",
     "note": "Normalised angular choice: how often the segment lies on the simplest routes within the radius (through-movement).",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "< 0.64"
      },
      {
       "min": 0.642,
       "label": "0.64 – 0.9"
      },
      {
       "min": 0.901,
       "label": "0.9 – 1.04"
      },
      {
       "min": 1.04,
       "label": "1.04 – 1.16"
      },
      {
       "min": 1.16,
       "label": "≥ 1.16"
      }
     ]
    },
    {
     "id": "ss_nach_2000",
     "group": "transport",
     "kind": "numeric",
     "format": "num",
     "family": "ss_nach",
     "family_label": "Through-movement · NACH",
     "chip": "2000",
     "label": "NACH (normalised angular choice), R2000 m",
     "short": "Through-movement R2000 m",
     "note": "Normalised angular choice: how often the segment lies on the simplest routes within the radius (through-movement).",
     "in_model": false,
     "excluded_reason": "Not used in clustering: the model takes Rn and 800 m. This radius lies between them (Spearman ρ up to 0.81) and is shown for interpretation.",
     "classes": [
      {
       "min": 0.0,
       "label": "< 0.78"
      },
      {
       "min": 0.776,
       "label": "0.78 – 0.99"
      },
      {
       "min": 0.994,
       "label": "0.99 – 1.13"
      },
      {
       "min": 1.13,
       "label": "1.13 – 1.23"
      },
      {
       "min": 1.23,
       "label": "≥ 1.23"
      }
     ]
    },
    {
     "id": "lanes",
     "group": "transport",
     "kind": "numeric",
     "format": "int",
     "family": "lanes",
     "family_label": "Lanes across the street",
     "chip": null,
     "label": "Lanes across the street",
     "short": "Lanes",
     "note": "Lanes across the street, both carriageways of a divided road.",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "1"
      },
      {
       "min": 1.5,
       "label": "2"
      },
      {
       "min": 2.5,
       "label": "3"
      },
      {
       "min": 3.5,
       "label": "4–5"
      },
      {
       "min": 5.5,
       "label": "6 and more"
      }
     ]
    },
    {
     "id": "maxspeed",
     "group": "transport",
     "kind": "numeric",
     "format": "int",
     "family": "maxspeed",
     "family_label": "Speed limit, km/h",
     "chip": null,
     "label": "Speed limit, km/h",
     "short": "Speed limit",
     "note": "Speed limit; missing OSM tags are filled with national defaults by road class.",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "< 30"
      },
      {
       "min": 30.0,
       "label": "30–40"
      },
      {
       "min": 45.0,
       "label": "50"
      },
      {
       "min": 55.0,
       "label": "60–70"
      },
      {
       "min": 75.0,
       "label": "80 and more"
      }
     ]
    },
    {
     "id": "pt_routes",
     "group": "transport",
     "kind": "numeric",
     "format": "int",
     "family": "pt_routes",
     "family_label": "Public transport routes",
     "chip": null,
     "label": "Public transport routes",
     "short": "PT routes",
     "note": "Public transport routes running along the segment.",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "0"
      },
      {
       "min": 1.0,
       "label": "1"
      },
      {
       "min": 2.0,
       "label": "2–3"
      },
      {
       "min": 4.0,
       "label": "4–5"
      },
      {
       "min": 6.0,
       "label": "≥ 6"
      }
     ]
    },
    {
     "id": "pt_stops_per_100m",
     "group": "transport",
     "kind": "numeric",
     "format": "num",
     "family": "pt_stops_per_100m",
     "family_label": "PT stops per 100 m",
     "chip": null,
     "label": "PT stops per 100 m",
     "short": "PT stops",
     "note": "Public transport stops per 100 m of street.",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "0"
      },
      {
       "min": 0.04799302891559415,
       "label": "< 0.39"
      },
      {
       "min": 0.389,
       "label": "0.39 – 0.6"
      },
      {
       "min": 0.602,
       "label": "0.6 – 0.95"
      },
      {
       "min": 0.95,
       "label": "≥ 0.95"
      }
     ]
    },
    {
     "id": "frontage",
     "group": "context",
     "kind": "numeric",
     "format": "pct",
     "family": "frontage",
     "family_label": "Street-wall continuity (share of length)",
     "chip": null,
     "label": "Street-wall continuity (share of length)",
     "short": "Frontage",
     "note": "Share of the segment length lined by buildings (street wall).",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "0"
      },
      {
       "min": 1e-09,
       "label": "< 25%"
      },
      {
       "min": 0.25,
       "label": "25–50%"
      },
      {
       "min": 0.5,
       "label": "50–75%"
      },
      {
       "min": 0.75,
       "label": "≥ 75%"
      }
     ]
    },
    {
     "id": "poi_per_100m",
     "group": "context",
     "kind": "numeric",
     "format": "num",
     "family": "poi_per_100m",
     "family_label": "Organisations per 100 m",
     "chip": null,
     "label": "Organisations per 100 m",
     "short": "Organisations",
     "note": "Shops, services and other organisations per 100 m.",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "0"
      },
      {
       "min": 0.014713141756027965,
       "label": "< 0.69"
      },
      {
       "min": 0.691,
       "label": "0.69 – 1.42"
      },
      {
       "min": 1.42,
       "label": "1.42 – 2.92"
      },
      {
       "min": 2.92,
       "label": "≥ 2.92"
      }
     ]
    },
    {
     "id": "green_m2_per_100m",
     "group": "context",
     "kind": "numeric",
     "format": "num",
     "family": "green_m2_per_100m",
     "family_label": "Green area, m2 per 100 m",
     "chip": null,
     "label": "Green area, m2 per 100 m",
     "short": "Greenery",
     "note": "Green area in the side strips per 100 m of street.",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "< 232"
      },
      {
       "min": 232.0,
       "label": "232 – 1,520"
      },
      {
       "min": 1520.0,
       "label": "1,520 – 3,240"
      },
      {
       "min": 3240.0,
       "label": "3,240 – 5,960"
      },
      {
       "min": 5960.0,
       "label": "≥ 5,960"
      }
     ]
    },
    {
     "id": "fn_residential",
     "group": "context",
     "kind": "numeric",
     "format": "pct",
     "family": "fn",
     "family_label": "Floor-area function",
     "chip": "residential",
     "label": "Residential floor-area share",
     "short": "Residential",
     "note": "Share of floor area along the street by function.",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "0"
      },
      {
       "min": 1e-09,
       "label": "< 25%"
      },
      {
       "min": 0.25,
       "label": "25–50%"
      },
      {
       "min": 0.5,
       "label": "50–75%"
      },
      {
       "min": 0.75,
       "label": "≥ 75%"
      }
     ]
    },
    {
     "id": "fn_commercial",
     "group": "context",
     "kind": "numeric",
     "format": "pct",
     "family": "fn",
     "family_label": "Floor-area function",
     "chip": "commercial",
     "label": "Commercial floor-area share",
     "short": "Commercial",
     "note": "Share of floor area along the street by function.",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "0"
      },
      {
       "min": 1e-09,
       "label": "< 25%"
      },
      {
       "min": 0.25,
       "label": "25–50%"
      },
      {
       "min": 0.5,
       "label": "50–75%"
      },
      {
       "min": 0.75,
       "label": "≥ 75%"
      }
     ]
    },
    {
     "id": "fn_social",
     "group": "context",
     "kind": "numeric",
     "format": "pct",
     "family": "fn",
     "family_label": "Floor-area function",
     "chip": "social",
     "label": "Social floor-area share",
     "short": "Social",
     "note": "Share of floor area along the street by function.",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "0"
      },
      {
       "min": 1e-09,
       "label": "< 25%"
      },
      {
       "min": 0.25,
       "label": "25–50%"
      },
      {
       "min": 0.5,
       "label": "50–75%"
      },
      {
       "min": 0.75,
       "label": "≥ 75%"
      }
     ]
    },
    {
     "id": "fn_industrial",
     "group": "context",
     "kind": "numeric",
     "format": "pct",
     "family": "fn",
     "family_label": "Floor-area function",
     "chip": "industrial",
     "label": "Industrial floor-area share",
     "short": "Industrial",
     "note": "Share of floor area along the street by function.",
     "in_model": true,
     "excluded_reason": null,
     "classes": [
      {
       "min": 0.0,
       "label": "0"
      },
      {
       "min": 1e-09,
       "label": "< 25%"
      },
      {
       "min": 0.25,
       "label": "25–50%"
      },
      {
       "min": 0.5,
       "label": "50–75%"
      },
      {
       "min": 0.75,
       "label": "≥ 75%"
      }
     ]
    },
    {
     "id": "morphotype",
     "group": "morphotypes",
     "kind": "morphotype",
     "label": "Morphotypes T × C",
     "note": "Every street segment is a pair of classes: transport (line width) × context (colour)."
    },
    {
     "id": "T_cluster",
     "group": "morphotypes",
     "kind": "cluster",
     "block": "transport",
     "label": "Transport clusters",
     "note": "Classes of the street as a link in the movement network."
    },
    {
     "id": "C_cluster",
     "group": "morphotypes",
     "kind": "cluster",
     "block": "context",
     "label": "Context clusters",
     "note": "Classes of the street as a place: buildings, uses, greenery."
    },
    {
     "id": "borderline",
     "group": "morphotypes",
     "kind": "borderline",
     "label": "Borderline segments",
     "note": "Segments whose class is uncertain: low silhouette or low model confidence in either block."
    }
   ]
  }
 ]
};
