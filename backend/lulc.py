# services/lulc.py
import ee

# ---------- LULC DATA ----------
LULC_ASSET = (
    "projects/corestack-datasets/assets/datasets/"
    "LULC_v3_river_basin/pan_india_lulc_v3_2024_2025"
)

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


# ---------- A) ON-SPOT LULC ----------
def compute_lulc_point(lat: float, lon: float) -> str | None:
    lulc = _lulc_image()
    pt = ee.Geometry.Point([lon, lat])
    scale = lulc.projection().nominalScale()

    v = lulc.reduceRegion(
        reducer=ee.Reducer.first(),
        geometry=pt,
        scale=scale,
        maxPixels=1e9
    ).get("lulc")

    vv = v.getInfo() if v else None
    if vv is None:
        return None
    return LULC_NAMES.get(int(round(float(vv))))


# ---------- B) 30m BUFFER DOMINANT LULC ----------
def compute_lulc_buffer_dominant(lat: float, lon: float, buffer_m: int = 30) -> str | None:
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

    # empty / masked area
    if hist.size().getInfo() == 0:
        return None

    keys = hist.keys()
    counts = hist.values()
    max_count = counts.reduce(ee.Reducer.max())
    max_idx = counts.indexOf(max_count)

    dom_key = ee.String(keys.get(max_idx))     # e.g. "10" or "10.0"
    dom_id = ee.Number.parse(dom_key)          # safe parse

    dom_val = dom_id.getInfo()
    if dom_val is None:
        return None
    return LULC_NAMES.get(int(dom_val))


# ---------- C) DOWNSTREAM LULC (HydroSHEDS D8 stepping) ----------
# Note: HydroSHEDS flow direction is typically ~90m, so "downstream" is directional but coarse.
FDIR_ASSET = "WWF/HydroSHEDS/03DIR"  # band b1

# D8 offsets (ESRI)
D8 = {
    1:  ( 1,  0),  # E
    2:  ( 1, -1),  # SE
    4:  ( 0, -1),  # S
    8:  (-1, -1),  # SW
    16: (-1,  0),  # W
    32: (-1,  1),  # NW
    64: ( 0,  1),  # N
    128:( 1,  1)   # NE
}

def _move_point_meters(point4326: ee.Geometry, dx_m: ee.Number, dy_m: ee.Number) -> ee.Geometry:
    # work in meters projection
    p3857 = point4326.transform("EPSG:3857", 1)
    xy = ee.List(p3857.coordinates())
    x = ee.Number(xy.get(0)).add(dx_m)
    y = ee.Number(xy.get(1)).add(dy_m)
    return ee.Geometry.Point([x, y], "EPSG:3857").transform("EPSG:4326", 1)

def compute_downstream_point(lat: float, lon: float, n_steps: int = 3) -> tuple[float, float] | None:
    fdir = ee.Image(FDIR_ASSET).select("b1").rename("fdir")
    cell = ee.Number(fdir.projection().nominalScale())
    cur = ee.Geometry.Point([lon, lat])

    def step_fn(_, state):
        state = ee.Dictionary(state)
        cur_pt = ee.Geometry(state.get("pt"))

        dir_val = fdir.reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=cur_pt,
            scale=cell,
            maxPixels=1e9
        ).get("fdir")

        # if null → don't move
        is_null = ee.Algorithms.IsEqual(dir_val, None)

        # convert to integer code
        code = ee.Number(ee.Algorithms.If(is_null, -999, dir_val))

        # lookup dx,dy (cell units)
        # if invalid code, keep dx=dy=0
        dx_cell = ee.Number(
            ee.Algorithms.If(
                is_null,
                0,
                ee.Dictionary(D8).get(code, 0)
            )
        )

        # because D8 dict stores tuple, above get won't directly split;
        # safer: map code -> list [dx,dy]
        offsets = ee.Dictionary({
            1:  ee.List([ 1,  0]),
            2:  ee.List([ 1, -1]),
            4:  ee.List([ 0, -1]),
            8:  ee.List([-1, -1]),
            16: ee.List([-1,  0]),
            32: ee.List([-1,  1]),
            64: ee.List([ 0,  1]),
            128:ee.List([ 1,  1]),
        })

        off = ee.List(ee.Algorithms.If(is_null, ee.List([0, 0]), offsets.get(code, ee.List([0, 0]))))
        dx = ee.Number(off.get(0)).multiply(cell)
        dy = ee.Number(off.get(1)).multiply(cell)

        will_move = ee.Number(off.get(0)).neq(0).Or(ee.Number(off.get(1)).neq(0))

        next_pt = ee.Geometry(
            ee.Algorithms.If(will_move, _move_point_meters(cur_pt, dx, dy), cur_pt)
        )

        return ee.Dictionary({
            "pt": next_pt,
            "dirs": ee.List(state.get("dirs")).add(code),
            "moved": ee.List(state.get("moved")).add(will_move)
        })

    init = ee.Dictionary({"pt": cur, "dirs": ee.List([]), "moved": ee.List([])})
    out = ee.List.sequence(1, n_steps).iterate(step_fn, init)
    out = ee.Dictionary(out)

    down = ee.Geometry(out.get("pt"))
    coords = down.coordinates().getInfo()  # [lon, lat]
    if not coords or len(coords) < 2:
        return None
    return float(coords[1]), float(coords[0])


def compute_lulc_downstream(lat: float, lon: float, n_steps: int = 3) -> str | None:
    ds = compute_downstream_point(lat, lon, n_steps=n_steps)
    if ds is None:
        return None
    dlat, dlon = ds
    return compute_lulc_point(dlat, dlon)


