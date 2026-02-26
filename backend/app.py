
# # .\venv\Scripts\Activate
# # python app.py


#///////////////////////////////////////////////////////////

# PART 3 

# full code with integration of lulc

# from flask import Flask, jsonify, request
# from flask_cors import CORS
# import requests
# import csv
# import os
# import json
# import math
# import ee
# import re

# # ============================================================
# # 1) Flask app setup
# # ============================================================

# app = Flask(__name__)
# CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

# # ============================================================
# # 2) Config / constants
# # ============================================================

# GEOSERVER_BASE = "https://geoserver.core-stack.org:8443/geoserver/"
# WORKS_WORKSPACE = "works"
# RESOURCES_WORKSPACE = "resources"

# # Which prefixes live in which workspace
# LAYER_CONFIG = {
#     "plan_agri": WORKS_WORKSPACE,
#     "plan_gw": WORKS_WORKSPACE,
#     "waterbody": RESOURCES_WORKSPACE,
# }

# # Try these fields in this order to infer structure type from GeoServer properties
# STRUCTURE_FIELDS = ["TYPE_OF_WO", "work_type", "selected_w", "select_o_4"]

# FLAGGED_FILE = "flagged_sites.csv"

# # Drainage lines asset
# DRAINAGE_LINES_ASSET = "projects/corestack-datasets/assets/datasets/drainage-line/pan_india_drainage_lines"

# # Global drainage "on line / too close" threshold (meters)
# GLOBAL_DRAINAGE_EPS_M = 10.0

# # ============================================================
# # 3) Initialize Earth Engine (safe fallback)
# # ============================================================

# try:
#     ee.Initialize(project="gee-automation-479508")
#     EE_AVAILABLE = True
#     print("✅ Earth Engine initialized (project gee-automation-479508).")
# except Exception as e:
#     EE_AVAILABLE = False
#     print("⚠️ WARNING: Could not initialize Earth Engine:", e)

# # ============================================================
# # 4) Load rules.json
# # ============================================================

# with open("rules.json", "r", encoding="utf-8") as f:
#     RULES = json.load(f)

# print("✅ Loaded rules for structures:", list(RULES.keys()))

# # ============================================================
# # 5) Helpers
# # ============================================================

# STRUCTURE_ALIASES = {
#     "continuous_contour_trenches": "continuous_contour_trench",
#     "continuous_contour_trench_cct": "continuous_contour_trench",
#     "continuous_contour_trenches_cct": "continuous_contour_trench",

#     "staggered_contour_trenches": "staggered_contour_trench",

#     "earthen_gully_plug": "earthen_gully_plugs",
#     "earthen_gully_plugs_egp": "earthen_gully_plugs",

#     "drainage_soakage_channel": "drainage_soakage_channels",
#     "drainage_soakage_channels": "drainage_soakage_channels",

#     "trench_cum_bund_network": "trench_cum_bund",

#     # 5% model variations
#     "5_model_structure": "5_percent_model",
#     "5_percent_model_structure": "5_percent_model",
#     "5_percent_model": "5_percent_model",

#     # 30_40 model variations
#     "30_40_model_structure": "30_40_model",
#     "30_40_model": "30_40_model",
# }

# def normalize_structure_name(structure_type: str) -> str:
#     if not structure_type:
#         return ""

#     s = str(structure_type).strip().lower()

#     s = re.sub(r"\(.*?\)", " ", s)   # remove bracket text
#     s = s.replace("%", " percent ")

#     s = s.replace("&", " and ")
#     s = s.replace("/", " ")
#     s = s.replace("-", " ")

#     s = re.sub(r"[^a-z0-9\s]", " ", s)
#     s = s.replace("trenches", "trench")

#     s = "_".join(s.split()).strip("_")

#     return STRUCTURE_ALIASES.get(s, s)


# def get_structure_type(props: dict) -> str:
#     for field in STRUCTURE_FIELDS:
#         val = props.get(field)
#         if val:
#             return str(val).strip()
#     return ""


# def extract_lon_lat_from_geom(geom: dict):
#     coords = geom.get("coordinates")
#     if coords is None:
#         return None, None

#     def find_pair(c):
#         if (
#             isinstance(c, (list, tuple)) and len(c) >= 2
#             and isinstance(c[0], (int, float))
#             and isinstance(c[1], (int, float))
#         ):
#             return c[0], c[1]

#         if isinstance(c, (list, tuple)):
#             for item in c:
#                 lon, lat = find_pair(item)
#                 if lon is not None and lat is not None:
#                     return lon, lat

#         return None, None

#     return find_pair(coords)


# def build_layer_name(prefix: str, plan_number: str, district: str, block: str) -> str:
#     return f"{prefix}_{plan_number}_{district}_{block}"

# # ============================================================
# # 5.5) LULC CONFIG + METHODS (ADDED)
# # ============================================================

# LULC_ASSET = "projects/corestack-datasets/assets/datasets/LULC_v3_river_basin/pan_india_lulc_v3_2024_2025"

# LULC_NAMES = {
#     0: "Background",
#     1: "Built up",
#     2: "Kharif water",
#     3: "Kharif and rabi water",
#     4: "Kharif and rabi and zaid water",
#     5: "Croplands",
#     6: "Trees/forests",
#     7: "Barren land",
#     8: "Single Kharif cropping",
#     9: "Single Non-Kharif cropping",
#     10: "Double cropping",
#     11: "Triple cropping",
#     12: "Shrubs/Scrubs"
# }

# def _lulc_image():
#     return ee.Image(LULC_ASSET).select(0).rename("lulc")

# # A) On-spot LULC
# def compute_lulc_point(lat: float, lon: float) -> str | None:
#     if not EE_AVAILABLE:
#         return None

#     lulc = _lulc_image()
#     pt = ee.Geometry.Point([lon, lat])
#     scale = lulc.projection().nominalScale()

#     val = lulc.reduceRegion(
#         reducer=ee.Reducer.first(),
#         geometry=pt,
#         scale=scale,
#         maxPixels=1e9
#     ).get("lulc")

#     v = val.getInfo() if val else None
#     if v is None:
#         return None

#     return LULC_NAMES.get(int(round(float(v))))

# # B) Dominant LULC in 30m buffer
# def compute_lulc_buffer_dominant(lat: float, lon: float, buffer_m: int = 30) -> str | None:
#     if not EE_AVAILABLE:
#         return None

#     lulc = _lulc_image()
#     pt = ee.Geometry.Point([lon, lat])
#     buf = pt.buffer(buffer_m)
#     scale = lulc.projection().nominalScale()

#     hist = ee.Dictionary(
#         lulc.reduceRegion(
#             reducer=ee.Reducer.frequencyHistogram(),
#             geometry=buf,
#             scale=scale,
#             maxPixels=1e9,
#             tileScale=4
#         ).get("lulc")
#     )

#     # empty/masked
#     if hist.size().getInfo() == 0:
#         return None

#     keys = hist.keys()
#     counts = hist.values()

#     max_count = counts.reduce(ee.Reducer.max())
#     max_idx = counts.indexOf(max_count)

#     dom_key = ee.String(keys.get(max_idx))   # "10" or "10.0"
#     dom_id = ee.Number.parse(dom_key)        # safe parse

#     dom_val = dom_id.getInfo()
#     if dom_val is None:
#         return None

#     return LULC_NAMES.get(int(dom_val))

# # C) Downstream LULC (SAFE PLACEHOLDER for now)
# # Later you can swap this with your final D8 stepping method.
# def compute_lulc_downstream(lat: float, lon: float, n_steps: int = 3) -> str | None:
#     """
#     True downstream traversal using D8 flow direction (HydroSHEDS).
#     Moves n_steps along flow direction and returns LULC at final point.
#     """

#     if not EE_AVAILABLE:
#         return None

#     # -----------------------------
#     # Load datasets
#     # -----------------------------
#     fdir = ee.Image("WWF/HydroSHEDS/03DIR").select("b1")
#     lulc = _lulc_image()

#     pt = ee.Geometry.Point([lon, lat])
#     cell = fdir.projection().nominalScale()

#     # -----------------------------
#     # D8 direction offsets
#     # -----------------------------
#     D8 = {
#         1:  (1, 0),     # E
#         2:  (1, -1),    # SE
#         4:  (0, -1),    # S
#         8:  (-1, -1),   # SW
#         16: (-1, 0),    # W
#         32: (-1, 1),    # NW
#         64: (0, 1),     # N
#         128:(1, 1)      # NE
#     }

#     current_pt = pt

#     for _ in range(n_steps):

#         # Sample flow direction at current point
#         dir_val = fdir.reduceRegion(
#             reducer=ee.Reducer.first(),
#             geometry=current_pt,
#             scale=cell,
#             maxPixels=1e9
#         ).get("b1")

#         dir_val = dir_val.getInfo() if dir_val else None

#         if dir_val is None:
#             break

#         dir_val = int(dir_val)

#         if dir_val not in D8:
#             break

#         dx_cell, dy_cell = D8[dir_val]

#         dx_m = dx_cell * cell.getInfo()
#         dy_m = dy_cell * cell.getInfo()

#         # Move in projected coordinate system
#         pt_3857 = current_pt.transform("EPSG:3857", 1)
#         coords = pt_3857.coordinates().getInfo()

#         new_x = coords[0] + dx_m
#         new_y = coords[1] + dy_m

#         current_pt = ee.Geometry.Point([new_x, new_y], "EPSG:3857").transform("EPSG:4326", 1)

#     # -----------------------------
#     # Sample LULC at downstream point
#     # -----------------------------
#     lulc_val = lulc.reduceRegion(
#         reducer=ee.Reducer.first(),
#         geometry=current_pt,
#         scale=30,
#         maxPixels=1e9
#     ).get("lulc")

#     lulc_val = lulc_val.getInfo() if lulc_val else None

#     if lulc_val is None:
#         return None

#     return LULC_NAMES.get(int(round(float(lulc_val))))


# # Structure -> which LULC method to use
# LULC_MODE_BY_STRUCTURE = {
#     # A) On-spot
#     "farm_pond": "point",
#     "farm_bund": "point",
#     "30_40_model": "point",
#     "well": "point",
#     "soakage_pit": "point",
#     "recharge_pit": "point",
#     "rock_fill_dam": "point",
#     "graded_bund": "point",
#     "stone_bund": "point",
#     "earthen_gully_plugs": "point",

#     # B) 30m dominant
#     "canal": "buffer",
#     "diversion_drain": "buffer",
#     "drainage_soakage_channels": "buffer",
#     "check_dam": "buffer",
#     "percolation_tank": "buffer",
#     "community_pond": "buffer",
#     "trench_cum_bund": "buffer",

#     # C) downstream
#     "contour_bund": "downstream",
#     "loose_boulder_structure": "downstream",
#     "continuous_contour_trench": "downstream",
#     "staggered_contour_trench": "downstream",
#     "wat": "downstream",
# }

# def compute_lulc_auto(lat: float, lon: float, structure_type: str) -> str | None:
#     key = normalize_structure_name(structure_type)
#     mode = LULC_MODE_BY_STRUCTURE.get(key, "point")

#     if mode == "point":
#         return compute_lulc_point(lat, lon)
#     if mode == "buffer":
#         return compute_lulc_buffer_dominant(lat, lon, buffer_m=30)
#     if mode == "downstream":
#         return compute_lulc_downstream(lat, lon)

#     return compute_lulc_point(lat, lon)

# # ============================================================
# # 6) GeoServer: fetch plan sites
# # ============================================================

# def fetch_sites_from_layer(prefix: str, plan_number: str, district: str, block: str):
#     district = district.lower()
#     block = block.lower()

#     workspace = LAYER_CONFIG[prefix]
#     layer_name = build_layer_name(prefix, plan_number, district, block)
#     wfs_url = f"{GEOSERVER_BASE}{workspace}/ows"

#     params = {
#         "service": "WFS",
#         "version": "1.0.0",
#         "request": "GetFeature",
#         "typeName": f"{workspace}:{layer_name}",
#         "outputFormat": "application/json",
#     }

#     resp = requests.get(wfs_url, params=params, timeout=30)
#     resp.raise_for_status()
#     data = resp.json()

#     sites = []
#     features = data.get("features", [])

#     for idx, feat in enumerate(features):
#         geom = feat.get("geometry") or {}
#         lon, lat = extract_lon_lat_from_geom(geom)

#         props = feat.get("properties") or {}

#         if lon is None or lat is None:
#             lon = props.get("longitude")
#             lat = props.get("latitude")

#         if lon is None or lat is None:
#             continue

#         structure_type = get_structure_type(props)
#         site_id = f"{layer_name}_{idx}"

#         sites.append({
#             "id": site_id,
#             "lat": float(lat),
#             "lon": float(lon),
#             "structure_type": structure_type
#         })

#     return layer_name, sites

# # ============================================================
# # 7) GEE extractors
# # ============================================================

# def compute_slope_mean_30m(lat: float, lon: float, buffer_m: int = 30) -> float:
#     if not EE_AVAILABLE:
#         return 0.0

#     dem = ee.Image("USGS/SRTMGL1_003")
#     slope_deg = ee.Terrain.slope(dem)

#     slope_pct = (
#         slope_deg
#         .multiply(math.pi / 180.0)
#         .tan()
#         .multiply(100.0)
#         .rename("slope_pct")
#         .unmask(0)
#     )

#     pt = ee.Geometry.Point([lon, lat])
#     buf = pt.buffer(buffer_m)
#     scale = slope_pct.projection().nominalScale()

#     stats = slope_pct.reduceRegion(
#         reducer=ee.Reducer.mean(),
#         geometry=buf,
#         scale=scale,
#         bestEffort=True
#     )

#     v = stats.get("slope_pct").getInfo()
#     return round(float(v or 0.0), 2)


# def compute_catchment_minmax_30m(lat: float, lon: float, buffer_m: int = 30) -> dict:
#     if not EE_AVAILABLE:
#         return {"min": 0.0, "max": 0.0}

#     ca = (
#         ee.Image("projects/ext-datasets/assets/datasets/catchment_area_multiflow")
#         .select(0)
#         .rename("ha")
#         .unmask(0)
#     )

#     pt = ee.Geometry.Point([lon, lat])
#     buf = pt.buffer(buffer_m)
#     scale = ca.projection().nominalScale()

#     stats = ca.reduceRegion(
#         reducer=ee.Reducer.min().combine(ee.Reducer.max(), sharedInputs=True),
#         geometry=buf,
#         scale=scale,
#         bestEffort=True,
#         maxPixels=1e9
#     )

#     ca_min = stats.get("ha_min").getInfo()
#     ca_max = stats.get("ha_max").getInfo()

#     return {
#         "min": round(float(ca_min or 0.0), 2),
#         "max": round(float(ca_max or 0.0), 2),
#     }


# def compute_stream_order(lat: float, lon: float) -> int:
#     if not EE_AVAILABLE:
#         return 0

#     so = (
#         ee.Image("projects/corestack-datasets/assets/datasets/Stream_Order_Raster_India")
#         .select(0)
#         .rename("so")
#         .unmask(0)
#     )

#     pt = ee.Geometry.Point([lon, lat])
#     scale = so.projection().nominalScale()

#     stats = so.reduceRegion(
#         reducer=ee.Reducer.first(),
#         geometry=pt,
#         scale=scale,
#         bestEffort=True
#     )

#     v = stats.get("so").getInfo()
#     return int(round(float(v or 0)))


# def compute_drainage_distance_m(lat: float, lon: float, scale: int = 30) -> float:
#     if not EE_AVAILABLE:
#         return 0.0

#     pt = ee.Geometry.Point([lon, lat])
#     drainage = ee.FeatureCollection(DRAINAGE_LINES_ASSET)

#     dist_img = drainage.distance(searchRadius=10000, maxError=1)

#     stats = dist_img.reduceRegion(
#         reducer=ee.Reducer.min(),
#         geometry=pt,
#         scale=scale,
#         maxPixels=1e9
#     )

#     d = stats.get("distance").getInfo()
#     return round(float(d or 0.0), 2)

# # ============================================================
# # 8) RULES SCHEMA VALIDATION (unchanged)
# # ============================================================

# ALLOWED_PARAMS = {"slope", "stream_order", "catchment_area", "drainage_distance", "lulc"}

# def _is_num(x):
#     return isinstance(x, (int, float)) and not isinstance(x, bool)

# def _is_range_dict(d):
#     if not isinstance(d, dict):
#         return False
#     keys = set(d.keys())
#     if not keys.issubset({"min", "max"}):
#         return False
#     if "min" in d and not _is_num(d["min"]):
#         return False
#     if "max" in d and not _is_num(d["max"]):
#         return False
#     if "min" in d and "max" in d and float(d["min"]) > float(d["max"]):
#         return False
#     return True

# def _is_num_list(lst):
#     return isinstance(lst, list) and all(isinstance(x, int) for x in lst)

# def _is_str_list(lst):
#     return isinstance(lst, list) and all(isinstance(x, str) for x in lst)

# def validate_rules_schema(rules: dict):
#     issues = []
#     if not isinstance(rules, dict):
#         return ["RULES is not a dict (rules.json root must be an object)."]

#     for struct_name, struct_rules in rules.items():
#         if not isinstance(struct_rules, dict):
#             issues.append(f"[{struct_name}] structure rules must be an object/dict.")
#             continue

#         unknown_params = set(struct_rules.keys()) - ALLOWED_PARAMS
#         if unknown_params:
#             issues.append(f"[{struct_name}] has unknown params: {sorted(list(unknown_params))}")

#         if "slope" in struct_rules:
#             sr = struct_rules["slope"]
#             if not isinstance(sr, dict):
#                 issues.append(f"[{struct_name}.slope] must be an object.")
#             else:
#                 if "max" in sr and "accepted" not in sr:
#                     if not _is_num(sr["max"]):
#                         issues.append(f"[{struct_name}.slope.max] must be a number.")
#                 else:
#                     if "accepted" not in sr or not _is_range_dict(sr.get("accepted")):
#                         issues.append(f"[{struct_name}.slope.accepted] must be a range dict.")
#                     if "partially_accepted" in sr and not _is_range_dict(sr.get("partially_accepted")):
#                         issues.append(f"[{struct_name}.slope.partially_accepted] must be a range dict if present.")

#         if "catchment_area" in struct_rules:
#             cr = struct_rules["catchment_area"]
#             if not isinstance(cr, dict):
#                 issues.append(f"[{struct_name}.catchment_area] must be an object.")
#             else:
#                 if "accepted" not in cr or not _is_range_dict(cr.get("accepted")):
#                     issues.append(f"[{struct_name}.catchment_area.accepted] must be a range dict.")
#                 if "partially_accepted" in cr and not _is_range_dict(cr.get("partially_accepted")):
#                     issues.append(f"[{struct_name}.catchment_area.partially_accepted] must be a range dict if present.")

#         if "drainage_distance" in struct_rules:
#             dr = struct_rules["drainage_distance"]
#             if not isinstance(dr, dict):
#                 issues.append(f"[{struct_name}.drainage_distance] must be an object.")
#             else:
#                 if "accepted" not in dr or not _is_range_dict(dr.get("accepted")):
#                     issues.append(f"[{struct_name}.drainage_distance.accepted] must be a range dict.")
#                 if "partially_accepted" in dr and not _is_range_dict(dr.get("partially_accepted")):
#                     issues.append(f"[{struct_name}.drainage_distance.partially_accepted] must be a range dict if present.")

#         if "stream_order" in struct_rules:
#             sor = struct_rules["stream_order"]
#             if not isinstance(sor, dict):
#                 issues.append(f"[{struct_name}.stream_order] must be an object.")
#             else:
#                 if "accepted" in sor:
#                     if not _is_num_list(sor["accepted"]):
#                         issues.append(f"[{struct_name}.stream_order.accepted] must be a list of ints.")
#                 elif "valid" in sor:
#                     if not _is_num_list(sor["valid"]):
#                         issues.append(f"[{struct_name}.stream_order.valid] must be a list of ints.")
#                 else:
#                     issues.append(f"[{struct_name}.stream_order] must contain 'accepted' (or legacy 'valid').")
#                 if "partially_accepted" in sor and not _is_num_list(sor["partially_accepted"]):
#                     issues.append(f"[{struct_name}.stream_order.partially_accepted] must be a list of ints if present.")

#         if "lulc" in struct_rules:
#             lr = struct_rules["lulc"]
#             if not isinstance(lr, dict):
#                 issues.append(f"[{struct_name}.lulc] must be an object.")
#             else:
#                 if "accepted" not in lr or not _is_str_list(lr.get("accepted")):
#                     issues.append(f"[{struct_name}.lulc.accepted] must be a list of strings.")
#                 if "partially_accepted" in lr and not _is_str_list(lr.get("partially_accepted")):
#                     issues.append(f"[{struct_name}.lulc.partially_accepted] must be a list of strings if present.")
#                 if "not_accepted" in lr and not _is_str_list(lr.get("not_accepted")):
#                     issues.append(f"[{struct_name}.lulc.not_accepted] must be a list of strings if present.")

#     return issues

# schema_issues = validate_rules_schema(RULES)
# if schema_issues:
#     print("❌ RULES SCHEMA ISSUES FOUND:")
#     for i in schema_issues:
#         print(" -", i)
# else:
#     print("✅ rules.json schema validated (all patterns OK).")

# # ============================================================
# # 9) CLASSIFIERS + 10) EVALUATION ENGINE (unchanged)
# # ============================================================

# def in_range(v: float, r: dict) -> bool:
#     if not isinstance(r, dict):
#         return False
#     if "min" in r and v < float(r["min"]):
#         return False
#     if "max" in r and v > float(r["max"]):
#         return False
#     return True

# def classify_numeric(value, rule: dict, label: str):
#     if value is None or rule is None:
#         return ("not_evaluated", f"{label} not evaluated (missing value/rule).")

#     v = float(value)

#     if "max" in rule and "accepted" not in rule:
#         mx = float(rule["max"])
#         if v <= mx:
#             return ("accepted", f"{label} {v:.2f} ≤ {mx} → accepted.")
#         return ("not_accepted", f"{label} {v:.2f} > {mx} → not accepted.")

#     acc = rule.get("accepted")
#     part = rule.get("partially_accepted")

#     if isinstance(acc, dict) and in_range(v, acc):
#         return ("accepted", f"{label} {v:.2f} within accepted {acc} → accepted.")
#     if isinstance(part, dict) and in_range(v, part):
#         return ("partially_accepted", f"{label} {v:.2f} within partial {part} → partially accepted.")

#     if isinstance(acc, dict):
#         return ("not_accepted", f"{label} {v:.2f} outside accepted/partial ranges → not accepted.")

#     return ("not_evaluated", f"{label} rule format not recognized.")

# def classify_stream_order(value, rule: dict):
#     if value is None or rule is None:
#         return ("not_evaluated", "Stream order not evaluated (missing value/rule).")

#     v = int(value)
#     accepted = rule.get("accepted") or rule.get("valid", [])
#     partial = rule.get("partially_accepted", [])

#     if v in (accepted or []):
#         return ("accepted", f"Stream order {v} in {accepted} → accepted.")
#     if v in (partial or []):
#         return ("partially_accepted", f"Stream order {v} in {partial} → partially accepted.")
#     return ("not_accepted", f"Stream order {v} not in accepted/partial sets → not accepted.")

# def classify_lulc(value, rule: dict):
#     if not value or rule is None:
#         return ("not_evaluated", "LULC not evaluated (missing value/rule).")

#     v_raw = str(value).strip()
#     v = v_raw.lower()

#     acc = [str(x).strip().lower() for x in (rule.get("accepted") or [])]
#     part = [str(x).strip().lower() for x in (rule.get("partially_accepted") or [])]
#     notacc = [str(x).strip().lower() for x in (rule.get("not_accepted") or [])]

#     if v in acc:
#         return ("accepted", f"LULC '{v_raw}' is accepted.")
#     if v in part:
#         return ("partially_accepted", f"LULC '{v_raw}' is partially accepted.")
#     if v in notacc:
#         return ("not_accepted", f"LULC '{v_raw}' is not accepted.")
#     return ("not_evaluated", f"LULC '{v_raw}' not found in rule lists.")

# def evaluate_site_from_rules(site: dict) -> dict:
#     key = normalize_structure_name(site.get("structure_type", ""))
#     rules = RULES.get(key)

#     if not rules:
#         return {"suitable": False, "parameters": {}, "overall_comment": f"No rules found for structure '{key}'."}

#     params = {}
#     statuses = []
#     failures = []

#     if "slope" in rules:
#         cat, expl = classify_numeric(site.get("slope"), rules["slope"], "Slope (%)")
#         params["slope"] = {"category": cat, "value": site.get("slope"), "explanation": expl, "rule": rules["slope"]}
#         statuses.append(cat)
#         if cat == "not_accepted":
#             failures.append(expl)

#     if "catchment_area" in rules:
#         cat, expl = classify_numeric(site.get("catchment_area"), rules["catchment_area"], "Catchment (ha)")
#         params["catchment_area"] = {"category": cat, "value": site.get("catchment_area"), "explanation": expl, "rule": rules["catchment_area"]}
#         statuses.append(cat)
#         if cat == "not_accepted":
#             failures.append(expl)

#     if "stream_order" in rules:
#         cat, expl = classify_stream_order(site.get("stream_order"), rules["stream_order"])
#         params["stream_order"] = {"category": cat, "value": site.get("stream_order"), "explanation": expl, "rule": rules["stream_order"]}
#         statuses.append(cat)
#         if cat == "not_accepted":
#             failures.append(expl)

#     if "drainage_distance" in rules:
#         dd = site.get("drainage_distance")
#         if dd is None:
#             cat, expl = ("not_evaluated", "Drainage distance missing.")
#         else:
#             dd = float(dd)
#             if dd <= GLOBAL_DRAINAGE_EPS_M:
#                 cat = "not_accepted"
#                 expl = f"Rejected globally: drainage distance {dd:.1f} m ≤ {GLOBAL_DRAINAGE_EPS_M:.1f} m (on/too close to drainage line)."
#             else:
#                 cat, expl = classify_numeric(dd, rules["drainage_distance"], "Drainage distance (m)")

#         params["drainage_distance"] = {"category": cat, "value": site.get("drainage_distance"), "explanation": expl, "rule": rules["drainage_distance"]}
#         statuses.append(cat)
#         if cat == "not_accepted":
#             failures.append(expl)

#     if "lulc" in rules:
#         cat, expl = classify_lulc(site.get("lulc_class"), rules["lulc"])
#         params["lulc"] = {"category": cat, "value": site.get("lulc_class"), "explanation": expl, "rule": rules["lulc"]}
#         statuses.append(cat)
#         if cat == "not_accepted":
#             failures.append(expl)

#     suitable = ("not_accepted" not in statuses)
#     overall_comment = "Rule-based evaluation completed."
#     if not suitable and failures:
#         overall_comment += " Failures: " + " | ".join(failures[:3])

#     return {"suitable": suitable, "parameters": params, "overall_comment": overall_comment}

# # ============================================================
# # 11) API endpoints
# # ============================================================

# @app.route("/api/plan-sites", methods=["POST"])
# def api_plan_sites():
#     data = request.get_json() or {}

#     plan_number = str(data.get("plan_number", "")).strip()
#     district = str(data.get("district", "")).strip()
#     block = str(data.get("block", "")).strip()
#     layer_type = str(data.get("layer_type", "")).strip()

#     if not plan_number or not district or not block or not layer_type:
#         return jsonify({"error": "plan_number, district, block, layer_type are required"}), 400

#     if layer_type not in LAYER_CONFIG:
#         return jsonify({"error": f"layer_type must be one of {list(LAYER_CONFIG.keys())}"}), 400

#     try:
#         layer_name, sites = fetch_sites_from_layer(layer_type, plan_number, district, block)
#     except Exception as e:
#         return jsonify({"error": f"GeoServer fetch failed: {e}"}), 500

#     return jsonify({"layer_name": layer_name, "site_count": len(sites), "sites": sites})


# @app.route("/api/validate-site", methods=["POST"])
# def api_validate_site():
#     data = request.get_json() or {}

#     lat = data.get("lat")
#     lon = data.get("lon")
#     structure_type = (data.get("structure_type") or "").strip()

#     if lat is None or lon is None or not structure_type:
#         return jsonify({"error": "lat, lon, structure_type are required"}), 400

#     try:
#         lat = float(lat)
#         lon = float(lon)
#     except ValueError:
#         return jsonify({"error": "lat and lon must be numeric"}), 400

#     if not EE_AVAILABLE:
#         return jsonify({"error": "Earth Engine not available"}), 500

#     # If frontend provides lulc_class, treat as manual override. Else auto compute.
#     lulc_class = data.get("lulc_class")
#     if not lulc_class:
#         lulc_class = compute_lulc_auto(lat, lon, structure_type)

#     slope = compute_slope_mean_30m(lat, lon, buffer_m=30)
#     ca_range = compute_catchment_minmax_30m(lat, lon, buffer_m=30)
#     stream_order = compute_stream_order(lat, lon)
#     drainage_distance = compute_drainage_distance_m(lat, lon, scale=30)

#     catchment_rep = ca_range["max"]

#     site = {
#         "structure_type": structure_type,
#         "slope": slope,
#         "catchment_area": catchment_rep,
#         "stream_order": stream_order,
#         "drainage_distance": drainage_distance,
#         "lulc_class": lulc_class,
#     }

#     evaluation = evaluate_site_from_rules(site)

#     return jsonify({
#         "lat": lat,
#         "lon": lon,
#         "structure_type": structure_type,
#         "raw_values": {
#             "slope_mean_30m": slope,
#             "catchment_min_30m": ca_range["min"],
#             "catchment_max_30m": ca_range["max"],
#             "stream_order": stream_order,
#             "drainage_distance": drainage_distance,
#             "lulc_class": lulc_class,
#             "lulc_mode": LULC_MODE_BY_STRUCTURE.get(normalize_structure_name(structure_type), "point")
#         },
#         "evaluation": evaluation
#     })


# @app.route("/api/error1/submit", methods=["POST"])
# def api_submit_error1():
#     data = request.get_json() or {}

#     plan_number = str(data.get("plan_number", "")).strip()
#     district = str(data.get("district", "")).strip().lower()
#     block = str(data.get("block", "")).strip().lower()
#     layer_type = str(data.get("layer_type", "")).strip()
#     decisions = data.get("decisions") or []

#     if not plan_number or not district or not block or not decisions:
#         return jsonify({"error": "plan_number, district, block and decisions are required"}), 400

#     flagged = [d for d in decisions if d.get("status") == "flag"]
#     passed = [d for d in decisions if d.get("status") == "pass"]

#     file_exists = os.path.isfile(FLAGGED_FILE)

#     try:
#         with open(FLAGGED_FILE, "a", newline="", encoding="utf-8") as f:
#             writer = csv.writer(f)
#             if not file_exists:
#                 writer.writerow([
#                     "plan_number", "district", "block", "layer_type",
#                     "site_id", "lat", "lon", "structure_type",
#                     "status", "reason", "comments"
#                 ])

#             for d in flagged:
#                 writer.writerow([
#                     plan_number, district, block, layer_type,
#                     d.get("id", ""), d.get("lat", ""), d.get("lon", ""),
#                     d.get("structure_type", ""),
#                     d.get("status", ""), d.get("reason", ""), d.get("comments", "")
#                 ])

#     except Exception as e:
#         return jsonify({"error": f"Failed to save flagged sites: {e}"}), 500

#     return jsonify({
#         "flagged_count": len(flagged),
#         "passed_count": len(passed),
#         "passed_sites": passed
#     })


# @app.route("/api/rules-health", methods=["GET"])
# def api_rules_health():
#     issues = validate_rules_schema(RULES)
#     return jsonify({"ok": (len(issues) == 0), "issue_count": len(issues), "issues": issues})

# # ============================================================
# # 12) Start server
# # ============================================================

# if __name__ == "__main__":
#     app.run(host="127.0.0.1", port=8000, debug=True)


# --------------------------------------------------------------

#-------------------------------------------------------------



# Part -4 removing the glitches 



from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import csv
import os
import json
import math
import ee
import re

# ============================================================
# 1) Flask app setup
# ============================================================

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

# ============================================================
# 2) Config / constants
# ============================================================

GEOSERVER_BASE = "https://geoserver.core-stack.org:8443/geoserver/"
WORKS_WORKSPACE = "works"
RESOURCES_WORKSPACE = "resources"

# Which prefixes live in which workspace
LAYER_CONFIG = {
    "plan_agri": WORKS_WORKSPACE,
    "plan_gw": WORKS_WORKSPACE,
    "waterbody": RESOURCES_WORKSPACE,
}

# Try these fields in this order to infer structure type from GeoServer properties
STRUCTURE_FIELDS = ["TYPE_OF_WO", "work_type", "selected_w", "select_o_4"]

FLAGGED_FILE = "flagged_sites.csv"

# Drainage lines asset
DRAINAGE_LINES_ASSET = "projects/corestack-datasets/assets/datasets/drainage-line/pan_india_drainage_lines"

# Global drainage "on line / too close" threshold (meters)
GLOBAL_DRAINAGE_EPS_M = 10.0

# ============================================================
# 3) Initialize Earth Engine (safe fallback)
# ============================================================

try:
    ee.Initialize(project="gee-automation-479508")
    EE_AVAILABLE = True
    print("Earth Engine initialized (project gee-automation-479508).")
except Exception as e:
    EE_AVAILABLE = False
    print("WARNING: Could not initialize Earth Engine:", e)

# ============================================================
# 4) Load rules.json
# ============================================================

with open("rules.json", "r", encoding="utf-8") as f:
    RULES = json.load(f)

# ============================================================
# 4.5) Read required_inputs + rules (new format + backward compatible)
# ============================================================

DEFAULT_REQUIRED_INPUTS = ["lulc", "slope", "catchment_area", "stream_order", "drainage_distance"]

def get_structure_config(structure_type: str):
    """
    Supports both formats:
      NEW:
        RULES[key] = {"required_inputs":[...], "rules":{...}}
      OLD:
        RULES[key] = {"slope":{...}, "lulc":{...}, ...}
    Returns:
      required_inputs: list[str]
      rules: dict (parameter -> rule dict)
    """
    key = normalize_structure_name(structure_type)
    cfg = RULES.get(key)

    if not isinstance(cfg, dict) or not cfg:
        return [], None, key

    # New format
    if "rules" in cfg:
        rules = cfg.get("rules") or {}
        required = cfg.get("required_inputs")
        if not required:
            required = list(rules.keys())  # fallback: whatever rules exist
        return required, rules, key

    # Old format fallback
    rules = cfg
    required = list(rules.keys())
    return required, rules, key

print("Loaded rules for structures:", list(RULES.keys()))

# ============================================================
# 5) Helpers
# ============================================================

STRUCTURE_ALIASES = {
    "continuous_contour_trenches": "continuous_contour_trench",
    "continuous_contour_trench_cct": "continuous_contour_trench",
    "continuous_contour_trenches_cct": "continuous_contour_trench",

    "staggered_contour_trenches": "staggered_contour_trench",

    "earthen_gully_plug": "earthen_gully_plugs",
    "earthen_gully_plugs_egp": "earthen_gully_plugs",

    "drainage_soakage_channel": "drainage_soakage_channels",
    "drainage_soakage_channels": "drainage_soakage_channels",

    "trench_cum_bund_network": "trench_cum_bund",

    # 5% model variations
    "5_model_structure": "5_percent_model",
    "5_percent_model_structure": "5_percent_model",
    "5_percent_model": "5_percent_model",

    # 30_40 model variations
    "30_40_model_structure": "30_40_model",
    "30_40_model": "30_40_model",
}

def normalize_structure_name(structure_type: str) -> str:
    if not structure_type:
        return ""

    s = str(structure_type).strip().lower()

    s = re.sub(r"\(.*?\)", " ", s)   # remove bracket text
    s = s.replace("%", " percent ")

    s = s.replace("&", " and ")
    s = s.replace("/", " ")
    s = s.replace("-", " ")

    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = s.replace("trenches", "trench")

    s = "_".join(s.split()).strip("_")

    return STRUCTURE_ALIASES.get(s, s)


def get_structure_type(props: dict) -> str:
    for field in STRUCTURE_FIELDS:
        val = props.get(field)
        if val:
            return str(val).strip()
    return ""


def extract_lon_lat_from_geom(geom: dict):
    coords = geom.get("coordinates")
    if coords is None:
        return None, None

    def find_pair(c):
        if (
            isinstance(c, (list, tuple)) and len(c) >= 2
            and isinstance(c[0], (int, float))
            and isinstance(c[1], (int, float))
        ):
            return c[0], c[1]

        if isinstance(c, (list, tuple)):
            for item in c:
                lon, lat = find_pair(item)
                if lon is not None and lat is not None:
                    return lon, lat

        return None, None

    return find_pair(coords)


def build_layer_name(prefix: str, plan_number: str, district: str, block: str) -> str:
    return f"{prefix}_{plan_number}_{district}_{block}"

# ============================================================
# 5.5) LULC CONFIG + METHODS (ADDED)
# ============================================================

LULC_ASSET = "projects/corestack-datasets/assets/datasets/LULC_v3_river_basin/pan_india_lulc_v3_2024_2025"

LULC_NAMES = {
    0: "Background",
    1: "Built up",
    2: "Kharif water",
    3: "Kharif and rabi water",
    4: "Kharif and rabi and zaid water",
    5: "Croplands",
    6: "Trees/forests",
    7: "Barren land",
    8: "Single Kharif cropping",
    9: "Single Non-Kharif cropping",
    10: "Double cropping",
    11: "Triple cropping",
    12: "Shrubs/Scrubs"
}

def _lulc_image():
    return ee.Image(LULC_ASSET).select(0).rename("lulc")

# A) On-spot LULC
def compute_lulc_point(lat: float, lon: float) -> str | None:
    if not EE_AVAILABLE:
        return None

    lulc = _lulc_image()
    pt = ee.Geometry.Point([lon, lat])
    scale = lulc.projection().nominalScale()

    val = lulc.reduceRegion(
        reducer=ee.Reducer.first(),
        geometry=pt,
        scale=scale,
        maxPixels=1e9
    ).get("lulc")

    v = val.getInfo() if val else None
    if v is None:
        return None

    return LULC_NAMES.get(int(round(float(v))))

# B) Dominant LULC in 30m buffer
def compute_lulc_buffer_dominant(lat: float, lon: float, buffer_m: int = 30) -> str | None:
    if not EE_AVAILABLE:
        return None

    lulc = _lulc_image()
    pt = ee.Geometry.Point([lon, lat])
    buf = pt.buffer(buffer_m)
    scale = lulc.projection().nominalScale()

    hist = ee.Dictionary(
        lulc.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=buf,
            scale=scale,
            maxPixels=1e9,
            tileScale=4
        ).get("lulc")
    )

    # empty/masked
    if hist.size().getInfo() == 0:
        return None

    keys = hist.keys()
    counts = hist.values()

    max_count = counts.reduce(ee.Reducer.max())
    max_idx = counts.indexOf(max_count)

    dom_key = ee.String(keys.get(max_idx))   # "10" or "10.0"
    dom_id = ee.Number.parse(dom_key)        # safe parse

    dom_val = dom_id.getInfo()
    if dom_val is None:
        return None

    return LULC_NAMES.get(int(dom_val))

# C) Downstream LULC (SAFE PLACEHOLDER for now)
# Later you can swap this with your final D8 stepping method.
def compute_lulc_downstream(lat: float, lon: float, n_steps: int = 3) -> str | None:
    """
    True downstream traversal using D8 flow direction (HydroSHEDS).
    Moves n_steps along flow direction and returns LULC at final point.
    """

    if not EE_AVAILABLE:
        return None

    # -----------------------------
    # Load datasets
    # -----------------------------
    fdir = ee.Image("WWF/HydroSHEDS/03DIR").select("b1")
    lulc = _lulc_image()

    pt = ee.Geometry.Point([lon, lat])
    cell = fdir.projection().nominalScale()

    # -----------------------------
    # D8 direction offsets
    # -----------------------------
    D8 = {
        1:  (1, 0),     # E
        2:  (1, -1),    # SE
        4:  (0, -1),    # S
        8:  (-1, -1),   # SW
        16: (-1, 0),    # W
        32: (-1, 1),    # NW
        64: (0, 1),     # N
        128:(1, 1)      # NE
    }

    current_pt = pt

    for _ in range(n_steps):

        # Sample flow direction at current point
        dir_val = fdir.reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=current_pt,
            scale=cell,
            maxPixels=1e9
        ).get("b1")

        dir_val = dir_val.getInfo() if dir_val else None

        if dir_val is None:
            break

        dir_val = int(dir_val)

        if dir_val not in D8:
            break

        dx_cell, dy_cell = D8[dir_val]

        dx_m = dx_cell * cell.getInfo()
        dy_m = dy_cell * cell.getInfo()

        # Move in projected coordinate system
        pt_3857 = current_pt.transform("EPSG:3857", 1)
        coords = pt_3857.coordinates().getInfo()

        new_x = coords[0] + dx_m
        new_y = coords[1] + dy_m

        current_pt = ee.Geometry.Point([new_x, new_y], "EPSG:3857").transform("EPSG:4326", 1)

    # -----------------------------
    # Sample LULC at downstream point
    # -----------------------------
    lulc_val = lulc.reduceRegion(
        reducer=ee.Reducer.first(),
        geometry=current_pt,
        scale=30,
        maxPixels=1e9
    ).get("lulc")

    lulc_val = lulc_val.getInfo() if lulc_val else None

    if lulc_val is None:
        return None

    return LULC_NAMES.get(int(round(float(lulc_val))))


# Structure -> which LULC method to use
LULC_MODE_BY_STRUCTURE = {
    # A) On-spot
    "farm_pond": "point",
    "farm_bund": "point",
    "30_40_model": "point",
    "well": "point",
    "soakage_pit": "point",
    "recharge_pit": "point",
    "rock_fill_dam": "point",
    "graded_bund": "point",
    "stone_bund": "point",
    "earthen_gully_plugs": "point",

    # B) 30m dominant
    "canal": "buffer",
    "diversion_drain": "buffer",
    "drainage_soakage_channels": "buffer",
    "check_dam": "buffer",
    "percolation_tank": "buffer",
    "community_pond": "buffer",
    "trench_cum_bund": "buffer",

    # C) downstream
    "contour_bund": "downstream",
    "loose_boulder_structure": "downstream",
    "continuous_contour_trench": "downstream",
    "staggered_contour_trench": "downstream",
    "wat": "downstream",
}

def compute_lulc_auto(lat: float, lon: float, structure_type: str) -> str | None:
    key = normalize_structure_name(structure_type)
    mode = LULC_MODE_BY_STRUCTURE.get(key, "point")

    if mode == "point":
        return compute_lulc_point(lat, lon)
    if mode == "buffer":
        return compute_lulc_buffer_dominant(lat, lon, buffer_m=30)
    if mode == "downstream":
        return compute_lulc_downstream(lat, lon)

    return compute_lulc_point(lat, lon)

# ============================================================
# 6) GeoServer: fetch plan sites
# ============================================================

def fetch_sites_from_layer(prefix: str, plan_number: str, district: str, block: str):
    district = district.lower()
    block = block.lower()

    workspace = LAYER_CONFIG[prefix]
    layer_name = build_layer_name(prefix, plan_number, district, block)
    wfs_url = f"{GEOSERVER_BASE}{workspace}/ows"

    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature",
        "typeName": f"{workspace}:{layer_name}",
        "outputFormat": "application/json",
    }

    resp = requests.get(wfs_url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    sites = []
    features = data.get("features", [])

    for idx, feat in enumerate(features):
        geom = feat.get("geometry") or {}
        lon, lat = extract_lon_lat_from_geom(geom)

        props = feat.get("properties") or {}

        if lon is None or lat is None:
            lon = props.get("longitude")
            lat = props.get("latitude")

        if lon is None or lat is None:
            continue

        structure_type = get_structure_type(props)
        site_id = f"{layer_name}_{idx}"

        sites.append({
            "id": site_id,
            "lat": float(lat),
            "lon": float(lon),
            "structure_type": structure_type
        })

    return layer_name, sites

# ============================================================
# 7) GEE extractors
# ============================================================

def compute_slope_mean_30m(lat: float, lon: float, buffer_m: int = 30) -> float:
    if not EE_AVAILABLE:
        return 0.0

    dem = ee.Image("USGS/SRTMGL1_003")
    slope_deg = ee.Terrain.slope(dem)

    slope_pct = (
        slope_deg
        .multiply(math.pi / 180.0)
        .tan()
        .multiply(100.0)
        .rename("slope_pct")
        .unmask(0)
    )

    pt = ee.Geometry.Point([lon, lat])
    buf = pt.buffer(buffer_m)
    scale = slope_pct.projection().nominalScale()

    stats = slope_pct.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=buf,
        scale=scale,
        bestEffort=True
    )

    v = stats.get("slope_pct").getInfo()
    return round(float(v or 0.0), 2)


def compute_catchment_minmax_30m(lat: float, lon: float, buffer_m: int = 30) -> dict:
    if not EE_AVAILABLE:
        return {"min": 0.0, "max": 0.0}

    ca = (
        ee.Image("projects/ext-datasets/assets/datasets/catchment_area_multiflow")
        .select(0)
        .rename("ha")
        .unmask(0)
    )

    pt = ee.Geometry.Point([lon, lat])
    buf = pt.buffer(buffer_m)
    scale = ca.projection().nominalScale()

    stats = ca.reduceRegion(
        reducer=ee.Reducer.min().combine(ee.Reducer.max(), sharedInputs=True),
        geometry=buf,
        scale=scale,
        bestEffort=True,
        maxPixels=1e9
    )

    ca_min = stats.get("ha_min").getInfo()
    ca_max = stats.get("ha_max").getInfo()

    return {
        "min": round(float(ca_min or 0.0), 2),
        "max": round(float(ca_max or 0.0), 2),
    }


def compute_stream_order(lat: float, lon: float) -> int:
    if not EE_AVAILABLE:
        return 0

    so = (
        ee.Image("projects/corestack-datasets/assets/datasets/Stream_Order_Raster_India")
        .select(0)
        .rename("so")
        .unmask(0)
    )

    pt = ee.Geometry.Point([lon, lat])
    scale = so.projection().nominalScale()

    stats = so.reduceRegion(
        reducer=ee.Reducer.first(),
        geometry=pt,
        scale=scale,
        bestEffort=True
    )

    v = stats.get("so").getInfo()
    return int(round(float(v or 0)))


def compute_drainage_distance_m(lat: float, lon: float, scale: int = 30) -> float:
    if not EE_AVAILABLE:
        return 0.0

    pt = ee.Geometry.Point([lon, lat])
    drainage = ee.FeatureCollection(DRAINAGE_LINES_ASSET)

    dist_img = drainage.distance(searchRadius=10000, maxError=1)

    stats = dist_img.reduceRegion(
        reducer=ee.Reducer.min(),
        geometry=pt,
        scale=scale,
        maxPixels=1e9
    )

    d = stats.get("distance").getInfo()
    return round(float(d or 0.0), 2)

# ============================================================
# 8) RULES SCHEMA VALIDATION (unchanged)
# ============================================================

ALLOWED_PARAMS = {"slope", "stream_order", "catchment_area", "drainage_distance", "lulc"}

def _is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)

def _is_range_dict(d):
    if not isinstance(d, dict):
        return False
    keys = set(d.keys())
    if not keys.issubset({"min", "max"}):
        return False
    if "min" in d and not _is_num(d["min"]):
        return False
    if "max" in d and not _is_num(d["max"]):
        return False
    if "min" in d and "max" in d and float(d["min"]) > float(d["max"]):
        return False
    return True

def _is_num_list(lst):
    return isinstance(lst, list) and all(isinstance(x, int) for x in lst)

def _is_str_list(lst):
    return isinstance(lst, list) and all(isinstance(x, str) for x in lst)

def validate_rules_schema(rules: dict):
    issues = []
    if not isinstance(rules, dict):
        return ["RULES is not a dict (rules.json root must be an object)."]

    for struct_name, struct_rules in rules.items():
        if not isinstance(struct_rules, dict):
            issues.append(f"[{struct_name}] structure rules must be an object/dict.")
            continue
        # Support new format {required_inputs, rules:{...}}
        if "rules" in struct_rules:
            struct_rules = struct_rules.get("rules") or {}
        unknown_params = set(struct_rules.keys()) - ALLOWED_PARAMS
        if unknown_params:
            issues.append(f"[{struct_name}] has unknown params: {sorted(list(unknown_params))}")

        if "slope" in struct_rules:
            sr = struct_rules["slope"]
            if not isinstance(sr, dict):
                issues.append(f"[{struct_name}.slope] must be an object.")
            else:
                if "max" in sr and "accepted" not in sr:
                    if not _is_num(sr["max"]):
                        issues.append(f"[{struct_name}.slope.max] must be a number.")
                else:
                    if "accepted" not in sr or not _is_range_dict(sr.get("accepted")):
                        issues.append(f"[{struct_name}.slope.accepted] must be a range dict.")
                    if "partially_accepted" in sr and not _is_range_dict(sr.get("partially_accepted")):
                        issues.append(f"[{struct_name}.slope.partially_accepted] must be a range dict if present.")

        if "catchment_area" in struct_rules:
            cr = struct_rules["catchment_area"]
            if not isinstance(cr, dict):
                issues.append(f"[{struct_name}.catchment_area] must be an object.")
            else:
                if "accepted" not in cr or not _is_range_dict(cr.get("accepted")):
                    issues.append(f"[{struct_name}.catchment_area.accepted] must be a range dict.")
                if "partially_accepted" in cr and not _is_range_dict(cr.get("partially_accepted")):
                    issues.append(f"[{struct_name}.catchment_area.partially_accepted] must be a range dict if present.")

        if "drainage_distance" in struct_rules:
            dr = struct_rules["drainage_distance"]
            if not isinstance(dr, dict):
                issues.append(f"[{struct_name}.drainage_distance] must be an object.")
            else:
                if "accepted" not in dr or not _is_range_dict(dr.get("accepted")):
                    issues.append(f"[{struct_name}.drainage_distance.accepted] must be a range dict.")
                if "partially_accepted" in dr and not _is_range_dict(dr.get("partially_accepted")):
                    issues.append(f"[{struct_name}.drainage_distance.partially_accepted] must be a range dict if present.")

        if "stream_order" in struct_rules:
            sor = struct_rules["stream_order"]
            if not isinstance(sor, dict):
                issues.append(f"[{struct_name}.stream_order] must be an object.")
            else:
                if "accepted" in sor:
                    if not _is_num_list(sor["accepted"]):
                        issues.append(f"[{struct_name}.stream_order.accepted] must be a list of ints.")
                elif "valid" in sor:
                    if not _is_num_list(sor["valid"]):
                        issues.append(f"[{struct_name}.stream_order.valid] must be a list of ints.")
                else:
                    issues.append(f"[{struct_name}.stream_order] must contain 'accepted' (or legacy 'valid').")
                if "partially_accepted" in sor and not _is_num_list(sor["partially_accepted"]):
                    issues.append(f"[{struct_name}.stream_order.partially_accepted] must be a list of ints if present.")

        if "lulc" in struct_rules:
            lr = struct_rules["lulc"]
            if not isinstance(lr, dict):
                issues.append(f"[{struct_name}.lulc] must be an object.")
            else:
                if "accepted" not in lr or not _is_str_list(lr.get("accepted")):
                    issues.append(f"[{struct_name}.lulc.accepted] must be a list of strings.")
                if "partially_accepted" in lr and not _is_str_list(lr.get("partially_accepted")):
                    issues.append(f"[{struct_name}.lulc.partially_accepted] must be a list of strings if present.")
                if "not_accepted" in lr and not _is_str_list(lr.get("not_accepted")):
                    issues.append(f"[{struct_name}.lulc.not_accepted] must be a list of strings if present.")

    return issues

schema_issues = validate_rules_schema(RULES)
if schema_issues:
    print("RULES SCHEMA ISSUES FOUND:")
    for i in schema_issues:
        print(" -", i)
else:
    print("rules.json schema validated (all patterns OK).")

# ============================================================
# 9) CLASSIFIERS + 10) EVALUATION ENGINE (unchanged)
# ============================================================

def in_range(v: float, r: dict) -> bool:
    if not isinstance(r, dict):
        return False
    if "min" in r and v < float(r["min"]):
        return False
    if "max" in r and v > float(r["max"]):
        return False
    return True

def classify_numeric(value, rule: dict, label: str):
    if value is None or rule is None:
        return ("not_evaluated", f"{label} not evaluated (missing value/rule).")

    v = float(value)

    if "max" in rule and "accepted" not in rule:
        mx = float(rule["max"])
        if v <= mx:
            return ("accepted", f"{label} {v:.2f} ≤ {mx} → accepted.")
        return ("not_accepted", f"{label} {v:.2f} > {mx} → not accepted.")

    acc = rule.get("accepted")
    part = rule.get("partially_accepted")

    if isinstance(acc, dict) and in_range(v, acc):
        return ("accepted", f"{label} {v:.2f} within accepted {acc} → accepted.")
    if isinstance(part, dict) and in_range(v, part):
        return ("partially_accepted", f"{label} {v:.2f} within partial {part} → partially accepted.")

    if isinstance(acc, dict):
        return ("not_accepted", f"{label} {v:.2f} outside accepted/partial ranges → not accepted.")

    return ("not_evaluated", f"{label} rule format not recognized.")

def classify_stream_order(value, rule: dict):
    if value is None or rule is None:
        return ("not_evaluated", "Stream order not evaluated (missing value/rule).")

    v = int(value)
    accepted = rule.get("accepted") or rule.get("valid", [])
    partial = rule.get("partially_accepted", [])

    if v in (accepted or []):
        return ("accepted", f"Stream order {v} in {accepted} → accepted.")
    if v in (partial or []):
        return ("partially_accepted", f"Stream order {v} in {partial} → partially accepted.")
    return ("not_accepted", f"Stream order {v} not in accepted/partial sets → not accepted.")

def classify_lulc(value, rule: dict):
    if not value or rule is None:
        return ("not_evaluated", "LULC not evaluated (missing value/rule).")

    v_raw = str(value).strip()
    v = v_raw.lower()

    acc = [str(x).strip().lower() for x in (rule.get("accepted") or [])]
    part = [str(x).strip().lower() for x in (rule.get("partially_accepted") or [])]
    notacc = [str(x).strip().lower() for x in (rule.get("not_accepted") or [])]

    if v in acc:
        return ("accepted", f"LULC '{v_raw}' is accepted.")
    if v in part:
        return ("partially_accepted", f"LULC '{v_raw}' is partially accepted.")
    if v in notacc:
        return ("not_accepted", f"LULC '{v_raw}' is not accepted.")
    return ("not_evaluated", f"LULC '{v_raw}' not found in rule lists.")

def evaluate_site_from_rules(site: dict) -> dict:
    key = normalize_structure_name(site.get("structure_type", ""))
    cfg = RULES.get(key)
    if not cfg:
        return {"suitable": False, "parameters": {}, "overall_comment": f"No rules found for structure '{key}'."}

    rules = cfg.get("rules") if isinstance(cfg, dict) and "rules" in cfg else cfg

    if not rules:
        return {"suitable": False, "parameters": {}, "overall_comment": f"No rules found for structure '{key}'."}

    params = {}
    statuses = []
    failures = []

    if "slope" in rules:
        cat, expl = classify_numeric(site.get("slope"), rules["slope"], "Slope (%)")
        params["slope"] = {"category": cat, "value": site.get("slope"), "explanation": expl, "rule": rules["slope"]}
        statuses.append(cat)
        if cat == "not_accepted":
            failures.append(expl)

    if "catchment_area" in rules:
        cat, expl = classify_numeric(site.get("catchment_area"), rules["catchment_area"], "Catchment (ha)")
        params["catchment_area"] = {"category": cat, "value": site.get("catchment_area"), "explanation": expl, "rule": rules["catchment_area"]}
        statuses.append(cat)
        if cat == "not_accepted":
            failures.append(expl)

    if "stream_order" in rules:
        cat, expl = classify_stream_order(site.get("stream_order"), rules["stream_order"])
        params["stream_order"] = {"category": cat, "value": site.get("stream_order"), "explanation": expl, "rule": rules["stream_order"]}
        statuses.append(cat)
        if cat == "not_accepted":
            failures.append(expl)

    if "drainage_distance" in rules:
        dd = site.get("drainage_distance")
        if dd is None:
            cat, expl = ("not_evaluated", "Drainage distance missing.")
        else:
            dd = float(dd)
            if dd <= GLOBAL_DRAINAGE_EPS_M:
                cat = "not_accepted"
                expl = f"Rejected globally: drainage distance {dd:.1f} m ≤ {GLOBAL_DRAINAGE_EPS_M:.1f} m (on/too close to drainage line)."
            else:
                cat, expl = classify_numeric(dd, rules["drainage_distance"], "Drainage distance (m)")

        params["drainage_distance"] = {"category": cat, "value": site.get("drainage_distance"), "explanation": expl, "rule": rules["drainage_distance"]}
        statuses.append(cat)
        if cat == "not_accepted":
            failures.append(expl)

    if "lulc" in rules:
        cat, expl = classify_lulc(site.get("lulc_class"), rules["lulc"])
        params["lulc"] = {"category": cat, "value": site.get("lulc_class"), "explanation": expl, "rule": rules["lulc"]}
        statuses.append(cat)
        if cat == "not_accepted":
            failures.append(expl)

    # Final decision logic
    is_recommended = ("not_accepted" not in statuses)

    final_decision = "Recommended" if is_recommended else "Not Recommended"

    overall_comment = "Rule-based evaluation completed."
    if not is_recommended and failures:
        overall_comment += " Failures: " + " | ".join(failures[:3])

    return {
        "recommended": is_recommended,
        "final_decision": final_decision,
        "parameters": params,
        "suitable": is_recommended,
        "overall_comment": overall_comment
    }
# ============================================================
# 11) API endpoints
# ============================================================

@app.route("/api/plan-sites", methods=["POST"])
def api_plan_sites():
    data = request.get_json() or {}

    plan_number = str(data.get("plan_number", "")).strip()
    district = str(data.get("district", "")).strip()
    block = str(data.get("block", "")).strip()
    layer_type = str(data.get("layer_type", "")).strip()

    if not plan_number or not district or not block or not layer_type:
        return jsonify({"error": "plan_number, district, block, layer_type are required"}), 400

    if layer_type not in LAYER_CONFIG:
        return jsonify({"error": f"layer_type must be one of {list(LAYER_CONFIG.keys())}"}), 400

    try:
        layer_name, sites = fetch_sites_from_layer(layer_type, plan_number, district, block)
    except Exception as e:
        return jsonify({"error": f"GeoServer fetch failed: {e}"}), 500

    return jsonify({"layer_name": layer_name, "site_count": len(sites), "sites": sites})


@app.route("/api/validate-site", methods=["POST"])
def api_validate_site():
    data = request.get_json() or {}

    lat = data.get("lat")
    lon = data.get("lon")
    structure_type = (data.get("structure_type") or "").strip()

    if lat is None or lon is None or not structure_type:
        return jsonify({"error": "lat, lon, structure_type are required"}), 400

    try:
        lat = float(lat)
        lon = float(lon)
    except ValueError:
        return jsonify({"error": "lat and lon must be numeric"}), 400

    if not EE_AVAILABLE:
        return jsonify({"error": "Earth Engine not available"}), 500

    # If frontend provides lulc_class, treat as manual override. Else auto compute.
    lulc_class = data.get("lulc_class")
    if not lulc_class:
        lulc_class = compute_lulc_auto(lat, lon, structure_type)


    required_inputs, struct_rules, key = get_structure_config(structure_type)

    if not struct_rules:
        return jsonify({"error": f"No rules found for structure '{key}'"}), 400

    # manual override from frontend (optional)
    lulc_class = data.get("lulc_class")

    # Compute only what is required
    slope = None
    ca_range = {"min": None, "max": None}
    stream_order = None
    drainage_distance = None

    if "lulc" in required_inputs:
        if not lulc_class:
            lulc_class = compute_lulc_auto(lat, lon, structure_type)

    if "slope" in required_inputs:
        slope = compute_slope_mean_30m(lat, lon, buffer_m=30)

    if "catchment_area" in required_inputs:
        ca_range = compute_catchment_minmax_30m(lat, lon, buffer_m=30)

    if "stream_order" in required_inputs:
        stream_order = compute_stream_order(lat, lon)

    if "drainage_distance" in required_inputs:
        drainage_distance = compute_drainage_distance_m(lat, lon, scale=30)

    catchment_rep = ca_range["max"] if ca_range["max"] is not None else None

    site = {
        "structure_type": structure_type,
        "slope": slope,
        "catchment_area": catchment_rep,
        "stream_order": stream_order,
        "drainage_distance": drainage_distance,
        "lulc_class": lulc_class,
    }

    evaluation = evaluate_site_from_rules(site)


    return jsonify({
        "lat": lat,
        "lon": lon,
        "structure_type": structure_type,
        "raw_values": {
            "slope_mean_30m": slope,
            "catchment_min_30m": ca_range["min"],
            "catchment_max_30m": ca_range["max"],
            "stream_order": stream_order,
            "drainage_distance": drainage_distance,
            "lulc_class": lulc_class,
            "lulc_mode": LULC_MODE_BY_STRUCTURE.get(normalize_structure_name(structure_type), "point")
        },
        "evaluation": evaluation
    })


@app.route("/api/error1/submit", methods=["POST"])
def api_submit_error1():
    data = request.get_json() or {}

    plan_number = str(data.get("plan_number", "")).strip()
    district = str(data.get("district", "")).strip().lower()
    block = str(data.get("block", "")).strip().lower()
    layer_type = str(data.get("layer_type", "")).strip()
    decisions = data.get("decisions") or []

    if not plan_number or not district or not block or not decisions:
        return jsonify({"error": "plan_number, district, block and decisions are required"}), 400

    flagged = [d for d in decisions if d.get("status") == "flag"]
    passed = [d for d in decisions if d.get("status") == "pass"]

    file_exists = os.path.isfile(FLAGGED_FILE)

    try:
        with open(FLAGGED_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    "plan_number", "district", "block", "layer_type",
                    "site_id", "lat", "lon", "structure_type",
                    "status", "reason", "comments"
                ])

            for d in flagged:
                writer.writerow([
                    plan_number, district, block, layer_type,
                    d.get("id", ""), d.get("lat", ""), d.get("lon", ""),
                    d.get("structure_type", ""),
                    d.get("status", ""), d.get("reason", ""), d.get("comments", "")
                ])

    except Exception as e:
        return jsonify({"error": f"Failed to save flagged sites: {e}"}), 500

    return jsonify({
        "flagged_count": len(flagged),
        "passed_count": len(passed),
        "passed_sites": passed
    })


@app.route("/api/rules-health", methods=["GET"])
def api_rules_health():
    issues = validate_rules_schema(RULES)
    return jsonify({"ok": (len(issues) == 0), "issue_count": len(issues), "issues": issues})

# ============================================================
# 12) Start server
# ============================================================

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)

