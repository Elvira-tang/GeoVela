# ─── OpenGIS Agent · run df034f2a · step 2 · poi_price_class_layers ───
# Timestamp : 2026-11-05T20:18:38
# Semantic : poi_price_class_layers
# Metadata : 20261105-201838-step02-poi_price_class_layers.metadata.json
# User query: 将价格高的放在上方
import json, os
import pandas as pd

base = r"D:\Study\大三\申威高级语言编译与程序设计\GIS\GeoVela\Data\MilkTea_Wuxi_20261105"
src = os.path.join(base, "data", "wuxi_milktea_poi.geojson")
outdir = os.path.join(base, "data", "poi_price_classes")
os.makedirs(outdir, exist_ok=True)

with open(src, "r", encoding="utf-8") as f:
    gj = json.load(f)

FIELD = "人均消费(元)"
breaks = [5, 8, 12, 15, 18, 22, 30, 60, 430]
colors = ["#fee391", "#fec44f", "#fe9929", "#ec7014", "#cc4c02", "#ad3700", "#8c2d04", "#662506"]
opacities = [0.40, 0.48, 0.56, 0.65, 0.74, 0.83, 0.90, 0.97]

feats = gj["features"]
def price(f):
    v = f.get("properties", {}).get(FIELD)
    return None if v is None or (isinstance(v, float) and pd.isna(v)) else float(v)

buckets = {i: [] for i in range(len(colors))}
unknown = []
for f in feats:
    p = price(f)
    if p is None:
        unknown.append(f)
        continue
    idx = len(colors) - 1
    for i in range(len(colors) - 1):
        if breaks[i] <= p < breaks[i + 1]:
            idx = i
            break
    if p < breaks[0]:
        idx = 0
    buckets[idx].append(f)

meta = []
if unknown:
    path = os.path.join(outdir, "class_00_unknown.geojson")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"type": "FeatureCollection", "features": unknown}, fh, ensure_ascii=False)
    meta.append({"file": path, "label": "价格未知", "color": "#b0b0b0", "opacity": 0.35, "count": len(unknown)})

for i in range(len(colors)):
    sub = sorted(buckets[i], key=lambda f: price(f))
    if not sub:
        continue
    label = f"{breaks[i]}-{breaks[i+1]} 元" if i < len(colors) - 1 else f"{breaks[i]}-{breaks[i+1]} 元"
    path = os.path.join(outdir, f"class_{i+1:02d}.geojson")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"type": "FeatureCollection", "features": sub}, fh, ensure_ascii=False)
    meta.append({"file": path, "label": label, "color": colors[i], "opacity": opacities[i], "count": len(sub)})

meta_path = os.path.join(outdir, "class_meta.json")
with open(meta_path, "w", encoding="utf-8") as fh:
    json.dump(meta, fh, ensure_ascii=False, indent=2)

print(len(meta), sum(m["count"] for m in meta))
for m in meta:
    print(m["label"], m["count"], m["color"], m["opacity"])

# ─── Observations ───
# 9 1654
# 价格未知 83 #b0b0b0 0.35
# 5-8 元 238 #fee391 0.4
# 8-12 元 94 #fec44f 0.48
# 12-15 元 397 #fe9929 0.56
# 15-18 元 412 #ec7014 0.65
# 18-22 元 300 #cc4c02 0.74
# 22-30 元 95 #ad3700 0.83
# 30-60 元 25 #8c2d04 0.9
# 60-430 元 10 #662506 0.97
