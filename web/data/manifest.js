window.SM_MANIFEST = {
 "generated": "2026-10-14T08:49:22+00:00",
 "output_root": "outputs",
 "cities": [
  {
   "id": "irkutsk",
   "label": "Irkutsk",
   "run": "irkutsk",
   "mode": "own",
   "trained_on": [
    "irkutsk"
   ],
   "file": "data/cities/irkutsk.js",
   "version": 1791963885,
   "bounds": [
    104.07191,
    52.20975,
    104.44439,
    52.40524
   ],
   "stats": {
    "segments": 4741,
    "lanes_imputed_share": 0.605,
    "maxspeed_imputed_share": 0.626,
    "unknown_function_share": 0.076
   },
   "typologies": [
    {
     "id": "own",
     "key": "",
     "kind": "own",
     "label": "Own typology",
     "run": "irkutsk",
     "trained_on": [
      "irkutsk"
     ],
     "trained_on_labels": [
      "Irkutsk"
     ],
     "stats": {
      "classified": 4528,
      "borderline": 883,
      "k": {
       "transport": 4,
       "context": 4
      },
      "mean_silhouette": {
       "transport": 0.412,
       "context": 0.4835
      }
     },
     "clusters": {
      "transport": [
       {
        "id": 1,
        "name": "T1 · Local access street",
        "count": 813,
        "profile": "low through-movement Rn, low integration R800 m"
       },
       {
        "id": 2,
        "name": "T2 · Ordinary street",
        "count": 2730,
        "profile": "close to the city median on every feature"
       },
       {
        "id": 3,
        "name": "T3 · Public transport street with stops",
        "count": 297,
        "profile": "high PT stops, high PT routes"
       },
       {
        "id": 4,
        "name": "T4 · Public transport arterial",
        "count": 688,
        "profile": "high PT routes, high lanes"
       }
      ],
      "context": [
       {
        "id": 1,
        "name": "C1 · Residential street without services",
        "count": 2688,
        "profile": "close to the city median on every feature"
       },
       {
        "id": 2,
        "name": "C2 · Green street with sparse buildings",
        "count": 617,
        "profile": "high greenery, low residential"
       },
       {
        "id": 3,
        "name": "C3 · Institutional street (schools, health, campuses)",
        "count": 185,
        "profile": "high social, low residential"
       },
       {
        "id": 4,
        "name": "C4 · Commercial street",
        "count": 769,
        "profile": "high commercial, high organisations"
       },
       {
        "id": -1,
        "name": "C_null · no reliable building data",
        "count": 269
       }
      ]
     },
     "morphotypes": {
      "T1-C1": {
       "count": 565,
       "name": "Local access street | Residential street without services"
      },
      "T1-C2": {
       "count": 91,
       "name": "Local access street | Green street with sparse buildings"
      },
      "T1-C3": {
       "count": 27,
       "name": "Local access street | Institutional street (schools, health, campuses)"
      },
      "T1-C4": {
       "count": 70,
       "name": "Local access street | Commercial street"
      },
      "T1-C_null": {
       "count": 60,
       "name": "Local access street | no reliable building data"
      },
      "T2-C1": {
       "count": 1847,
       "name": "Ordinary street | Residential street without services"
      },
      "T2-C2": {
       "count": 330,
       "name": "Ordinary street | Green street with sparse buildings"
      },
      "T2-C3": {
       "count": 87,
       "name": "Ordinary street | Institutional street (schools, health, campuses)"
      },
      "T2-C4": {
       "count": 325,
       "name": "Ordinary street | Commercial street"
      },
      "T2-C_null": {
       "count": 141,
       "name": "Ordinary street | no reliable building data"
      },
      "T3-C1": {
       "count": 105,
       "name": "Public transport street with stops | Residential street without services"
      },
      "T3-C2": {
       "count": 32,
       "name": "Public transport street with stops | Green street with sparse buildings"
      },
      "T3-C3": {
       "count": 23,
       "name": "Public transport street with stops | Institutional street (schools, health, campuses)"
      },
      "T3-C4": {
       "count": 124,
       "name": "Public transport street with stops | Commercial street"
      },
      "T3-C_null": {
       "count": 13,
       "name": "Public transport street with stops | no reliable building data"
      },
      "T4-C1": {
       "count": 171,
       "name": "Public transport arterial | Residential street without services"
      },
      "T4-C2": {
       "count": 164,
       "name": "Public transport arterial | Green street with sparse buildings"
      },
      "T4-C3": {
       "count": 48,
       "name": "Public transport arterial | Institutional street (schools, health, campuses)"
      },
      "T4-C4": {
       "count": 250,
       "name": "Public transport arterial | Commercial street"
      },
      "T4-C_null": {
       "count": 55,
       "name": "Public transport arterial | no reliable building data"
      }
     }
    },
    {
     "id": "model-wroclaw",
     "key": "@1",
     "kind": "model",
     "label": "Wrocław model",
     "run": "applied_wroclaw",
     "trained_on": [
      "wroclaw"
     ],
     "trained_on_labels": [
      "Wrocław"
     ],
     "stats": {
      "classified": 4528,
      "borderline": 889,
      "k": {
       "transport": 4,
       "context": 4
      },
      "mean_silhouette": {
       "transport": 0.4115,
       "context": 0.5337
      }
     },
     "clusters": {
      "transport": [
       {
        "id": 1,
        "name": "T1 · Local access street",
        "count": 769,
        "profile": "low through-movement Rn, low speed limit"
       },
       {
        "id": 2,
        "name": "T2 · Ordinary street",
        "count": 2681,
        "profile": "low speed limit"
       },
       {
        "id": 3,
        "name": "T3 · Public transport street with stops",
        "count": 300,
        "profile": "high PT stops, high PT routes"
       },
       {
        "id": 4,
        "name": "T4 · Public transport arterial",
        "count": 778,
        "profile": "high PT routes, high lanes"
       }
      ],
      "context": [
       {
        "id": 1,
        "name": "C1 · Dense residential street, little greenery",
        "count": 3053,
        "profile": "low greenery"
       },
       {
        "id": 2,
        "name": "C2 · Green residential street",
        "count": 689,
        "profile": "close to the city median on every feature"
       },
       {
        "id": 3,
        "name": "C3 · Institutional street (schools, health, campuses)",
        "count": 148,
        "profile": "high social, low residential"
       },
       {
        "id": 4,
        "name": "C4 · Commercial street",
        "count": 369,
        "profile": "high commercial, high organisations"
       },
       {
        "id": -1,
        "name": "C_null · no reliable building data",
        "count": 269
       }
      ]
     },
     "morphotypes": {
      "T1-C1": {
       "count": 569,
       "name": "Local access street | Dense residential street, little greenery"
      },
      "T1-C2": {
       "count": 95,
       "name": "Local access street | Green residential street"
      },
      "T1-C3": {
       "count": 18,
       "name": "Local access street | Institutional street (schools, health, campuses)"
      },
      "T1-C4": {
       "count": 29,
       "name": "Local access street | Commercial street"
      },
      "T1-C_null": {
       "count": 58,
       "name": "Local access street | no reliable building data"
      },
      "T2-C1": {
       "count": 2032,
       "name": "Ordinary street | Dense residential street, little greenery"
      },
      "T2-C2": {
       "count": 337,
       "name": "Ordinary street | Green residential street"
      },
      "T2-C3": {
       "count": 60,
       "name": "Ordinary street | Institutional street (schools, health, campuses)"
      },
      "T2-C4": {
       "count": 116,
       "name": "Ordinary street | Commercial street"
      },
      "T2-C_null": {
       "count": 136,
       "name": "Ordinary street | no reliable building data"
      },
      "T3-C1": {
       "count": 163,
       "name": "Public transport street with stops | Dense residential street, little greenery"
      },
      "T3-C2": {
       "count": 44,
       "name": "Public transport street with stops | Green residential street"
      },
      "T3-C3": {
       "count": 20,
       "name": "Public transport street with stops | Institutional street (schools, health, campuses)"
      },
      "T3-C4": {
       "count": 59,
       "name": "Public transport street with stops | Commercial street"
      },
      "T3-C_null": {
       "count": 14,
       "name": "Public transport street with stops | no reliable building data"
      },
      "T4-C1": {
       "count": 289,
       "name": "Public transport arterial | Dense residential street, little greenery"
      },
      "T4-C2": {
       "count": 213,
       "name": "Public transport arterial | Green residential street"
      },
      "T4-C3": {
       "count": 50,
       "name": "Public transport arterial | Institutional street (schools, health, campuses)"
      },
      "T4-C4": {
       "count": 165,
       "name": "Public transport arterial | Commercial street"
      },
      "T4-C_null": {
       "count": 61,
       "name": "Public transport arterial | no reliable building data"
      }
     },
     "compare": {
      "transport": {
       "ari": 0.889,
       "crosswalk": {
        "rows": [
         1,
         2,
         3,
         4
        ],
        "cols": [
         1,
         2,
         3,
         4
        ],
        "counts": [
         [
          757,
          56,
          0,
          0
         ],
         [
          10,
          2624,
          2,
          94
         ],
         [
          2,
          1,
          291,
          3
         ],
         [
          0,
          0,
          7,
          681
         ]
        ]
       }
      },
      "context": {
       "ari": 0.729,
       "crosswalk": {
        "rows": [
         1,
         2,
         3,
         4
        ],
        "cols": [
         1,
         2,
         3,
         4
        ],
        "counts": [
         [
          2688,
          0,
          0,
          0
         ],
         [
          1,
          615,
          1,
          0
         ],
         [
          67,
          1,
          117,
          0
         ],
         [
          297,
          73,
          30,
          369
         ]
        ]
       }
      },
      "morphotype": {
       "ari": 0.813
      }
     }
    },
    {
     "id": "pooled-irkutsk_wroclaw",
     "key": "@2",
     "kind": "pooled",
     "label": "Pooled: Irkutsk + Wrocław",
     "run": "irkutsk_wroclaw",
     "trained_on": [
      "irkutsk",
      "wroclaw"
     ],
     "trained_on_labels": [
      "Irkutsk",
      "Wrocław"
     ],
     "stats": {
      "classified": 4528,
      "borderline": 788,
      "k": {
       "transport": 4,
       "context": 2
      },
      "mean_silhouette": {
       "transport": 0.3598,
       "context": 0.5105
      }
     },
     "clusters": {
      "transport": [
       {
        "id": 1,
        "name": "T1 · low through-movement Rn, low integration R800 m",
        "count": 793,
        "profile": null
       },
       {
        "id": 2,
        "name": "T2 · average profile",
        "count": 2742,
        "profile": "close to the city median on every feature"
       },
       {
        "id": 3,
        "name": "T3 · high PT stops, high PT routes",
        "count": 291,
        "profile": null
       },
       {
        "id": 4,
        "name": "T4 · high PT routes, high lanes",
        "count": 702,
        "profile": null
       }
      ],
      "context": [
       {
        "id": 1,
        "name": "C1 · average profile",
        "count": 3659,
        "profile": "close to the city median on every feature"
       },
       {
        "id": 2,
        "name": "C2 · high commercial, high organisations",
        "count": 600,
        "profile": null
       },
       {
        "id": -1,
        "name": "C_null · no reliable building data",
        "count": 269
       }
      ]
     },
     "morphotypes": {
      "T1-C1": {
       "count": 685,
       "name": "low through-movement Rn, low integration R800 m | average profile"
      },
      "T1-C2": {
       "count": 48,
       "name": "low through-movement Rn, low integration R800 m | high commercial, high organisations"
      },
      "T1-C_null": {
       "count": 60,
       "name": "low through-movement Rn, low integration R800 m | no reliable building data"
      },
      "T2-C1": {
       "count": 2363,
       "name": "average profile | average profile"
      },
      "T2-C2": {
       "count": 239,
       "name": "average profile | high commercial, high organisations"
      },
      "T2-C_null": {
       "count": 140,
       "name": "average profile | no reliable building data"
      },
      "T3-C1": {
       "count": 175,
       "name": "high PT stops, high PT routes | average profile"
      },
      "T3-C2": {
       "count": 103,
       "name": "high PT stops, high PT routes | high commercial, high organisations"
      },
      "T3-C_null": {
       "count": 13,
       "name": "high PT stops, high PT routes | no reliable building data"
      },
      "T4-C1": {
       "count": 436,
       "name": "high PT routes, high lanes | average profile"
      },
      "T4-C2": {
       "count": 210,
       "name": "high PT routes, high lanes | high commercial, high organisations"
      },
      "T4-C_null": {
       "count": 56,
       "name": "high PT routes, high lanes | no reliable building data"
      }
     },
     "compare": {
      "transport": {
       "ari": 0.965,
       "crosswalk": {
        "rows": [
         1,
         2,
         3,
         4
        ],
        "cols": [
         1,
         2,
         3,
         4
        ],
        "counts": [
         [
          786,
          27,
          0,
          0
         ],
         [
          6,
          2711,
          0,
          13
         ],
         [
          1,
          3,
          291,
          2
         ],
         [
          0,
          1,
          0,
          687
         ]
        ]
       }
      },
      "context": {
       "ari": 0.376,
       "crosswalk": {
        "rows": [
         1,
         2,
         3,
         4
        ],
        "cols": [
         1,
         2
        ],
        "counts": [
         [
          2688,
          0
         ],
         [
          617,
          0
         ],
         [
          182,
          3
         ],
         [
          172,
          597
         ]
        ]
       }
      },
      "morphotype": {
       "ari": 0.686
      }
     }
    }
   ],
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
       "min": 0.5719432416193888,
       "label": "< 0.93"
      },
      {
       "min": 0.932,
       "label": "0.93 – 1.03"
      },
      {
       "min": 1.03,
       "label": "1.03 – 1.1"
      },
      {
       "min": 1.1,
       "label": "1.1 – 1.21"
      },
      {
       "min": 1.21,
       "label": "≥ 1.21"
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
       "label": "< 1.27"
      },
      {
       "min": 1.27,
       "label": "1.27 – 1.5"
      },
      {
       "min": 1.5,
       "label": "1.5 – 1.72"
      },
      {
       "min": 1.72,
       "label": "1.72 – 1.99"
      },
      {
       "min": 1.99,
       "label": "≥ 1.99"
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
     "excluded_reason": "Not used in clustering: the model takes Rn and 800 m. This radius lies between them (Spearman ρ up to 0.71) and is shown for interpretation.",
     "classes": [
      {
       "min": 0.42836851132100806,
       "label": "< 1.16"
      },
      {
       "min": 1.16,
       "label": "1.16 – 1.37"
      },
      {
       "min": 1.37,
       "label": "1.37 – 1.59"
      },
      {
       "min": 1.59,
       "label": "1.59 – 1.88"
      },
      {
       "min": 1.88,
       "label": "≥ 1.88"
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
       "label": "< 0.59"
      },
      {
       "min": 0.589,
       "label": "0.59 – 0.89"
      },
      {
       "min": 0.891,
       "label": "0.89 – 0.99"
      },
      {
       "min": 0.992,
       "label": "0.99 – 1.13"
      },
      {
       "min": 1.13,
       "label": "≥ 1.13"
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
       "min": 0.638,
       "label": "0.64 – 0.87"
      },
      {
       "min": 0.874,
       "label": "0.87 – 1.01"
      },
      {
       "min": 1.01,
       "label": "1.01 – 1.13"
      },
      {
       "min": 1.13,
       "label": "≥ 1.13"
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
     "excluded_reason": "Not used in clustering: the model takes Rn and 800 m. This radius lies between them (Spearman ρ up to 0.75) and is shown for interpretation.",
     "classes": [
      {
       "min": 0.0,
       "label": "< 0.79"
      },
      {
       "min": 0.791,
       "label": "0.79 – 0.99"
      },
      {
       "min": 0.988,
       "label": "0.99 – 1.11"
      },
      {
       "min": 1.11,
       "label": "1.11 – 1.21"
      },
      {
       "min": 1.21,
       "label": "≥ 1.21"
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
       "label": "< 0.33"
      },
      {
       "min": 0.333,
       "label": "0.33 – 0.53"
      },
      {
       "min": 0.528,
       "label": "0.53 – 0.9"
      },
      {
       "min": 0.898,
       "label": "≥ 0.9"
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
       "label": "< 0.55"
      },
      {
       "min": 0.545,
       "label": "0.55 – 1.05"
      },
      {
       "min": 1.05,
       "label": "1.05 – 1.95"
      },
      {
       "min": 1.95,
       "label": "≥ 1.95"
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
       "min": 0.015675281660541232,
       "label": "< 436"
      },
      {
       "min": 436.0,
       "label": "436 – 1,640"
      },
      {
       "min": 1640.0,
       "label": "1,640 – 4,750"
      },
      {
       "min": 4750.0,
       "label": "≥ 4,750"
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
   "mode": "own",
   "trained_on": [
    "wroclaw"
   ],
   "file": "data/cities/wroclaw.js",
   "version": 1791963815,
   "bounds": [
    16.80737,
    51.04298,
    17.17579,
    51.20794
   ],
   "stats": {
    "segments": 7817,
    "lanes_imputed_share": 0.474,
    "maxspeed_imputed_share": 0.221,
    "unknown_function_share": 0.038
   },
   "typologies": [
    {
     "id": "own",
     "key": "",
     "kind": "own",
     "label": "Own typology",
     "run": "wroclaw",
     "trained_on": [
      "wroclaw"
     ],
     "trained_on_labels": [
      "Wrocław"
     ],
     "stats": {
      "classified": 7294,
      "borderline": 1690,
      "k": {
       "transport": 4,
       "context": 4
      },
      "mean_silhouette": {
       "transport": 0.3477,
       "context": 0.4435
      }
     },
     "clusters": {
      "transport": [
       {
        "id": 1,
        "name": "T1 · Local access street",
        "count": 1298,
        "profile": "low through-movement Rn, low speed limit"
       },
       {
        "id": 2,
        "name": "T2 · Ordinary street",
        "count": 3620,
        "profile": "low speed limit"
       },
       {
        "id": 3,
        "name": "T3 · Public transport street with stops",
        "count": 781,
        "profile": "high PT stops, high PT routes"
       },
       {
        "id": 4,
        "name": "T4 · Public transport arterial",
        "count": 1595,
        "profile": "high PT routes, high lanes"
       }
      ],
      "context": [
       {
        "id": 1,
        "name": "C1 · Dense residential street, little greenery",
        "count": 1114,
        "profile": "low greenery"
       },
       {
        "id": 2,
        "name": "C2 · Green residential street",
        "count": 4448,
        "profile": "close to the city median on every feature"
       },
       {
        "id": 3,
        "name": "C3 · Institutional street (schools, health, campuses)",
        "count": 434,
        "profile": "high social, low residential"
       },
       {
        "id": 4,
        "name": "C4 · Commercial street",
        "count": 1078,
        "profile": "high commercial, high organisations"
       },
       {
        "id": -1,
        "name": "C_null · no reliable building data",
        "count": 220
       }
      ]
     },
     "morphotypes": {
      "T1-C1": {
       "count": 272,
       "name": "Local access street | Dense residential street, little greenery"
      },
      "T1-C2": {
       "count": 840,
       "name": "Local access street | Green residential street"
      },
      "T1-C3": {
       "count": 50,
       "name": "Local access street | Institutional street (schools, health, campuses)"
      },
      "T1-C4": {
       "count": 102,
       "name": "Local access street | Commercial street"
      },
      "T1-C_null": {
       "count": 34,
       "name": "Local access street | no reliable building data"
      },
      "T2-C1": {
       "count": 715,
       "name": "Ordinary street | Dense residential street, little greenery"
      },
      "T2-C2": {
       "count": 2229,
       "name": "Ordinary street | Green residential street"
      },
      "T2-C3": {
       "count": 207,
       "name": "Ordinary street | Institutional street (schools, health, campuses)"
      },
      "T2-C4": {
       "count": 386,
       "name": "Ordinary street | Commercial street"
      },
      "T2-C_null": {
       "count": 83,
       "name": "Ordinary street | no reliable building data"
      },
      "T3-C1": {
       "count": 50,
       "name": "Public transport street with stops | Dense residential street, little greenery"
      },
      "T3-C2": {
       "count": 483,
       "name": "Public transport street with stops | Green residential street"
      },
      "T3-C3": {
       "count": 67,
       "name": "Public transport street with stops | Institutional street (schools, health, campuses)"
      },
      "T3-C4": {
       "count": 160,
       "name": "Public transport street with stops | Commercial street"
      },
      "T3-C_null": {
       "count": 21,
       "name": "Public transport street with stops | no reliable building data"
      },
      "T4-C1": {
       "count": 77,
       "name": "Public transport arterial | Dense residential street, little greenery"
      },
      "T4-C2": {
       "count": 896,
       "name": "Public transport arterial | Green residential street"
      },
      "T4-C3": {
       "count": 110,
       "name": "Public transport arterial | Institutional street (schools, health, campuses)"
      },
      "T4-C4": {
       "count": 430,
       "name": "Public transport arterial | Commercial street"
      },
      "T4-C_null": {
       "count": 82,
       "name": "Public transport arterial | no reliable building data"
      }
     }
    },
    {
     "id": "model-irkutsk",
     "key": "@1",
     "kind": "model",
     "label": "Irkutsk model",
     "run": "applied_irkutsk",
     "trained_on": [
      "irkutsk"
     ],
     "trained_on_labels": [
      "Irkutsk"
     ],
     "stats": {
      "classified": 7294,
      "borderline": 2073,
      "k": {
       "transport": 4,
       "context": 4
      },
      "mean_silhouette": {
       "transport": 0.3583,
       "context": 0.356
      }
     },
     "clusters": {
      "transport": [
       {
        "id": 1,
        "name": "T1 · Local access street",
        "count": 1317,
        "profile": "low through-movement Rn, low integration R800 m"
       },
       {
        "id": 2,
        "name": "T2 · Ordinary street",
        "count": 3706,
        "profile": "close to the city median on every feature"
       },
       {
        "id": 3,
        "name": "T3 · Public transport street with stops",
        "count": 798,
        "profile": "high PT stops, high PT routes"
       },
       {
        "id": 4,
        "name": "T4 · Public transport arterial",
        "count": 1473,
        "profile": "high PT routes, high lanes"
       }
      ],
      "context": [
       {
        "id": 1,
        "name": "C1 · Residential street without services",
        "count": 978,
        "profile": "close to the city median on every feature"
       },
       {
        "id": 2,
        "name": "C2 · Green street with sparse buildings",
        "count": 3731,
        "profile": "high greenery, low residential"
       },
       {
        "id": 3,
        "name": "C3 · Institutional street (schools, health, campuses)",
        "count": 400,
        "profile": "high social, low residential"
       },
       {
        "id": 4,
        "name": "C4 · Commercial street",
        "count": 1965,
        "profile": "high commercial, high organisations"
       },
       {
        "id": -1,
        "name": "C_null · no reliable building data",
        "count": 220
       }
      ]
     },
     "morphotypes": {
      "T1-C1": {
       "count": 266,
       "name": "Local access street | Residential street without services"
      },
      "T1-C2": {
       "count": 764,
       "name": "Local access street | Green street with sparse buildings"
      },
      "T1-C3": {
       "count": 47,
       "name": "Local access street | Institutional street (schools, health, campuses)"
      },
      "T1-C4": {
       "count": 208,
       "name": "Local access street | Commercial street"
      },
      "T1-C_null": {
       "count": 32,
       "name": "Local access street | no reliable building data"
      },
      "T2-C1": {
       "count": 628,
       "name": "Ordinary street | Residential street without services"
      },
      "T2-C2": {
       "count": 1936,
       "name": "Ordinary street | Green street with sparse buildings"
      },
      "T2-C3": {
       "count": 196,
       "name": "Ordinary street | Institutional street (schools, health, campuses)"
      },
      "T2-C4": {
       "count": 858,
       "name": "Ordinary street | Commercial street"
      },
      "T2-C_null": {
       "count": 88,
       "name": "Ordinary street | no reliable building data"
      },
      "T3-C1": {
       "count": 35,
       "name": "Public transport street with stops | Residential street without services"
      },
      "T3-C2": {
       "count": 366,
       "name": "Public transport street with stops | Green street with sparse buildings"
      },
      "T3-C3": {
       "count": 63,
       "name": "Public transport street with stops | Institutional street (schools, health, campuses)"
      },
      "T3-C4": {
       "count": 313,
       "name": "Public transport street with stops | Commercial street"
      },
      "T3-C_null": {
       "count": 21,
       "name": "Public transport street with stops | no reliable building data"
      },
      "T4-C1": {
       "count": 49,
       "name": "Public transport arterial | Residential street without services"
      },
      "T4-C2": {
       "count": 665,
       "name": "Public transport arterial | Green street with sparse buildings"
      },
      "T4-C3": {
       "count": 94,
       "name": "Public transport arterial | Institutional street (schools, health, campuses)"
      },
      "T4-C4": {
       "count": 586,
       "name": "Public transport arterial | Commercial street"
      },
      "T4-C_null": {
       "count": 79,
       "name": "Public transport arterial | no reliable building data"
      }
     },
     "compare": {
      "transport": {
       "ari": 0.906,
       "crosswalk": {
        "rows": [
         1,
         2,
         3,
         4
        ],
        "cols": [
         1,
         2,
         3,
         4
        ],
        "counts": [
         [
          1283,
          12,
          3,
          0
         ],
         [
          34,
          3554,
          18,
          14
         ],
         [
          0,
          0,
          770,
          11
         ],
         [
          0,
          140,
          7,
          1448
         ]
        ]
       }
      },
      "context": {
       "ari": 0.667,
       "crosswalk": {
        "rows": [
         1,
         2,
         3,
         4
        ],
        "cols": [
         1,
         2,
         3,
         4
        ],
        "counts": [
         [
          967,
          7,
          23,
          117
         ],
         [
          11,
          3720,
          13,
          704
         ],
         [
          0,
          4,
          364,
          66
         ],
         [
          0,
          0,
          0,
          1078
         ]
        ]
       }
      },
      "morphotype": {
       "ari": 0.733
      }
     }
    },
    {
     "id": "pooled-irkutsk_wroclaw",
     "key": "@2",
     "kind": "pooled",
     "label": "Pooled: Irkutsk + Wrocław",
     "run": "irkutsk_wroclaw",
     "trained_on": [
      "irkutsk",
      "wroclaw"
     ],
     "trained_on_labels": [
      "Irkutsk",
      "Wrocław"
     ],
     "stats": {
      "classified": 7294,
      "borderline": 1666,
      "k": {
       "transport": 4,
       "context": 2
      },
      "mean_silhouette": {
       "transport": 0.3598,
       "context": 0.5105
      }
     },
     "clusters": {
      "transport": [
       {
        "id": 1,
        "name": "T1 · low through-movement Rn, low integration R800 m",
        "count": 1335,
        "profile": null
       },
       {
        "id": 2,
        "name": "T2 · average profile",
        "count": 3779,
        "profile": "close to the city median on every feature"
       },
       {
        "id": 3,
        "name": "T3 · high PT stops, high PT routes",
        "count": 786,
        "profile": null
       },
       {
        "id": 4,
        "name": "T4 · high PT routes, high lanes",
        "count": 1394,
        "profile": null
       }
      ],
      "context": [
       {
        "id": 1,
        "name": "C1 · average profile",
        "count": 5450,
        "profile": "close to the city median on every feature"
       },
       {
        "id": 2,
        "name": "C2 · high commercial, high organisations",
        "count": 1624,
        "profile": null
       },
       {
        "id": -1,
        "name": "C_null · no reliable building data",
        "count": 220
       }
      ]
     },
     "morphotypes": {
      "T1-C1": {
       "count": 1129,
       "name": "low through-movement Rn, low integration R800 m | average profile"
      },
      "T1-C2": {
       "count": 172,
       "name": "low through-movement Rn, low integration R800 m | high commercial, high organisations"
      },
      "T1-C_null": {
       "count": 34,
       "name": "low through-movement Rn, low integration R800 m | no reliable building data"
      },
      "T2-C1": {
       "count": 2995,
       "name": "average profile | average profile"
      },
      "T2-C2": {
       "count": 691,
       "name": "average profile | high commercial, high organisations"
      },
      "T2-C_null": {
       "count": 93,
       "name": "average profile | no reliable building data"
      },
      "T3-C1": {
       "count": 509,
       "name": "high PT stops, high PT routes | average profile"
      },
      "T3-C2": {
       "count": 257,
       "name": "high PT stops, high PT routes | high commercial, high organisations"
      },
      "T3-C_null": {
       "count": 20,
       "name": "high PT stops, high PT routes | no reliable building data"
      },
      "T4-C1": {
       "count": 817,
       "name": "high PT routes, high lanes | average profile"
      },
      "T4-C2": {
       "count": 504,
       "name": "high PT routes, high lanes | high commercial, high organisations"
      },
      "T4-C_null": {
       "count": 73,
       "name": "high PT routes, high lanes | no reliable building data"
      }
     },
     "compare": {
      "transport": {
       "ari": 0.893,
       "crosswalk": {
        "rows": [
         1,
         2,
         3,
         4
        ],
        "cols": [
         1,
         2,
         3,
         4
        ],
        "counts": [
         [
          1296,
          1,
          1,
          0
         ],
         [
          39,
          3573,
          6,
          2
         ],
         [
          0,
          7,
          769,
          5
         ],
         [
          0,
          198,
          10,
          1387
         ]
        ]
       }
      },
      "context": {
       "ari": 0.34,
       "crosswalk": {
        "rows": [
         1,
         2,
         3,
         4
        ],
        "cols": [
         1,
         2
        ],
        "counts": [
         [
          1060,
          54
         ],
         [
          4032,
          416
         ],
         [
          358,
          76
         ],
         [
          0,
          1078
         ]
        ]
       }
      },
      "morphotype": {
       "ari": 0.555
      }
     }
    }
   ],
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
       "min": 0.6881863389856026,
       "label": "< 1.16"
      },
      {
       "min": 1.16,
       "label": "1.16 – 1.3"
      },
      {
       "min": 1.3,
       "label": "1.3 – 1.45"
      },
      {
       "min": 1.45,
       "label": "1.45 – 1.6"
      },
      {
       "min": 1.6,
       "label": "≥ 1.6"
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
       "min": 0.4921257878166598,
       "label": "< 1.22"
      },
      {
       "min": 1.22,
       "label": "1.22 – 1.46"
      },
      {
       "min": 1.46,
       "label": "1.46 – 1.73"
      },
      {
       "min": 1.73,
       "label": "1.73 – 2.05"
      },
      {
       "min": 2.05,
       "label": "≥ 2.05"
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
     "excluded_reason": "Not used in clustering: the model takes Rn and 800 m. This radius lies between them (Spearman ρ up to 0.81) and is shown for interpretation.",
     "classes": [
      {
       "min": 0.4001959607688923,
       "label": "< 1.14"
      },
      {
       "min": 1.14,
       "label": "1.14 – 1.37"
      },
      {
       "min": 1.37,
       "label": "1.37 – 1.61"
      },
      {
       "min": 1.61,
       "label": "1.61 – 1.9"
      },
      {
       "min": 1.9,
       "label": "≥ 1.9"
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
       "label": "< 0.58"
      },
      {
       "min": 0.579,
       "label": "0.58 – 0.91"
      },
      {
       "min": 0.908,
       "label": "0.91 – 1.02"
      },
      {
       "min": 1.02,
       "label": "1.02 – 1.17"
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
       "label": "< 0.66"
      },
      {
       "min": 0.656,
       "label": "0.66 – 0.9"
      },
      {
       "min": 0.9,
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
     "excluded_reason": "Not used in clustering: the model takes Rn and 800 m. This radius lies between them (Spearman ρ up to 0.84) and is shown for interpretation.",
     "classes": [
      {
       "min": 0.0,
       "label": "< 0.76"
      },
      {
       "min": 0.758,
       "label": "0.76 – 0.98"
      },
      {
       "min": 0.979,
       "label": "0.98 – 1.12"
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
       "min": 0.0539329315447596,
       "label": "< 0.4"
      },
      {
       "min": 0.402,
       "label": "0.4 – 0.62"
      },
      {
       "min": 0.624,
       "label": "0.62 – 0.97"
      },
      {
       "min": 0.973,
       "label": "≥ 0.97"
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
       "min": 0.03836240562735611,
       "label": "< 0.74"
      },
      {
       "min": 0.736,
       "label": "0.74 – 1.47"
      },
      {
       "min": 1.47,
       "label": "1.47 – 3.02"
      },
      {
       "min": 3.02,
       "label": "≥ 3.02"
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
       "label": "< 217"
      },
      {
       "min": 217.0,
       "label": "217 – 1,510"
      },
      {
       "min": 1510.0,
       "label": "1,510 – 3,290"
      },
      {
       "min": 3290.0,
       "label": "3,290 – 6,090"
      },
      {
       "min": 6090.0,
       "label": "≥ 6,090"
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
