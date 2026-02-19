
# # .\venv\Scripts\Activate
# # python app.py

# from flask import Flask, jsonify, request
# from flask_cors import CORS
# import requests
# import csv
# import os
# import json
# import math
# import ee


# app = Flask(__name__)
# CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

# GEOSERVER_BASE = "https://geoserver.core-stack.org:8443/geoserver/"
# WORKS_WORKSPACE = "works"
# RESOURCES_WORKSPACE = "resources"

# # Initialize Google Earth Engine with safe fallback
# try:
#     ee.Initialize(project='gee-automation-479508')
#     EE_AVAILABLE = True
#     print("Earth Engine initialized successfully with project gee-automation-479508.")
# except Exception as e:
#     EE_AVAILABLE = False
#     print("WARNING: Could not initialize Earth Engine:", e)




# FLAGGED_FILE = "flagged_sites.csv"

# # Which prefixes live in which workspace
# LAYER_CONFIG = {
#     "plan_agri": WORKS_WORKSPACE,
#     "plan_gw": WORKS_WORKSPACE,
#     "waterbody": RESOURCES_WORKSPACE,  
# }

# with open("rules.json", "r", encoding="utf-8") as f:
#     RULES = json.load(f)

# print("Loaded rules for structures:", [k for k in RULES.keys() if k != "global"])

# # We will try these field names (in this order) to get structure type
# STRUCTURE_FIELDS = [
#     "TYPE_OF_WO",   # plan_agri / plan_gw
#     "work_type",    # plan_agri / plan_gw
#     "selected_w",   # sometimes used in agri
#     "select_o_4"    # waterbody structure type (Community Pond, Farm pond, etc.)
# ]









# def build_layer_name(prefix: str, plan_number: str, district: str, block: str) -> str:
#     """
#     Example:
#     prefix="plan_gw", plan_number="116", district="bhilwara", block="mandalgarh"
#     -> "plan_gw_116_bhilwara_mandalgarh"
#     """
#     return f"{prefix}_{plan_number}_{district}_{block}"


# def get_structure_type(props: dict) -> str:
#     """
#     Try to get structure name from TYPE_OF_WO, work_type, or selected_w.
#     """
#     for field in STRUCTURE_FIELDS:
#         val = props.get(field)
#         if val:
#             return str(val).strip()
#     return ""


# def extract_lon_lat_from_geom(geom: dict):
#     """
#     Tries to extract a [lon, lat] pair from a GeoJSON geometry.
#     Works for Point and Polygon/MultiPolygon by digging into nested coords.
#     """
#     coords = geom.get("coordinates")
#     if coords is None:
#         return None, None

#     def find_pair(c):
#         # If this is already a [lon, lat] pair (both numbers), return it
#         if (
#             isinstance(c, (list, tuple)) and len(c) >= 2
#             and isinstance(c[0], (int, float))
#             and isinstance(c[1], (int, float))
#         ):
#             return c[0], c[1]

#         # If it's a nested list, search inside
#         if isinstance(c, (list, tuple)):
#             for item in c:
#                 lon, lat = find_pair(item)
#                 if lon is not None and lat is not None:
#                     return lon, lat

#         return None, None

#     return find_pair(coords)



# def fetch_sites_from_layer(prefix: str, plan_number: str, district: str, block: str):
#     """
#     Calls GeoServer WFS for the given plan layer and extracts:
#     - id
#     - lat, lon
#     - structure_type
#     """
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
#         "outputFormat": "application/json"
#     }

#     resp = requests.get(wfs_url, params=params, timeout=30)
#     resp.raise_for_status()
#     data = resp.json()

#     sites = []
#     features = data.get("features", [])

#     for idx, feat in enumerate(features):
#         geom = feat.get("geometry") or {}

#         # First try to extract lon/lat from geometry (works for points + polygons)
#         lon, lat = extract_lon_lat_from_geom(geom)

#         # Fallback: use properties.longitude / latitude if geometry is missing/weird
#         props = feat.get("properties") or {}
#         if lon is None or lat is None:
#             lon = props.get("longitude")
#             lat = props.get("latitude")

#         # If we still don't have coordinates, skip this feature
#         if lon is None or lat is None:
#             continue

#         structure_type = get_structure_type(props)
#         site_id = f"{layer_name}_{idx}"

#         site = {
#             "id": site_id,
#             "lat": float(lat),
#             "lon": float(lon),
#             "structure_type": structure_type,
#         }
#         sites.append(site)

#     return layer_name, sites

# def compute_slope_mean_30m(lat: float, lon: float, buffer_m: int = 30) -> float:
#     """
#     Compute mean slope (%) within a 30 m buffer around (lat, lon).
#     Returns a float rounded to 2 decimal places.
#     If Earth Engine is not available, returns a dummy value.
#     """
#     if not EE_AVAILABLE:
#         print("EE not available, returning dummy slope value 4.0")
#         # still round to 2 decimals for consistency
#         return round(4.0, 2)

#     # 1) DEM and slope (%)
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

#     # 2) Geometry
#     point = ee.Geometry.Point([lon, lat])
#     buffer_geom = point.buffer(buffer_m)

#     # 3) Use native scale of slope image
#     scale = slope_pct.projection().nominalScale()

#     stats = slope_pct.reduceRegion(
#         reducer=ee.Reducer.mean(),
#         geometry=buffer_geom,
#         scale=scale,
#         bestEffort=True,
#     )

#     slope_mean = stats.get("slope_pct")

#     value = slope_mean.getInfo()
#     if value is None:
#         return 0.0

#     #  round to 2 decimal places here
#     return round(float(value), 2)



# @app.route("/api/validate-slope", methods=["POST"])
# def validate_slope():
#     """
#     Validate a single site based only on slope (mean in 30 m buffer).

#     Input JSON:
#     {
#       "lat": 25.3290703,
#       "lon": 75.22412015,
#       "structure_type": "Check dam"
#     }

#     Output JSON:
#     {
#       "lat": ...,
#       "lon": ...,
#       "structure_type": "...",
#       "slope_mean_30m": ...,
#       "suitable": true/false,
#       "reasons": [...]
#     }
#     """
#     data = request.get_json() or {}

#     lat = data.get("lat")
#     lon = data.get("lon")
#     structure_type = data.get("structure_type")

#     if lat is None or lon is None or not structure_type:
#         return jsonify({
#             "error": "lat, lon and structure_type are required"
#         }), 400

#     try:
#         lat = float(lat)
#         lon = float(lon)
#     except ValueError:
#         return jsonify({"error": "lat and lon must be numeric"}), 400

#     try:
#         slope_mean = compute_slope_mean_30m(lat, lon, buffer_m=30)
#     except Exception as e:
#         return jsonify({"error": f"Failed to compute slope: {e}"}), 500

#     # Build site object for the rule engine
#     site = {
#         "structure_type": structure_type,
#         "slope": slope_mean,
#         "catchment_area": None,
#         "stream_order": None,
#         "lulc_class": None,
#         "drainage_distance": None,
#     }

#     eval_result = evaluate_site_from_rules(site)


#     return jsonify({
#         "lat": lat,
#         "lon": lon,
#         "structure_type": structure_type,
#         "slope_mean_30m": slope_mean,
#         "suitable": eval_result["suitable"],
#         "reasons": eval_result["reasons"],
#     })




# def compute_catchment_minmax_30m(lat: float, lon: float, buffer_m: int = 30):
#     """
#     Compute MIN and MAX catchment area (ha) within a 30 m buffer
#     around (lat, lon), using the catchment_area_multiflow raster.

#     Returns a dict:
#       {
#         "min": float,   # rounded to 2 decimals
#         "max": float    # rounded to 2 decimals
#       }
#     """
#     if not EE_AVAILABLE:
#         print("EE not available, returning dummy CA range.")
#         return {"min": 0.0, "max": 0.0}

#     # 1) Load catchment area image (ha)
#     ca = (
#         ee.Image("projects/ext-datasets/assets/datasets/catchment_area_multiflow")
#         .select(0)
#         .rename("ha")
#         .unmask(0)  # fill missing with 0
#     )

#     # 2) Geometry: point and 30 m buffer
#     point = ee.Geometry.Point([lon, lat])
#     buffer_geom = point.buffer(buffer_m)

#     # 3) Native scale of the image
#     scale = ca.projection().nominalScale()

#     # 4) Reduce region: MIN + MAX in one go
#     stats = ca.reduceRegion(
#         reducer=ee.Reducer.min().combine(
#             reducer2=ee.Reducer.max(),
#             sharedInputs=True
#         ),
#         geometry=buffer_geom,
#         scale=scale,
#         bestEffort=True,
#     )

#     ca_min = stats.get("ha_min")
#     ca_max = stats.get("ha_max")

#     # Convert EE objects -> Python numbers
#     ca_min_val = ca_min.getInfo() if ca_min is not None else None
#     ca_max_val = ca_max.getInfo() if ca_max is not None else None

#     # Handle None safely
#     if ca_min_val is None:
#         ca_min_val = 0.0
#     if ca_max_val is None:
#         ca_max_val = 0.0

#     return {
#         "min": round(float(ca_min_val), 2),
#         "max": round(float(ca_max_val), 2),
#     }


# @app.route("/api/compute-catchment-range", methods=["POST"])
# def compute_catchment_range():
#     """
#     Test endpoint: returns catchment MIN and MAX (ha) in 30 m buffer.

#     Input JSON:
#     {
#       "lat": 25.32907,
#       "lon": 75.22412
#     }
#     """
#     data = request.get_json() or {}

#     lat = data.get("lat")
#     lon = data.get("lon")

#     if lat is None or lon is None:
#         return jsonify({"error": "lat and lon are required"}), 400

#     try:
#         lat = float(lat)
#         lon = float(lon)
#     except ValueError:
#         return jsonify({"error": "lat and lon must be numeric"}), 400

#     try:
#         ca_range = compute_catchment_minmax_30m(lat, lon, buffer_m=30)
#     except Exception as e:
#         return jsonify({"error": f"Failed to compute catchment range: {e}"}), 500

#     return jsonify({
#         "lat": lat,
#         "lon": lon,
#         "catchment_min_30m": ca_range["min"],
#         "catchment_max_30m": ca_range["max"],
#     })


# def compute_stream_order(lat: float, lon: float) -> int:
#     """
#     Get direct stream order at the exact pixel for (lat, lon)
#     from Stream_Order_Raster_India.

#     Returns an integer stream order (0 if missing).
#     """
#     if not EE_AVAILABLE:
#         print("EE not available, returning dummy stream order 0.")
#         return 0

#     # Load stream order raster
#     so = (
#         ee.Image("projects/corestack-datasets/assets/datasets/Stream_Order_Raster_India")
#         .select(0)
#         .rename("so")
#         .unmask(0)  # fill missing pixels with 0
#     )

#     # Geometry for the site
#     point = ee.Geometry.Point([lon, lat])

#     # Use native scale of raster
#     scale = so.projection().nominalScale()

#     # Reduce region: get the first pixel value at the point
#     stats = so.reduceRegion(
#         reducer=ee.Reducer.first(),
#         geometry=point,
#         scale=scale,
#         bestEffort=True,
#     )

#     so_val = stats.get("so")
#     value = so_val.getInfo() if so_val is not None else None

#     if value is None:
#         return 0

#     # Stream order is integer
#     return int(round(float(value)))

# # ---------- Normalization helpers ----------

# def normalize_structure_name(structure_type: str) -> str:
#     if not structure_type:
#         return ""
#     st = structure_type.strip().lower()
#     st = st.replace(" ", "_").replace("-", "_")
#     # "Check dam" -> "check_dam"
#     return st

# def normalize_text(s: str | None) -> str:
#     if not s:
#         return ""
#     return s.strip().lower()


# def classify_slope(value: float | None, slope_rule: dict | None) -> dict:
#     if slope_rule is None or value is None:
#         return {
#             "value": value,
#             "rule": slope_rule,
#             "category": "not_evaluated",
#             "explanation": "Slope not evaluated (no value or rule)."
#         }

#     max_v = float(slope_rule["max"])
#     if value <= max_v:
#         category = "accepted"
#         expl = f"Slope {value:.2f}% is ≤ {max_v}% → accepted."
#     else:
#         category = "not_accepted"
#         expl = f"Slope {value:.2f}% is > {max_v}% → not accepted."

#     return {
#         "value": round(value, 2),
#         "rule": {"max": max_v},
#         "category": category,
#         "explanation": expl
#     }

# def classify_catchment(value: float | None, ca_rule: dict | None) -> dict:
#     if ca_rule is None or value is None:
#         return {
#             "value": value,
#             "rule": ca_rule,
#             "category": "not_evaluated",
#             "explanation": "Catchment area not evaluated (no value or rule)."
#         }

#     acc = ca_rule["accepted"]
#     part = ca_rule["partially_accepted"]
#     acc_min, acc_max = float(acc["min"]), float(acc["max"])
#     part_min, part_max = float(part["min"]), float(part["max"])
#     v = float(value)

#     if v < acc_min or v > part_max:
#         category = "not_accepted"
#         expl = (
#             f"Catchment area {v:.2f} ha is outside accepted range "
#             f"{acc_min}–{acc_max} ha and partially accepted range "
#             f"{part_min}–{part_max} ha → not accepted."
#         )
#     elif acc_min <= v <= acc_max:
#         category = "accepted"
#         expl = (
#             f"Catchment area {v:.2f} ha is within accepted range "
#             f"{acc_min}–{acc_max} ha."
#         )
#     else:  # acc_max < v <= part_max
#         category = "partially_accepted"
#         expl = (
#             f"Catchment area {v:.2f} ha lies between {part_min}–{part_max} ha "
#             f"→ partially accepted."
#         )

#     return {
#         "value": round(v, 2),
#         "rule": {
#             "accepted": acc,
#             "partially_accepted": part,
#             "not_accepted": ca_rule.get("not_accepted")
#         },
#         "category": category,
#         "explanation": expl
#     }

# def classify_stream_order(value: int | None, so_rule: dict | None) -> dict:
#     if so_rule is None or value is None:
#         return {
#             "value": value,
#             "rule": so_rule,
#             "category": "not_evaluated",
#             "explanation": "Stream order not evaluated (no value or rule)."
#         }

#     v = int(value)
#     valid = so_rule.get("valid", [])
#     be_careful = so_rule.get("be_careful", [])

#     if v in valid:
#         category = "valid"
#         expl = f"Stream order {v} is in valid set {valid}."
#     elif v in be_careful:
#         category = "be_careful"
#         expl = f"Stream order {v} is in be-careful range {be_careful}."
#     elif v > 6:
#         category = "not_accepted"
#         expl = f"Stream order {v} is > 6 → not accepted."
#     else:
#         category = "not_evaluated"
#         expl = f"Stream order {v} does not clearly match any rule bucket."

#     return {
#         "value": v,
#         "rule": so_rule,
#         "category": category,
#         "explanation": expl
#     }



# def classify_drainage(value: float | None, dd_rule: dict | None) -> dict:
#     if dd_rule is None or value is None:
#         return {
#             "value": value,
#             "rule": dd_rule,
#             "category": "not_evaluated",
#             "explanation": "Drainage distance not evaluated (no value or rule or script not yet wired)."
#         }

#     acc = dd_rule["accepted"]
#     part = dd_rule["partially_accepted"]
#     acc_max = float(acc["max"])
#     part_max = float(part["max"])
#     v = float(value)

#     if v < acc_max:
#         category = "accepted"
#         expl = f"Drainage distance {v:.1f} m is < {acc_max} m → accepted."
#     elif v <= part_max:
#         category = "partially_accepted"
#         expl = (
#             f"Drainage distance {v:.1f} m lies between "
#             f"{acc_max}–{part_max} m → partially accepted."
#         )
#     else:
#         category = "not_accepted"
#         expl = f"Drainage distance {v:.1f} m is > {part_max} m → not accepted."

#     return {
#         "value": round(v, 2),
#         "rule": dd_rule,
#         "category": category,
#         "explanation": expl
#     }


# def classify_lulc(value: str | None, lulc_rule: dict | None) -> dict:
#     if lulc_rule is None or not value:
#         return {
#             "value": value,
#             "rule": lulc_rule,
#             "category": "not_evaluated",
#             "explanation": "LULC not evaluated (no value or rule or script not yet wired)."
#         }

#     v_raw = value.strip()
#     v_norm = normalize_text(v_raw)

#     def norm_list(lst):
#         return [normalize_text(x) for x in (lst or [])]

#     acc = norm_list(lulc_rule.get("accepted"))
#     part = norm_list(lulc_rule.get("partially_accepted"))
#     not_acc = norm_list(lulc_rule.get("not_accepted"))

#     if v_norm in acc:
#         category = "accepted"
#         expl = f"LULC '{v_raw}' is in accepted list."
#     elif v_norm in part:
#         category = "partially_accepted"
#         expl = f"LULC '{v_raw}' is in partially accepted list."
#     elif v_norm in not_acc:
#         category = "not_accepted"
#         expl = f"LULC '{v_raw}' is in not-accepted list."
#     else:
#         category = "not_evaluated"
#         expl = f"LULC '{v_raw}' does not match any of the configured categories."

#     return {
#         "value": v_raw,
#         "rule": lulc_rule,
#         "category": category,
#         "explanation": expl
#     }



# def evaluate_site_from_rules(site: dict) -> dict:
#     """
#     Uses rules.json for the given structure_type and returns
#     per-parameter categories + explanations.
#     No final True/False suitability yet.
#     """
#     structure_key = normalize_structure_name(site.get("structure_type", ""))
#     rules = RULES.get(structure_key)

#     if not rules:
#         return {
#             "structure_type": site.get("structure_type"),
#             "error": f"No rules defined for structure: {structure_key}",
#             "parameters": {},
#             "overall_comment": "Cannot evaluate without structure-specific rules."
#         }

#     slope_res = classify_slope(site.get("slope"), rules.get("slope"))
#     ca_res = classify_catchment(site.get("catchment_area"), rules.get("catchment_area"))
#     so_res = classify_stream_order(site.get("stream_order"), rules.get("stream_order"))
#     dd_res = classify_drainage(site.get("drainage_distance"), rules.get("drainage_distance"))
#     lulc_res = classify_lulc(site.get("lulc_class"), rules.get("lulc"))

#     explanations = [
#         slope_res["explanation"],
#         ca_res["explanation"],
#         so_res["explanation"],
#         dd_res["explanation"],
#         lulc_res["explanation"],
#     ]

#     overall_comment = (
#         "Intermediate validation: slope, catchment area and stream order are "
#         "computed using GEE. LULC and drainage distance thresholds are "
#         "defined in rules.json; automatic extraction will be wired next."
#     )

#     return {
#         "structure_type": site.get("structure_type"),
#         "parameters": {
#             "slope": slope_res,
#             "catchment_area": ca_res,
#             "stream_order": so_res,
#             "drainage_distance": dd_res,
#             "lulc": lulc_res
#         },
#         "explanations": explanations,
#         "overall_comment": overall_comment
#     }


# @app.route("/api/compute-stream-order", methods=["POST"])
# def api_compute_stream_order():
#     """
#     Test endpoint: returns direct stream order at a point.

#     Input JSON:
#     {
#       "lat": 25.3290703,
#       "lon": 75.22412015
#     }
#     """
#     data = request.get_json() or {}

#     lat = data.get("lat")
#     lon = data.get("lon")

#     if lat is None or lon is None:
#         return jsonify({"error": "lat and lon are required"}), 400

#     try:
#         lat = float(lat)
#         lon = float(lon)
#     except ValueError:
#         return jsonify({"error": "lat and lon must be numeric"}), 400

#     try:
#         so_val = compute_stream_order(lat, lon)
#     except Exception as e:
#         return jsonify({"error": f"Failed to compute stream order: {e}"}), 500

#     return jsonify({
#         "lat": lat,
#         "lon": lon,
#         "stream_order": so_val,
#     })

# @app.route("/api/validate-site", methods=["POST"])
# def validate_site():
#     """
#     Validate a single site using GEE + rules.json.

#     Input JSON:
#     {
#       "lat": 25.32907,
#       "lon": 75.22412,
#       "structure_type": "Check dam",
#       "lulc_class": "Croplands",        # optional for now
#       "drainage_distance": 80           # optional for now
#     }
#     """
#     data = request.get_json() or {}

#     lat = data.get("lat")
#     lon = data.get("lon")
#     structure_type = (data.get("structure_type") or "").strip()
#     lulc_class = data.get("lulc_class")  # can be None
#     drainage_distance = data.get("drainage_distance")  # can be None

#     if lat is None or lon is None or not structure_type:
#         return jsonify({"error": "lat, lon and structure_type are required"}), 400

#     try:
#         lat = float(lat)
#         lon = float(lon)
#     except ValueError:
#         return jsonify({"error": "lat and lon must be numeric"}), 400

#     if not EE_AVAILABLE:
#         return jsonify({"error": "Earth Engine is not available on the backend."}), 500

#     try:
#         slope_val = compute_slope_mean_30m(lat, lon, buffer_m=30)
#         ca_range = compute_catchment_minmax_30m(lat, lon, buffer_m=30)
#         so_val = compute_stream_order(lat, lon)
#     except Exception as e:
#         return jsonify({"error": f"GEE computation failed: {e}"}), 500

#     ca_rep = ca_range["max"]  # use max in 30 m buffer as representative C

#     site = {
#         "structure_type": structure_type,
#         "slope": slope_val,
#         "catchment_area": ca_rep,
#         "stream_order": so_val,
#         "drainage_distance": float(drainage_distance) if drainage_distance is not None else None,
#         "lulc_class": lulc_class
#     }

#     eval_report = evaluate_site_from_rules(site)

#     return jsonify({
#         "lat": lat,
#         "lon": lon,
#         "structure_type": structure_type,
#         "raw_values": {
#             "slope_mean_30m": slope_val,
#             "catchment_min_30m": ca_range["min"],
#             "catchment_max_30m": ca_range["max"],
#             "stream_order": so_val,
#             "drainage_distance": drainage_distance,
#             "lulc_class": lulc_class
#         },
#         "evaluation": eval_report
#     })




# @app.route("/api/plan-sites", methods=["POST"])
# def plan_sites():
#     """
#     Extract site points for a given plan layer.

#     Input JSON:
#     {
#       "plan_number": "116",
#       "district": "bhilwara",
#       "block": "mandalgarh",
#       "layer_type": "plan_agri"     # or "plan_gw"
#     }
#     """
#     data = request.get_json() or {}

#     plan_number = str(data.get("plan_number", "")).strip()
#     district = str(data.get("district", "")).strip()
#     block = str(data.get("block", "")).strip()
#     layer_type = str(data.get("layer_type", "")).strip()

#     if not plan_number or not district or not block or not layer_type:
#         return jsonify({"error": "plan_number, district, block and layer_type are required"}), 400

#     if layer_type not in LAYER_CONFIG:
#         return jsonify({"error": f"layer_type must be one of {list(LAYER_CONFIG.keys())}"}), 400

#     try:
#         layer_name, sites = fetch_sites_from_layer(layer_type, plan_number, district, block)
#     except Exception as e:
#         return jsonify({"error": f"Could not fetch sites from layer: {str(e)}"}), 500

#     return jsonify({
#         "plan_number": plan_number,
#         "district": district.lower(),
#         "block": block.lower(),
#         "layer_type": layer_type,
#         "layer_name": layer_name,
#         "site_count": len(sites),
#         "sites": sites,
#     })


# @app.route("/api/error1/submit", methods=["POST"])
# def submit_error1():
#     """
#     Receives user decisions for Error 1 review.

#     Input JSON:
#     {
#       "plan_number": "116",
#       "district": "bhilwara",
#       "block": "mandalgarh",
#       "layer_type": "plan_gw",
#       "decisions": [
#         {
#           "id": "...",
#           "lat": 25.32,
#           "lon": 75.21,
#           "structure_type": "Check dam",
#           "status": "pass" | "flag",
#           "reason": "mis_marking" | "built_up" | "inside_water" | "no_structure" | "other",
#           "comments": "optional notes"
#         },
#         ...
#       ]
#     }
#     """
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

#     # Append flagged sites to CSV (simple 'database' for now)
#     save_path = FLAGGED_FILE
#     file_exists = os.path.isfile(save_path)

#     try:
#         with open(save_path, "a", newline="", encoding="utf-8") as f:
#             writer = csv.writer(f)
#             if not file_exists:
#                 writer.writerow([
#                     "plan_number",
#                     "district",
#                     "block",
#                     "layer_type",
#                     "site_id",
#                     "lat",
#                     "lon",
#                     "structure_type",
#                     "status",
#                     "reason",
#                     "comments",
#                 ])

#             for d in flagged:
#                 writer.writerow([
#                     plan_number,
#                     district,
#                     block,
#                     layer_type,
#                     d.get("id", ""),
#                     d.get("lat", ""),
#                     d.get("lon", ""),
#                     d.get("structure_type", ""),
#                     d.get("status", ""),
#                     d.get("reason", ""),
#                     d.get("comments", ""),
#                 ])
#     except Exception as e:
#         return jsonify({"error": f"Failed to save flagged sites: {e}"}), 500

#     return jsonify({
#         "plan_number": plan_number,
#         "district": district,
#         "block": block,
#         "layer_type": layer_type,
#         "flagged_count": len(flagged),
#         "passed_count": len(passed),
#         "passed_sites": passed,
#     })



# if __name__ == "__main__":

#     app.run(host="127.0.0.1", port=8000, debug=True)

# ------------------------------------------------------------------------






# Part 2

# Experimenting and learning from the begining (working code without lulc)
# app.py
# ============================================================
# Run:
#   .\venv\Scripts\Activate
#   python app.py
# ============================================================

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

# # Drainage lines asset (same as your JS)
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

# import re

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

#     # remove anything inside brackets/parentheses: "(cct)" "(egp)" etc.
#     s = re.sub(r"\(.*?\)", " ", s)

#     # IMPORTANT: handle % BEFORE underscore-joining
#     s = s.replace("%", " percent ")

#     # normalize separators
#     s = s.replace("&", " and ")
#     s = s.replace("/", " ")
#     s = s.replace("-", " ")

#     # remove non-alphanumeric (keep spaces for now)
#     s = re.sub(r"[^a-z0-9\s]", " ", s)

#     # optional plural standardization
#     s = s.replace("trenches", "trench")

#     # collapse whitespace -> underscores (FINAL canonical form)
#     s = "_".join(s.split()).strip("_")

#     # apply aliases
#     return STRUCTURE_ALIASES.get(s, s)


# def get_structure_type(props: dict) -> str:
#     """Try extracting structure type from known GeoServer fields."""
#     for field in STRUCTURE_FIELDS:
#         val = props.get(field)
#         if val:
#             return str(val).strip()
#     return ""


# def extract_lon_lat_from_geom(geom: dict):
#     """
#     Extract lon/lat from GeoJSON geometry.
#     Supports Point and Polygon-like nested coordinate arrays.
#     """
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
# # 6) GeoServer: fetch plan sites (keep SAME params as your old working code)
# # ============================================================

# def fetch_sites_from_layer(prefix: str, plan_number: str, district: str, block: str):
#     """
#     Calls GeoServer WFS for the given plan layer and extracts:
#     - id
#     - lat, lon
#     - structure_type
#     """
#     district = district.lower()
#     block = block.lower()

#     workspace = LAYER_CONFIG[prefix]
#     layer_name = build_layer_name(prefix, plan_number, district, block)
#     wfs_url = f"{GEOSERVER_BASE}{workspace}/ows"

#     # IMPORTANT: keep this EXACT like your old working code:
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

#         # fallback to lat/lon fields if geometry extraction fails
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
#     """Mean slope (%) within buffer_m around point using SRTM."""
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
#     """Min/Max catchment area (ha) in buffer_m around point."""
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
#     """Stream order at point (integer)."""
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
#     """
#     Vector -> distance image -> reduceRegion(min) at point.
#     Returns distance in meters.
#     """
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

#     d = stats.get("distance").getInfo()  # band name is "distance"
#     return round(float(d or 0.0), 2)


# # ============================================================
# # 8) RULES SCHEMA VALIDATION (keeps all patterns in check)
# # ============================================================

# ALLOWED_PARAMS = {"slope", "stream_order", "catchment_area", "drainage_distance", "lulc"}

# def _is_num(x):
#     return isinstance(x, (int, float)) and not isinstance(x, bool)

# def _is_range_dict(d):
#     """Range dict can be: {"min": n}, {"max": n}, {"min": n, "max": n}"""
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
#     """
#     Returns list of issues. Each issue is a string describing what's wrong.
#     Checks:
#       - each structure is dict
#       - each param uses allowed keys
#       - numeric params have accepted ranges (or legacy slope.max)
#       - stream_order uses accepted + optional partially_accepted (or legacy valid)
#       - lulc uses accepted/partially_accepted/not_accepted lists
#     """
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

#         # ---- slope ----
#         if "slope" in struct_rules:
#             sr = struct_rules["slope"]
#             if not isinstance(sr, dict):
#                 issues.append(f"[{struct_name}.slope] must be an object.")
#             else:
#                 # allowed: legacy {"max": n} OR bucketed accepted/partially_accepted
#                 if "max" in sr and "accepted" not in sr:
#                     if not _is_num(sr["max"]):
#                         issues.append(f"[{struct_name}.slope.max] must be a number.")
#                 else:
#                     if "accepted" not in sr or not _is_range_dict(sr.get("accepted")):
#                         issues.append(f"[{struct_name}.slope.accepted] must be a range dict like {{min,max}}.")
#                     if "partially_accepted" in sr and not _is_range_dict(sr.get("partially_accepted")):
#                         issues.append(f"[{struct_name}.slope.partially_accepted] must be a range dict if present.")

#         # ---- catchment_area ----
#         if "catchment_area" in struct_rules:
#             cr = struct_rules["catchment_area"]
#             if not isinstance(cr, dict):
#                 issues.append(f"[{struct_name}.catchment_area] must be an object.")
#             else:
#                 if "accepted" not in cr or not _is_range_dict(cr.get("accepted")):
#                     issues.append(f"[{struct_name}.catchment_area.accepted] must be a range dict.")
#                 if "partially_accepted" in cr and not _is_range_dict(cr.get("partially_accepted")):
#                     issues.append(f"[{struct_name}.catchment_area.partially_accepted] must be a range dict if present.")

#         # ---- drainage_distance ----
#         if "drainage_distance" in struct_rules:
#             dr = struct_rules["drainage_distance"]
#             if not isinstance(dr, dict):
#                 issues.append(f"[{struct_name}.drainage_distance] must be an object.")
#             else:
#                 if "accepted" not in dr or not _is_range_dict(dr.get("accepted")):
#                     issues.append(f"[{struct_name}.drainage_distance.accepted] must be a range dict.")
#                 if "partially_accepted" in dr and not _is_range_dict(dr.get("partially_accepted")):
#                     issues.append(f"[{struct_name}.drainage_distance.partially_accepted] must be a range dict if present.")

#         # ---- stream_order ----
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

#         # ---- lulc ----
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
#     # Uncomment to stop server when rules.json is wrong:
#     # raise ValueError("rules.json schema invalid. Fix issues above.")
# else:
#     print("✅ rules.json schema validated (all patterns OK).")


# # ============================================================
# # 9) CLASSIFIERS (works for all your patterns)
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
#     """
#     Handles:
#       - legacy: {"max": 15}
#       - standard: {"accepted": {...}, "partially_accepted": {...}}
#       - standard: {"accepted": {...}} only
#     """
#     if value is None or rule is None:
#         return ("not_evaluated", f"{label} not evaluated (missing value/rule).")

#     v = float(value)

#     # legacy slope: {"max": n}
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

#     # If accepted exists but didn't match, it is not accepted
#     if isinstance(acc, dict):
#         return ("not_accepted", f"{label} {v:.2f} outside accepted/partial ranges → not accepted.")

#     return ("not_evaluated", f"{label} rule format not recognized.")


# def classify_stream_order(value, rule: dict):
#     if value is None or rule is None:
#         return ("not_evaluated", "Stream order not evaluated (missing value/rule).")

#     v = int(value)

#     accepted = rule.get("accepted")
#     if accepted is None:
#         accepted = rule.get("valid", [])  # supports legacy 'valid'
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


# # ============================================================
# # 10) Main evaluation engine (single function)
# # ============================================================

# def evaluate_site_from_rules(site: dict) -> dict:
#     key = normalize_structure_name(site.get("structure_type", ""))
#     rules = RULES.get(key)

#     if not rules:
#         return {
#             "suitable": False,
#             "parameters": {},
#             "overall_comment": f"No rules found for structure '{key}'."
#         }

#     params = {}
#     statuses = []
#     failures = []

#     # slope
#     if "slope" in rules:
#         cat, expl = classify_numeric(site.get("slope"), rules["slope"], "Slope (%)")
#         params["slope"] = {"category": cat, "value": site.get("slope"), "explanation": expl, "rule": rules["slope"]}
#         statuses.append(cat)
#         if cat == "not_accepted":
#             failures.append(expl)

#     # catchment
#     if "catchment_area" in rules:
#         cat, expl = classify_numeric(site.get("catchment_area"), rules["catchment_area"], "Catchment (ha)")
#         params["catchment_area"] = {"category": cat, "value": site.get("catchment_area"), "explanation": expl, "rule": rules["catchment_area"]}
#         statuses.append(cat)
#         if cat == "not_accepted":
#             failures.append(expl)

#     # stream order
#     if "stream_order" in rules:
#         cat, expl = classify_stream_order(site.get("stream_order"), rules["stream_order"])
#         params["stream_order"] = {"category": cat, "value": site.get("stream_order"), "explanation": expl, "rule": rules["stream_order"]}
#         statuses.append(cat)
#         if cat == "not_accepted":
#             failures.append(expl)

#     # drainage distance (with global epsilon override)
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

#     # lulc
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

#     return {
#         "suitable": suitable,
#         "parameters": params,
#         "overall_comment": overall_comment
#     }


# # ============================================================
# # 11) API endpoints
# # ============================================================

# @app.route("/api/plan-sites", methods=["POST"])
# def api_plan_sites():
#     """
#     Input:
#     {
#       "plan_number": "116",
#       "district": "bhilwara",
#       "block": "mandalgarh",
#       "layer_type": "plan_agri"
#     }
#     """
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

#     return jsonify({
#         "layer_name": layer_name,
#         "site_count": len(sites),
#         "sites": sites
#     })


# @app.route("/api/validate-site", methods=["POST"])
# def api_validate_site():
#     """
#     Input:
#     {
#       "lat": 25.32907,
#       "lon": 75.22412,
#       "structure_type": "Farm bund",
#       "lulc_class": "Croplands"   # optional
#     }
#     """
#     data = request.get_json() or {}

#     lat = data.get("lat")
#     lon = data.get("lon")
#     structure_type = (data.get("structure_type") or "").strip()
#     lulc_class = data.get("lulc_class")

#     if lat is None or lon is None or not structure_type:
#         return jsonify({"error": "lat, lon, structure_type are required"}), 400

#     try:
#         lat = float(lat)
#         lon = float(lon)
#     except ValueError:
#         return jsonify({"error": "lat and lon must be numeric"}), 400

#     if not EE_AVAILABLE:
#         return jsonify({"error": "Earth Engine not available"}), 500

#     # Compute values from GEE
#     slope = compute_slope_mean_30m(lat, lon, buffer_m=30)
#     ca_range = compute_catchment_minmax_30m(lat, lon, buffer_m=30)
#     stream_order = compute_stream_order(lat, lon)
#     drainage_distance = compute_drainage_distance_m(lat, lon, scale=30)

#     # Representative catchment: max in 30m buffer
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
#         },
#         "evaluation": evaluation
#     })


# @app.route("/api/error1/submit", methods=["POST"])
# def api_submit_error1():
#     """
#     Receives user decisions for Error 1 review and appends flagged to CSV.
#     """
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
#     """Returns rules schema issues (if any) so you can debug from UI."""
#     issues = validate_rules_schema(RULES)
#     return jsonify({
#         "ok": (len(issues) == 0),
#         "issue_count": len(issues),
#         "issues": issues
#     })


# # ============================================================
# # 12) Start server
# # ============================================================

# if __name__ == "__main__":
#     app.run(host="127.0.0.1", port=8000, debug=True)










#///////////////////////////////////////////////////////////

# PART 3

# full code with integration of lulc

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
    print("✅ Earth Engine initialized (project gee-automation-479508).")
except Exception as e:
    EE_AVAILABLE = False
    print("⚠️ WARNING: Could not initialize Earth Engine:", e)

# ============================================================
# 4) Load rules.json
# ============================================================

with open("rules.json", "r", encoding="utf-8") as f:
    RULES = json.load(f)

print("✅ Loaded rules for structures:", list(RULES.keys()))

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
    print("❌ RULES SCHEMA ISSUES FOUND:")
    for i in schema_issues:
        print(" -", i)
else:
    print("✅ rules.json schema validated (all patterns OK).")

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
    rules = RULES.get(key)

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

    suitable = ("not_accepted" not in statuses)
    overall_comment = "Rule-based evaluation completed."
    if not suitable and failures:
        overall_comment += " Failures: " + " | ".join(failures[:3])

    return {"suitable": suitable, "parameters": params, "overall_comment": overall_comment}

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

    slope = compute_slope_mean_30m(lat, lon, buffer_m=30)
    ca_range = compute_catchment_minmax_30m(lat, lon, buffer_m=30)
    stream_order = compute_stream_order(lat, lon)
    drainage_distance = compute_drainage_distance_m(lat, lon, scale=30)

    catchment_rep = ca_range["max"]

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




