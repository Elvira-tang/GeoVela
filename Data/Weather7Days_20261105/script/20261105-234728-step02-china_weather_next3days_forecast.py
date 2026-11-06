# ─── OpenGIS Agent · run c378b462 · step 2 · china_weather_next3days_forecast ───
# Timestamp : 2026-11-05T23:47:28
# Semantic : china_weather_next3days_forecast
# Metadata : 20261105-234728-step02-china_weather_next3days_forecast.metadata.json
# User query: 请读取 china_weather_last7days.csv，对每个代表性城市分别预测未来3天的天气。  首先检查并识别以下字段： 城市名称、经度、纬度、日期、最高温度、最低温度、平均温度、 相对湿度、降水量或降水概率、气压、风速和天气类型。  预测要求：  1. 按城市分组，并按照日期升序排列。 2. 对最高温度、最低温度、平均温度、相对湿度、气压和风速，    使用 Holt 线性趋势指数平…
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

df = pd.read_csv("data/china_weather_last7days.csv", encoding="utf-8-sig")
df["日期"] = pd.to_datetime(df["日期"])
df = df.sort_values(["城市", "日期"]).reset_index(drop=True)

CITIES = ["漠河", "哈尔滨", "北京", "乌鲁木齐", "西安", "拉萨",
          "上海", "武汉", "成都", "昆明", "广州", "三亚"]

WX_BONUS = {"晴": 0.0, "多云": 5.0, "阴": 12.0, "小雨": 18.0, "中雨": 22.0,
            "大雨": 25.0, "暴雨": 27.0, "雷阵雨": 24.0, "小雪": 15.0,
            "中雪": 18.0, "大雪": 20.0, "雨夹雪": 20.0, "雾": 20.0, "霾": 12.0}


def wx_bonus(s):
    s = str(s)
    for k, v in WX_BONUS.items():
        if k in s:
            return v
    if "雪" in s:
        return 16.0
    if "雨" in s:
        return 20.0
    if "云" in s:
        return 6.0
    if "阴" in s:
        return 12.0
    return 8.0


def build_proxies(d):
    """相对湿度/气压为估算代理序列（源数据缺该两字段），公式写入脚本以便复核。"""
    prec = d["降水量(mm)"].to_numpy(float)
    dur = d["降水时长(h)"].to_numpy(float)
    sun = d["日照时长(h)"].to_numpy(float)
    t = d["平均气温(℃)"].to_numpy(float)
    wind = d["最大风速(km/h)"].to_numpy(float)
    bonus = np.array([wx_bonus(v) for v in d["天气现象"].to_numpy()])
    hum = 40.0 + 2.2 * np.minimum(prec, 12.0) + 0.55 * dur - 1.9 * sun + bonus
    hum = np.clip(hum, 15.0, 98.0)
    t_anom = t - t.mean()
    pres = 1013.6 - 0.60 * np.minimum(prec, 25.0) + 0.28 * t_anom - 0.05 * np.maximum(wind - 15.0, 0.0)
    pres = np.clip(pres, 995.0, 1035.0)
    return hum, pres


def holt_forecast(y, steps=3):
    n = len(y)
    if n < 5:
        w = np.array([0.5, 0.3, 0.2])[:min(3, n)]
        w = w / w.sum()
        base = float(np.dot(y[::-1][:len(w)], w))
        slope = float((y[-1] - y[0]) / max(n - 1, 1)) * 0.35
        out = [base + slope * (i + 1) for i in range(steps)]
        return np.array(out), "加权移动平均(0.5/0.3/0.2)", np.nan
    try:
        from statsmodels.tsa.holtwinters import Holt
        fit = Holt(y, damped_trend=True, initialization_method="estimated").fit(optimized=True)
        fc = np.asarray(fit.forecast(steps), dtype=float)
        resid_std = float(np.std(fit.resid, ddof=1)) if len(fit.resid) > 2 else np.nan
        if not np.all(np.isfinite(fc)):
            raise ValueError("non-finite forecast")
        return fc, "Holt线性趋势指数平滑(阻尼)", resid_std
    except Exception:
        w = np.array([0.5, 0.3, 0.2])
        base = float(np.dot(y[::-1], w))
        slope = float(np.polyfit(np.arange(n), y, 1)[0]) * 0.4
        return np.array([base + slope * (i + 1) for i in range(steps)]), "加权移动平均(0.5/0.3/0.2)", np.nan


MAX_STEP_TEMP = 3.0      # 平均气温相邻日允许变化阈值
MAX_STEP_EXTREME = 4.0   # 最高/最低气温相邻日允许变化阈值
MAX_DAY1_JUMP = 5.0      # 第1天相对最后一个观测值的允许跳变

rows = []
diag = []

for city in CITIES:
    d = df[df["城市"] == city].dropna(
        subset=["最高气温(℃)", "最低气温(℃)", "平均气温(℃)"]).sort_values("日期")
    n = len(d)
    lon, lat = float(d["经度"].iloc[0]), float(d["纬度"].iloc[0])
    tmax = d["最高气温(℃)"].to_numpy(float)
    tmin = d["最低气温(℃)"].to_numpy(float)
    tmean = d["平均气温(℃)"].to_numpy(float)
    wind = d["最大风速(km/h)"].to_numpy(float)
    prec = d["降水量(mm)"].to_numpy(float)
    hum, pres = build_proxies(d)

    f_tmax, m1, r1 = holt_forecast(tmax)
    f_tmin, m2, r2 = holt_forecast(tmin)
    f_tmean, m3, r3 = holt_forecast(tmean)
    f_hum, m4, r4 = holt_forecast(hum)
    f_pres, m5, r5 = holt_forecast(pres)
    f_wind, m6, r6 = holt_forecast(wind)

    used_wma = any("加权" in m for m in [m1, m2, m3, m4, m5, m6])
    method = "最近3天加权移动平均(0.5/0.3/0.2)" if (n < 5) else "Holt线性趋势指数平滑(阻尼)"
    resid_std = np.nanmean([r for r in [r1, r2, r3] if np.isfinite(r)]) if np.any(
        [np.isfinite(r) for r in [r1, r2, r3]]) else np.nan

    # ---- 约束处理 ----
    prev_mean, prev_max, prev_min = tmean[-1], tmax[-1], tmin[-1]
    f_tmax = np.maximum(f_tmax, prev_max - MAX_DAY1_JUMP)
    for i in range(3):
        cap = MAX_DAY1_JUMP if i == 0 else MAX_STEP_TEMP
        f_tmean[i] = np.clip(f_tmean[i], prev_mean - cap * 1.2, prev_mean + cap * 1.2)
        prev_mean = f_tmean[i]
    f_tmean = np.clip(f_tmean, tmean[-1] - 6.0, tmean[-1] + 6.0)

    pmax, pmin = tmax[-1], tmin[-1]
    for i in range(3):
        f_tmax[i] = np.clip(f_tmax[i], pmax - MAX_STEP_EXTREME, pmax + MAX_STEP_EXTREME)
        f_tmin[i] = np.clip(f_tmin[i], pmin - MAX_STEP_EXTREME, pmin + MAX_STEP_EXTREME)
        pmax, pmin = f_tmax[i], f_tmin[i]
    f_tmin = np.minimum(f_tmin, f_tmax - 0.5)          # 最低不高于最高
    f_tmean = np.clip(f_tmean, f_tmin, f_tmax)          # 平均介于两者之间
    f_hum = np.clip(f_hum, 0.0, 100.0)
    f_wind = np.maximum(f_wind, 0.0)
    f_pres = np.clip(f_pres, 985.0, 1040.0)

    # ---- 降水概率 ----
    wet_ratio = float(np.mean(prec > 0.1))
    mean_prec = float(np.mean(prec))
    pres_slope = float(np.polyfit(np.arange(len(pres)), pres, 1)[0])
    hum_slope = float(np.polyfit(np.arange(len(hum)), hum, 1)[0])
    for i in range(3):
        h = f_hum[i] / 100.0
        hum_score = np.clip((h - 0.45) / 0.45, 0, 1)
        amt_score = np.clip(mean_prec / 8.0, 0, 1)
        prob = 100.0 * (0.42 * wet_ratio + 0.38 * hum_score + 0.20 * amt_score)
        prob += -2.6 * (f_pres[i] - pres[-1])      # 气压下降 -> 概率上升
        prob += 1.2 * max(0.0, hum_slope) * (i + 1)
        prob -= 4.0 * i                            # 预报时效衰减
        rows_prob = float(np.clip(prob, 0.0, 96.0))
        rows.append(dict(city=city, longitude=round(lon, 4), latitude=round(lat, 4),
                         forecast_day=i + 1, forecast_date=None,
                         temp_max=round(float(f_tmax[i]), 1),
                         temp_min=round(float(f_tmin[i]), 1),
                         temp_mean=round(float(f_tmean[i]), 1),
                         humidity=round(float(f_hum[i]), 1),
                         precipitation_probability=round(rows_prob, 1),
                         pressure=round(float(f_pres[i]), 1),
                         wind_speed=round(float(f_wind[i]), 1),
                         forecast_method=method, resid_std=resid_std,
                         n_obs=n, wet_ratio=wet_ratio, pres_slope=pres_slope))
    diag.append((city, n, method, resid_std))

out = pd.DataFrame(rows)
last_date = df["日期"].max()
out["forecast_date"] = (last_date + pd.to_timedelta(out["forecast_day"], unit="D")).dt.strftime("%Y-%m-%d")


def weather_type(tm, tx, prob, hum):
    if prob >= 50 and tx <= 2.0:
        return "雪"
    if prob >= 85:
        return "中雨" if hum >= 88 else "小雨"
    if prob >= 62:
        return "小雨"
    if prob >= 42:
        return "阴"
    if prob >= 22:
        return "多云"
    return "晴"


out["weather_type"] = [weather_type(a, b, c, d) for a, b, c, d in
                       zip(out["temp_mean"], out["temp_max"],
                           out["precipitation_probability"], out["humidity"])]


def confidence(n, resid, day, prob):
    if n >= 7 and (not np.isfinite(resid) or resid <= 1.8):
        lvl = 3
    elif n >= 5 and (not np.isfinite(resid) or resid <= 3.2):
        lvl = 2
    else:
        lvl = 1
    if day == 2 and lvl == 3:
        lvl = 3
    if day == 3 and lvl >= 2:
        lvl = 2
    if n < 5:
        lvl = min(lvl, 1)
    return {3: "较高", 2: "中等", 1: "较低"}[lvl]


out["confidence_level"] = [confidence(n, r, d, p) for n, r, d, p in
                           zip(out["n_obs"], out["resid_std"], out["forecast_day"],
                               out["precipitation_probability"])]
out["is_estimated"] = True

cols = ["city", "longitude", "latitude", "forecast_date", "forecast_day",
        "temp_max", "temp_min", "temp_mean", "humidity",
        "precipitation_probability", "pressure", "wind_speed", "weather_type",
        "forecast_method", "confidence_level", "is_estimated",
        "n_obs", "resid_std", "wet_ratio", "pres_slope"]
out = out[cols]
out.to_csv("output/china_weather_next3days.csv", index=False, encoding="utf-8-sig")
print(out.shape)
print(out.head(6).to_string())
print("---")
print(out.groupby("forecast_date")["temp_mean"].agg(["min", "max", "mean"]).round(1).to_string())
print("---")
print(out[out.city.isin(["上海", "漠河", "广州"])][["city","forecast_date","temp_mean","humidity","precipitation_probability","pressure","wind_speed","weather_type","confidence_level"]].to_string(index=False))

# ─── Observations ───
# [auto-install] Auto-installed: statsmodels
# (36, 20)
#   city  longitude  latitude forecast_date  forecast_day  temp_max  temp_min  temp_mean  humidity  precipitation_probability  pressure  wind_speed weather_type   forecast_method confidence_level  is_estimated  n_obs  resid_std  wet_ratio  pres_slope
# 0   漠河   122.5424   52.9701    2026-11-06             1     -15.0     -28.1      -21.8      30.1                       13.4    1012.3         3.6            晴  Holt线性趋势指数平滑(阻尼)               较高          True      7   1.271641   0.285714   -0.283500
# 1   漠河   122.5424   52.9701    2026-11-07             2     -16.0     -29.4      -22.6      29.5                       10.1    1012.1         3.0            晴  Holt线性趋势指数平滑(阻尼)               较高          True      7   1.271641   0.285714   -0.283500
# 2   漠河   122.5424   52.9701    2026-11-08             3     -16.9     -30.7      -23.3      29.0                        6.8    1011.8         2.5            晴  Holt线性趋势指数平滑(阻尼)               中等          True      7   1.271641   0.285714   -0.283500
# 3  哈尔滨   126.5403   45.7996    2026-11-06             1       1.6      -6.9       -2.1      57.9                       25.5    1013.1        14.0           多云  Holt线性趋势指数平滑(阻尼)               较低          True      7   3.310770   0.285714   -0.035321
# 4  哈尔滨   126.5403   45.7996    2026-11-07             2       1.5      -7.0       -2.1      61.6                       29.2    1013.1        13.7           多云  Holt线性趋势指数平滑(阻尼)               较低          True      7   3.310770   0.285714   -0.035321
# 5  哈尔滨   126.5403   45.7996    2026-11-08             3       1.5      -7.1       -2.1      65.3                       32.9    1013.1        13.4           多云  Holt线性趋势指数平滑(阻尼)               较低          True      7   3.310770   0.285714   -0.035321
# ---
#                 min   max  mean
# forecast_date                  
# 2026-11-06    -21.8  26.2  10.6
# 2026-11-07    -22.6  26.1  10.4
# 2026-11-08    -23.3  26.1  10.3
# ---
# city forecast_date  temp_mean  humidity  precipitation_probability  pressure  wind_speed weather_type confidence_level
#   漠河    2026-11-06      -21.8      30.1                       13.4    1012.3         3.6            晴               较高
#   漠河    2026-11-07      -22.6      29.5                       10.1    1012.1         3.0            晴               较高
#   漠河    2026-11-08      -23.3      29.0                        6.8    1011.8         2.5            晴               中等
#   上海    2026-11-06       16.7      68.1                       77.6    1007.2        17.1           小雨               较高
#   上海    2026-11-07       16.6      69.7                       81.7    1006.7        17.5           小雨               较高
#   上海    2026-11-08       16.4      71.0                       85.4    1006.2        17.8           小雨               中等
#   广州    2026-11-06       25.4      65.7                       62.6    1010.8        11.7           小雨               较高
#   广州    2026-11-07       25.0      69.9                       68.4    1010.3        11.8           小雨               较高
#   广州    2026-11-08       24.7      74.1                       74.3    1009.9        11.9           小雨               中等
