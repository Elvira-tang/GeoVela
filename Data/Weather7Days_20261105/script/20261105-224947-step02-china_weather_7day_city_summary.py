# ─── OpenGIS Agent · run c4b06689 · step 2 · china_weather_7day_city_summary ───
# Timestamp : 2026-11-05T22:49:47
# Semantic : china_weather_7day_city_summary
# Metadata : 20261105-224947-step02-china_weather_7day_city_summary.metadata.json
# User query: 读取 📎china_weather_last7days.csv ， 按城市进行7天统计，每个城市输出一条记录：  - 平均气温(℃)取7日平均值 - 降水量(mm)取7日总和，命名为“累计降水量(mm)” - 降雪量(mm)取7日总和，命名为“累计降雪量(mm)” - 最大风速(km/h)取7日最大值 - 日照时长(h)取7日平均值 - 天气现象取出现次数最多的类型  使用城市原有的经纬度生成点图…
import pandas as pd, geopandas as gpd, os, json

base = r"D:\Study\大三\申威高级语言编译与程序设计\GIS\GeoVela\Data\Weather7Days_20261105"
src = os.path.join(base, "data", "china_weather_last7days.csv")
out_dir = os.path.join(base, "output")
os.makedirs(out_dir, exist_ok=True)

df = pd.read_csv(src, encoding="utf-8-sig")


def mode_type(s):
    vc = s.value_counts()
    top = vc.max()
    cands = [k for k in vc.index if vc[k] == top]
    # tie -> the one appearing earliest in the period
    first_seen = {k: s[s == k].index[0] for k in cands}
    return min(cands, key=lambda k: first_seen[k])


rows = []
for city, g in df.groupby("城市", sort=False):
    g = g.sort_values("日期")
    rows.append({
        "城市": city,
        "省/区/市": g["省/区/市"].iloc[0],
        "纬度": g["纬度"].iloc[0],
        "经度": g["经度"].iloc[0],
        "平均气温(℃)": round(g["平均气温(℃)"].mean(), 1),
        "最高气温(℃)": round(g["最高气温(℃)"].max(), 1),
        "最低气温(℃)": round(g["最低气温(℃)"].min(), 1),
        "累计降水量(mm)": round(g["降水量(mm)"].sum(), 1),
        "累计降雪量(mm)": round(g["降雪量(mm)"].sum(), 1),
        "最大风速(km/h)": round(g["最大风速(km/h)"].max(), 1),
        "平均日照时长(h)": round(g["日照时长(h)"].mean(), 1),
        "主要天气现象": mode_type(g["天气现象"]),
        "统计天数": len(g),
    })

s = pd.DataFrame(rows)
s["标签"] = s["城市"] + " " + s["平均气温(℃)"].round(1).astype(str) + "℃"

gdf = gpd.GeoDataFrame(
    s, geometry=gpd.points_from_xy(s["经度"], s["纬度"]), crs="EPSG:4326"
)

out_all = os.path.join(out_dir, "china_weather_7day_summary.geojson")
gdf.to_file(out_all, driver="GeoJSON", encoding="utf-8")

strong = gdf[gdf["最大风速(km/h)"] >= 20].copy()
out_strong = os.path.join(out_dir, "china_weather_7day_strongwind.geojson")
strong.to_file(out_strong, driver="GeoJSON", encoding="utf-8")

print(len(gdf), len(strong))
print(s[["城市", "省/区/市", "平均气温(℃)", "累计降水量(mm)", "累计降雪量(mm)", "最大风速(km/h)", "平均日照时长(h)", "主要天气现象"]].head(6).to_string(index=False))
print("precip max:", s["累计降水量(mm)"].max(), "temp range:", s["平均气温(℃)"].min(), s["平均气温(℃)"].max())
print("strong:", list(strong["城市"]))
print(out_all, out_strong)

# ─── Observations ───
# 49 27
#   城市  省/区/市  平均气温(℃)  累计降水量(mm)  累计降雪量(mm)  最大风速(km/h)  平均日照时长(h) 主要天气现象
#   北京    北京市     10.1        0.0        0.0        19.2        8.7      阴
#   天津    天津市     12.4        1.1        0.0        18.8        9.0      晴
#  石家庄    河北省     13.6        1.4        0.0        19.0        7.8      晴
#   唐山    河北省     11.4        0.9        0.0        22.3        8.9      阴
#   太原    山西省      8.7        0.7        0.0        25.2        8.7      晴
# 呼和浩特 内蒙古自治区      3.6        0.0        0.0        22.1        8.8      阴
# precip max: 60.2 temp range: -17.3 26.8
# strong: ['唐山', '太原', '呼和浩特', '海拉尔', '沈阳', '大连', '长春', '哈尔滨', '南京', '无锡', '杭州', '厦门', '南昌', '青岛', '郑州', '武汉', '长沙', '南宁', '桂林', '海口', '三亚', '贵阳', '丽江', '敦煌', '西宁', '澳门', '台北']
# D:\Study\大三\申威高级语言编译与程序设计\GIS\GeoVela\Data\Weather7Days_20261105\output\china_weather_7day_summary.geojson D:\Study\大三\申威高级语言编译与程序设计\GIS\GeoVela\Data\Weather7Days_20261105\output\china_weather_7day_strongwind.geojson
