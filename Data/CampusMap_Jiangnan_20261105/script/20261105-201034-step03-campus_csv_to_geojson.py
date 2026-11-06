# ─── OpenGIS Agent · run 3c5b52a5 · step 3 · campus_csv_to_geojson ───
# Timestamp : 2026-11-05T20:10:34
# Semantic : campus_csv_to_geojson
# Metadata : 20261105-201034-step03-campus_csv_to_geojson.metadata.json
# User query: 加载 📎jiangnan_university_campus.csv到地图上
import pandas as pd, json, os
from shapely import wkt
from shapely.geometry import Point, mapping, shape
from shapely.validation import make_valid

src = "data/jiangnan_university_campus.csv"
df = pd.read_csv(src, encoding="utf-8-sig")
out_dir = "output"
os.makedirs(out_dir, exist_ok=True)

geoms, kinds = [], []
for i, row in df.iterrows():
    w = row.get("几何(WKT)")
    if isinstance(w, str) and w.strip():
        try:
            g = wkt.loads(w.strip())
            if not g.is_valid:
                g = make_valid(g)
            geoms.append(g); kinds.append(g.geom_type)
            continue
        except Exception:
            pass
    lon, lat = row.get("经度"), row.get("纬度")
    if pd.notna(lon) and pd.notna(lat):
        geoms.append(Point(float(lon), float(lat))); kinds.append("Point")
    else:
        geoms.append(None); kinds.append(None)

df["_geom"] = geoms
df["_kind"] = kinds
df = df[df["_geom"].notna()].copy()
df["_kind"] = df["_geom"].apply(lambda g: g.geom_type)

def clean(v):
    if pd.isna(v):
        return None
    if isinstance(v, float):
        return None if pd.isna(v) else v
    return v

groups = {
    "polygons": df[df["_kind"].isin(["Polygon", "MultiPolygon"])],
    "lines": df[df["_kind"].isin(["LineString", "MultiLineString"])],
    "points": df[df["_kind"].isin(["Point", "MultiPoint"])],
}
paths = {}
for name, sub in groups.items():
    feats = []
    for _, r in sub.iterrows():
        props = {c: clean(r[c]) for c in ["类别", "名称", "英文名称", "类型细分", "经度", "纬度", "长度(m)", "面积(m2)", "备注", "OSM_ID", "数据来源", "采集日期"]}
        feats.append({"type": "Feature", "properties": props, "geometry": mapping(r["_geom"])})
    fc = {"type": "FeatureCollection", "features": feats}
    p = os.path.join(out_dir, f"jiangnan_campus_{name}.geojson")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False)
    paths[name] = (p, len(feats))
    print(name, len(feats), p)
print(df["类别"].value_counts().to_string())

# ─── Observations ───
# polygons 70 output\jiangnan_campus_polygons.geojson
# lines 61 output\jiangnan_campus_lines.geojson
# points 103 output\jiangnan_campus_points.geojson
# 类别
# 建筑      95
# 道路      61
# 体育休闲    34
# 设施      26
# 出入口      9
# 节点       4
# 景点       3
# 用地       2
