# ─── OpenGIS Agent · run 7653f30d · step 1 · w7_theme_subsets ───
# Timestamp : 2026-11-05T22:58:13
# Semantic : w7_theme_subsets
# Metadata : 20261105-225813-step01-w7_theme_subsets.metadata.json
# User query: 请重新设计当前全国7日天气地图，目标是简洁、清晰、有专业气象地图的视觉效果。  第一步：清理图层 删除当前所有重复的 china_weather_7day_summary 和 china_weather_7day_strongwind 图层，也删除已有的 w7_temp、 w7_precip 和 w7_strongwind，避免同一城市出现同心圆。 不要重复加载同一个GeoJSON。  第二步：重…
import geopandas as gpd, json, os
src = r"output/china_weather_7day_summary.geojson"
gdf = gpd.read_file(src)
print(len(gdf), list(gdf.columns))
precip = gdf[gdf["累计降水量(mm)"] > 0].copy()
wind = gdf[gdf["最大风速(km/h)"] >= 20].copy()
os.makedirs("output", exist_ok=True)
precip.to_file("output/china_weather_7day_precip_gt0.geojson", driver="GeoJSON")
wind.to_file("output/china_weather_7day_wind_ge20.geojson", driver="GeoJSON")
print("precip>0:", len(precip), "wind>=20:", len(wind))
print("precip range", precip["累计降水量(mm)"].min(), precip["累计降水量(mm)"].max())
print("temp range", gdf["平均气温(℃)"].min(), gdf["平均气温(℃)"].max())
print(gdf[["城市","标签","平均气温(℃)"]].head(5).to_string())

# ─── Observations ───
# 49 ['城市', '省/区/市', '纬度', '经度', '平均气温(℃)', '最高气温(℃)', '最低气温(℃)', '累计降水量(mm)', '累计降雪量(mm)', '最大风速(km/h)', '平均日照时长(h)', '主要天气现象', '统计天数', '标签', 'geometry']
# precip>0: 44 wind>=20: 27
# precip range 0.1 60.2
# temp range -17.3 26.8
#     城市         标签  平均气温(℃)
# 0   北京   北京 10.1℃     10.1
# 1   天津   天津 12.4℃     12.4
# 2  石家庄  石家庄 13.6℃     13.6
# 3   唐山   唐山 11.4℃     11.4
# 4   太原    太原 8.7℃      8.7
