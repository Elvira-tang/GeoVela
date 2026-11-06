# ─── OpenGIS Agent · run c378b462 · step 3 · export_forecast_day_geojson ───
# Timestamp : 2026-11-05T23:47:34
# Semantic : export_forecast_day_geojson
# Metadata : 20261105-234734-step03-export_forecast_day_geojson.metadata.json
# User query: 请读取 china_weather_last7days.csv，对每个代表性城市分别预测未来3天的天气。  首先检查并识别以下字段： 城市名称、经度、纬度、日期、最高温度、最低温度、平均温度、 相对湿度、降水量或降水概率、气压、风速和天气类型。  预测要求：  1. 按城市分组，并按照日期升序排列。 2. 对最高温度、最低温度、平均温度、相对湿度、气压和风速，    使用 Holt 线性趋势指数平…
import json
import pandas as pd

out = pd.read_csv("output/china_weather_next3days.csv", encoding="utf-8-sig")
files = []
for day in [1, 2, 3]:
    d = out[out["forecast_day"] == day]
    feats = []
    for _, r in d.iterrows():
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(r["longitude"]), float(r["latitude"])]},
            "properties": {
                "城市": r["city"],
                "预报日期": r["forecast_date"],
                "预报日序": int(r["forecast_day"]),
                "预测平均气温": float(r["temp_mean"]),
                "预测最高气温": float(r["temp_max"]),
                "预测最低气温": float(r["temp_min"]),
                "相对湿度(%)": float(r["humidity"]),
                "降水概率(%)": float(r["precipitation_probability"]),
                "气压(hPa)": float(r["pressure"]),
                "风速(km/h)": float(r["wind_speed"]),
                "天气类型": r["weather_type"],
                "预测方法": r["forecast_method"],
                "置信度": r["confidence_level"],
                "是否估算": "是",
                "标签": f"{r['city']} {r['temp_mean']:.0f}°C",
            },
        })
    fc = {"type": "FeatureCollection", "features": feats}
    p = f"output/china_weather_forecast_day{day}.geojson"
    with open(p, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False)
    files.append((day, p, len(feats)))

print(files)
print(out["forecast_date"].unique())
print("breaks range", out["temp_mean"].min(), out["temp_mean"].max())

# ─── Observations ───
# [(1, 'output/china_weather_forecast_day1.geojson', 12), (2, 'output/china_weather_forecast_day2.geojson', 12), (3, 'output/china_weather_forecast_day3.geojson', 12)]
# <StringArray>
# ['2026-11-06', '2026-11-07', '2026-11-08']
# Length: 3, dtype: str
# breaks range -23.3 26.2
