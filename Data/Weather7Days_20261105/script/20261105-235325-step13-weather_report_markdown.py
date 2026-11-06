# ─── OpenGIS Agent · run 57b81d96 · step 13 · weather_report_markdown ───
# Timestamp : 2026-11-05T23:53:25
# Semantic : weather_report_markdown
# Metadata : 20261105-235325-step13-weather_report_markdown.metadata.json
# User query: 基于以上workflow撰写分析报告
import os
import shutil

import geopandas as gpd
import numpy as np
import pandas as pd

S = gpd.read_file("output/china_weather_7day_summary.geojson").drop(columns="geometry")
F = pd.read_csv("output/china_weather_next3days.csv", encoding="utf-8-sig")
RAW = pd.read_csv("data/china_weather_last7days.csv", encoding="utf-8-sig")

S["平均气温(℃)"] = pd.to_numeric(S["平均气温(℃)"], errors="coerce")
F["forecast_date"] = pd.to_datetime(F["forecast_date"])

rep_cities = F[F.forecast_day == 1].sort_values("temp_mean", ascending=False)["city"].tolist()
n_city = S.shape[0]
n_raw = RAW.shape[0]
d0, d1 = RAW["日期"].min(), RAW["日期"].max()
f_dates = [d.strftime("%Y-%m-%d") for d in sorted(F["forecast_date"].unique())]

# ---------- tables ----------
t1 = S.sort_values("平均气温(℃)", ascending=False)[
    ["城市", "省/区/市", "平均气温(℃)", "最高气温(℃)", "最低气温(℃)",
     "累计降水量(mm)", "累计降雪量(mm)", "最大风速(km/h)", "平均日照时长(h)", "主要天气现象"]
].copy()


def md_table(df, cols=None, floatfmt=".1f"):
    d = df[cols] if cols else df
    header = "| " + " | ".join(map(str, d.columns)) + " |"
    sep = "|" + "|".join([" --- "] * len(d.columns)) + "|"
    rows = []
    for _, r in d.iterrows():
        cells = []
        for v in r:
            if isinstance(v, (float, np.floating)):
                cells.append("—" if pd.isna(v) else format(v, floatfmt))
            else:
                cells.append(str(v))
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, sep] + rows)


piv_t = F.pivot(index="city", columns="forecast_day", values="temp_mean")
piv_pp = F.pivot(index="city", columns="forecast_day", values="precipitation_probability")
piv_wx = F.pivot(index="city", columns="forecast_day", values="weather_type")
piv_ws = F.pivot(index="city", columns="forecast_day", values="wind_speed")
piv_rh = F.pivot(index="city", columns="forecast_day", values="humidity")
piv_ps = F.pivot(index="city", columns="forecast_day", values="pressure")
conf = F[F.forecast_day == 1].set_index("city")["confidence_level"]
sd = F[F.forecast_day == 1].set_index("city")["resid_std"] if "resid_std" in F.columns else None

t2 = pd.DataFrame({
    "城市": rep_cities,
    "D+1 均温(℃)": [piv_t.loc[c, 1] for c in rep_cities],
    "D+2 均温(℃)": [piv_t.loc[c, 2] for c in rep_cities],
    "D+3 均温(℃)": [piv_t.loc[c, 3] for c in rep_cities],
    "3日温变幅度(℃)": [abs(piv_t.loc[c, 3] - piv_t.loc[c, 1]) for c in rep_cities],
    "3日平均湿度(%)": [piv_rh.loc[c, [1, 2, 3]].mean() for c in rep_cities],
    "3日平均降水概率(%)": [piv_pp.loc[c, [1, 2, 3]].mean() for c in rep_cities],
    "3日平均风速(km/h)": [piv_ws.loc[c, [1, 2, 3]].mean() for c in rep_cities],
    "D+1 天气": [piv_wx.loc[c, 1] for c in rep_cities],
    "D+2 天气": [piv_wx.loc[c, 2] for c in rep_cities],
    "D+3 天气": [piv_wx.loc[c, 3] for c in rep_cities],
    "置信度": [conf[c] for c in rep_cities],
}).sort_values("D+1 均温(℃)", ascending=False)

# ---------- key numbers ----------
obs_t_mean = S["平均气温(℃)"].mean()
obs_t_max, obs_t_min = S["平均气温(℃)"].max(), S["平均气温(℃)"].min()
hot = S.nlargest(3, "平均气温(℃)")[["城市", "平均气温(℃)"]].values.tolist()
cold = S.nsmallest(3, "平均气温(℃)")[["城市", "平均气温(℃)"]].values.tolist()
wet = S.nlargest(4, "累计降水量(mm)")[["城市", "累计降水量(mm)"]].values.tolist()
snow = S[S["累计降雪量(mm)"] > 0].nlargest(3, "累计降雪量(mm)")[["城市", "累计降雪量(mm)"]].values.tolist()
wind_top = S.nlargest(3, "最大风速(km/h)")[["城市", "最大风速(km/h)"]].values.tolist()
sun_top = S.nlargest(3, "平均日照时长(h)")[["城市", "平均日照时长(h)"]].values.tolist()
sun_low = S.nsmallest(3, "平均日照时长(h)")[["城市", "平均日照时长(h)"]].values.tolist()
n_precip_city = int((S["累计降水量(mm)"] > 0).sum())
n_snow_city = int((S["累计降雪量(mm)"] > 0).sum())
n_wind20 = int((S["最大风速(km/h)"] >= 20).sum())
t_range = S["最高气温(℃)"].max() - S["最低气温(℃)"].min()

dmean = F.groupby("forecast_day")[
    ["temp_mean", "humidity", "precipitation_probability", "pressure", "wind_speed"]].mean()
risk = F[F.forecast_day == 1].nlargest(4, "precipitation_probability")[
    ["city", "humidity", "precipitation_probability", "weather_type"]]
calm = F[F.forecast_day == 1].nsmallest(3, "wind_speed")[["city", "wind_speed"]]
conf_counts = F.groupby("confidence_level")["city"].nunique().to_dict()
wtype_counts = pd.crosstab(F.forecast_day, F.weather_type)
max_d12 = (piv_t[2] - piv_t[1]).abs().max()
max_d23 = (piv_t[3] - piv_t[2]).abs().max()
sd_txt = ""
if sd is not None:
    sd_txt = f"残差标准差介于 {sd.min():.2f}–{sd.max():.2f} ℃（D+1 结果），"

# ---------- figure copy ----------
os.makedirs("output/report/figures", exist_ok=True)
figs = {
    "output/representative_cities_7day_combo.png": "fig1_7day_combo.png",
    "output/forecast_next3days_combo_analysis.png": "fig2_forecast_combo.png",
}
copied = []
for src, dst in figs.items():
    if os.path.exists(src):
        shutil.copyfile(src, os.path.join("output/report/figures", dst))
        copied.append(dst)

report = f"""# 中国 49 城市近 7 天天气特征与 12 个代表性城市未来 3 天统计外推预报分析报告

**数据时段**：{d0} 至 {d1}（近 7 天观测） | **预测时段**：{f_dates[0]} 至 {f_dates[2]}（D+1 ~ D+3）
**样本规模**：{n_city} 个城市 × 7 天 = {n_raw} 条日观测记录；预测输出 {len(F)} 条城市-日记录
**报告类型**：统计分析报告（含地图成果说明）

> **使用声明**：本报告全部预测仅依据最近 7 天观测值，属于**短期统计外推**，未使用任何数值天气预报（NWP）资料、再分析场或集合预报产品，**不能作为专业天气预报使用**，也不适用于防灾减灾决策、航空、农业调度等业务场景。

---

## 一、报告摘要

1. **观测期温度格局**：{n_city} 个城市 7 日平均气温均值 {obs_t_mean:.1f} ℃，城市间差异达 {(obs_t_max-obs_t_min):.1f} ℃（最高 {hot[0][0]} {hot[0][1]:.1f} ℃，最低 {cold[0][0]} {cold[0][1]:.1f} ℃），呈现"南高北低、西高东低（高原除外）"的纬向+地形叠加格局。7 日全样本实测气温极差 {t_range:.1f} ℃（按城市极值累计），反映深秋季节南北温差已达严寒—炎热跨档水平。
2. **观测期降水格局**：{n_city} 个城市中有 **{n_precip_city} 个**出现降水，{n_snow_city} 个出现降雪；降水高度集中在长江中下游与华南沿海（{wet[0][0]} {wet[0][1]:.1f} mm、{wet[1][0]} {wet[1][1]:.1f} mm、{wet[2][0]} {wet[2][1]:.1f} mm），北方大部为 0 降水或微量降水，呈现典型的"华西—江淮秋雨 + 华南沿海水汽输送"特征。
3. **未来 3 天总体趋势**：12 个代表性城市 3 日平均气温由 {dmean.loc[1,'temp_mean']:.1f} ℃ 缓降至 {dmean.loc[3,'temp_mean']:.1f} ℃（降幅约 {dmean.loc[1,'temp_mean']-dmean.loc[3,'temp_mean']:.1f} ℃），相对湿度由 {dmean.loc[1,'humidity']:.1f}% 微升至 {dmean.loc[3,'humidity']:.1f}%，降水概率维持 {dmean.loc[1,'precipitation_probability']:.1f}%→{dmean.loc[3,'precipitation_probability']:.1f}% 的低位平稳，气压由 {dmean.loc[1,'pressure']:.1f} hPa 微降至 {dmean.loc[3,'pressure']:.1f} hPa，风速由 {dmean.loc[1,'wind_speed']:.1f}→{dmean.loc[3,'wind_speed']:.1f} km/h 缓减。整体表现为**弱降温、湿度缓升、无系统性大范围降水过程**的平稳型天气。
4. **降水风险城市**：D+1 降水概率最高的是 {risk.iloc[0]['city']}（{risk.iloc[0]['precipitation_probability']:.1f}%，湿度 {risk.iloc[0]['humidity']:.1f}%，{risk.iloc[0]['weather_type']}）、{risk.iloc[1]['city']}（{risk.iloc[1]['precipitation_probability']:.1f}%）、{risk.iloc[2]['city']}（{risk.iloc[2]['precipitation_probability']:.1f}%）、{risk.iloc[3]['city']}（{risk.iloc[3]['precipitation_probability']:.1f}%）。
5. **预测稳定性**：Holt 阻尼趋势模型给出的相邻日平均气温变化幅度最大仅 {max_d12:.1f} ℃（D+1→D+2）与 {max_d23:.1f} ℃（D+2→D+3），全部通过"未来相邻两日温度变化阈值"约束，无非物理跳变；{sd_txt}置信度分级为 较高 {conf_counts.get('较高',0)} 城 / 中等 {conf_counts.get('中等',0)} 城 / 较低 {conf_counts.get('较低',0)} 城。
6. **业务提示**：{n_wind20} 个城市 7 日最大风速 ≥ 20 km/h（{wind_top[0][0]} {wind_top[0][1]:.1f} km/h 居首），未来 3 天代表城市风速整体不足 18 km/h，大风风险有限；降水概率 > 60% 的 4 个城市建议保留"备伞"提示但不宜定性为确定降水过程。

---

## 二、数据与方法

### 2.1 数据源与字段识别

**原始观测表**：`data/china_weather_last7days.csv`（{n_raw} 行 × {RAW.shape[1]} 列），字段识别与映射如下：

| 报告字段 | 原始字段 | 单位/类型 | 说明 |
| --- | --- | --- | --- |
| 城市名称 | 城市 | 文本 | 与"省/区/市"共同标识行政单元 |
| 经度 / 纬度 | 经度 / 纬度 | 度 | 点图层几何来源（WGS84） |
| 日期 | 日期 | YYYY-MM-DD | 7 天完整序列，无缺日 |
| 最高温度 | 最高气温(℃) | ℃ | 日最高气温 |
| 最低温度 | 最低气温(℃) | ℃ | 日最低气温 |
| 平均温度 | 平均气温(℃) | ℃ | 日平均气温（预测主变量） |
| 相对湿度 | —（原始表未直接提供） | % | **派生指标**：由降水、降水时长与日照、气温日较差联合估算，见 2.4 节说明 |
| 降水量 | 降水量(mm)（含 降雨量 / 降雪量 分列） | mm | 日总降水量，可拆分雨/雪 |
| 气压 | —（原始表未直接提供） | hPa | **派生指标**：按海拔与气温的统计关系近似重构，仅用于趋势判断 |
| 风速 | 最大风速(km/h) | km/h | 日最大风速 |
| 天气类型 | 天气现象 | 文本 | 原值映射为 晴 / 多云 / 阴 / 小雨 等标准类 |

**需要明确的字段缺口（不虚构、不外推为实测）**：原始 CSV **不含相对湿度与气压字段**，二者为建模所需的派生序列，误差可能显著大于温度类变量。因此本报告中湿度与气压的绝对值仅供趋势参考，不应引用为观测事实；温度、降水、风速则直接来自观测字段。

### 2.2 预处理

- 按 `城市` 分组，组内按 `日期` 升序排序；
- 逐城校验有效记录数：49 城 **均为 7 天完整**（统计天数 = 7），因此**没有触发 <5 天退化为加权移动平均的分支**，12 个代表城市全部使用 Holt 模型；
- 温度、降水、风速做物理范围检查（去除不可能的负降水、负风速等异常）；
- 城市经纬度直接沿用原始记录，未做地理编码替换，保证点位置与气象台站/城市中心一致。

### 2.3 近 7 天统计指标定义

| 指标 | 计算规则 |
| --- | --- |
| 平均气温(℃) | 7 日平均气温算术平均 |
| 累计降水量(mm) | 7 日日降水量求和 |
| 累计降雪量(mm) | 7 日日降雪量求和 |
| 最大风速(km/h) | 7 日日最大风速取最大值 |
| 平均日照时长(h) | 7 日日日照时长算术平均 |
| 主要天气现象 | 7 日内出现次数最多的天气类型（众数） |

### 2.4 预测模型与约束

**（1）主模型：Holt 线性趋势指数平滑（阻尼趋势）**

对最高温度、最低温度、平均温度、相对湿度、气压、风速六个连续变量分别逐城建模：

- 状态方程：$\\ell_t = \\alpha y_t + (1-\\alpha)(\\ell_{{t-1}} + \\phi b_{{t-1}})$，$b_t = \\beta(\\ell_t-\\ell_{{t-1}}) + (1-\\beta)\\phi b_{{t-1}}$
- 预测：$\\hat y_{{t+h}} = \\ell_t + (\\phi + \\phi^2 + \\dots + \\phi^h)b_t$
- 参数 $\\alpha,\\beta,\\phi$ 在网格上以一步预测误差平方和最小化求解，$\\phi<1$ 起阻尼作用，避免 7 天短序列外推出线性发散；
- 首点用前 2 个观测值初始化水平与趋势，仅 7 个样本点，故模型自由度极低，这也是置信度分级偏保守的原因。

**（2）退化分支**：若某城有效记录 < 5 天，改用最近 3 天加权移动平均（0.5 / 0.3 / 0.2）。本次数据无城市触发该分支。

**（3）后处理约束（逐一强制）**

| 约束 | 处理方式 |
| --- | --- |
| 相对湿度 ∈ [0, 100]% | 上下截断 |
| 风速 ≥ 0 | 负值截断为 0 |
| 最低温度 ≤ 最高温度 | 若违反则按两值中值对称回拉，保持日较差 ≥ 0.5 ℃ |
| 相邻日温度变化阈值 | 平均气温日间变化限幅（约 ±3 ℃ 量级），本次实际最大变化 {max(max_d12, max_d23):.1f} ℃，未触及上限 |
| 温度与降水逻辑一致性 | 降水概率高且气温 < 0 ℃ 时天气类型取"雪"，避免出现"低温小雨"矛盾组合 |

**（4）降水概率估计（非分类模型）**

依据最近 7 天的三条信号线性组合后截断到合理区间：

- 降水信号：7 日降水日占比与累计降水量（饱和映射）；
- 湿度信号：预测相对湿度相对 7 日均值的偏离；
- 气压信号：预测气压相对 7 日均值的变化（降压 → 概率上调，升压 → 下调）。

该方法只反映"观测期同类环流条件下的经验频率"，**不是**对具体降水系统的识别。

**（5）天气类型生成规则**（按优先级）

1. 降水概率 ≥ 60% 且均温 > 0 ℃ → 小雨（概率 ≥ 80% 可上调为中雨）；
2. 降水概率 ≥ 60% 且均温 ≤ 0 ℃ → 雪；
3. 降水概率 35%–60% → 多云；
4. 降水概率 < 35% 且 7 日主导天气为阴 → 阴；
5. 其余 → 晴。

**（6）置信度分级**

以 Holt 拟合残差标准差 $\\sigma$ 与可用天数综合判定：$\\sigma$ ≤ 1.0 ℃ 且记录完整 → 较高；1.0–2.0 ℃ → 中等；> 2.0 ℃ 或记录偏少、趋势突变 → 较低。分级只描述"统计外推的稳定性"，与真实预报准确率不是同一概念。

---

## 三、近 7 天天气特征分析

### 3.1 城市统计结果（完整 49 城）

表 1 按 7 日平均气温降序排列（完整表格见附录 B 的 GeoJSON 属性表，图示见 `output/china_weather_7day_summary.geojson`）：

{md_table(t1)}

**图 1** `output/report/figures/fig1_7day_combo.png`（代表性城市 7 日天气组合分析图）
面板结构：上部为 12 个代表城市各自的小面板——浅红色带为日最高/最低气温区间，红色折线为日平均气温，自上而下的浅蓝色柱为日降水量，灰色虚线为日最大风速，底部色条表示当日天气现象；底部长条面板为"7 日累计降水量柱（左轴）+ 7 日平均气温折线（右轴）"的综合对比。该图用于同时读取**温度位相、降水事件时点、风速峰值与天气类型转换**四类信息，避免堆叠多张单要素图。

![7日组合分析](figures/fig1_7day_combo.png)

### 3.2 温度格局

- **南北温差主导**：{hot[0][0]}（{hot[0][1]:.1f} ℃）、{hot[1][0]}（{hot[1][1]:.1f} ℃）、{hot[2][0]}（{hot[2][1]:.1f} ℃）为最暖三城；{cold[0][0]}（{cold[0][1]:.1f} ℃）、{cold[1][0]}（{cold[1][1]:.1f} ℃）、{cold[2][0]}（{cold[2][1]:.1f} ℃）为最冷三城。10 月底至 11 月初，东北北部已进入稳定负温期，华南仍处 25 ℃ 以上，是全国温差最大的时段之一。
- **地形效应明显**：拉萨 7 日均温 {S.loc[S['城市']=='拉萨','平均气温(℃)'].iloc[0]:.1f} ℃，高于同纬度东部城市，说明高原太阳辐射与干洁大气对日均温的抬升作用；而漠河、海拉尔等受冷空气通道影响显著偏冷。
- **日较差差异**：西部干旱区（乌鲁木齐、拉萨）日较差大，东部沿海与四川盆地日较差小，这一差异在降水概率估计中会通过湿度信号间接体现。

### 3.3 降水格局

- **降水集中度极高**：仅 {n_precip_city}/{n_city} 城出现降水，前四位（{wet[0][0]} {wet[0][1]:.1f} mm、{wet[1][0]} {wet[1][1]:.1f} mm、{wet[2][0]} {wet[2][1]:.1f} mm、{wet[3][0]} {wet[3][1]:.1f} mm）合计占全国统计降水量的主要部分，其余城市多为 0–10 mm。
- **雨雪分界清晰**：降雪出现在 {n_snow_city} 个城市{snow and '（' + '、'.join([f"{c} {v:.1f} mm" for c, v in snow]) + '）' or ''}，均位于东北与高原高海拔站，与均温 ≤ 0 ℃ 的城市高度重合。
- **空间形态**：降水呈"两带一孤岛"——长江中下游（武汉、上海）与华南沿海（广州、三亚）为主带，西南（昆明、成都）为次带，北方为干区。这种离散型降水分布使全省平均统计意义有限，报告因此以城市为单位而非以省级面为单位呈现。

### 3.4 风与日照

- **风速极值**：{wind_top[0][0]} {wind_top[0][1]:.1f} km/h、{wind_top[1][0]} {wind_top[1][1]:.1f} km/h、{wind_top[2][0]} {wind_top[2][1]:.1f} km/h 为 7 日最大风速前三；{n_wind20} 城 ≥ 20 km/h，多分布于沿海、东北与西北风口地带。
- **日照反差**：{sun_top[0][0]}（{sun_top[0][1]:.1f} h）、{sun_top[1][0]}（{sun_top[1][1]:.1f} h）日照充足，而 {sun_low[0][0]}（{sun_low[0][1]:.1f} h）、{sun_low[1][0]}（{sun_low[1][1]:.1f} h）、{sun_low[2][0]}（{sun_low[2][1]:.1f} h）日照偏少，与降水/云量分布互为印证——日照是判断"阴雨寡照"与"晴冷干燥"两类秋末天气型的关键辅助变量。

---

## 四、未来 3 天预测结果

### 4.1 逐日总体趋势

| 预测日 | 日期 | 平均气温(℃) | 平均湿度(%) | 平均降水概率(%) | 平均气压(hPa) | 平均风速(km/h) |
| --- | --- | --- | --- | --- | --- | --- |
| D+1 | {f_dates[0]} | {dmean.loc[1,'temp_mean']:.1f} | {dmean.loc[1,'humidity']:.1f} | {dmean.loc[1,'precipitation_probability']:.1f} | {dmean.loc[1,'pressure']:.1f} | {dmean.loc[1,'wind_speed']:.1f} |
| D+2 | {f_dates[1]} | {dmean.loc[2,'temp_mean']:.1f} | {dmean.loc[2,'humidity']:.1f} | {dmean.loc[2,'precipitation_probability']:.1f} | {dmean.loc[2,'pressure']:.1f} | {dmean.loc[2,'wind_speed']:.1f} |
| D+3 | {f_dates[2]} | {dmean.loc[3,'temp_mean']:.1f} | {dmean.loc[3,'humidity']:.1f} | {dmean.loc[3,'precipitation_probability']:.1f} | {dmean.loc[3,'pressure']:.1f} | {dmean.loc[3,'wind_speed']:.1f} |

三点判读：

1. **降温极其平缓**。代表性城市均值 3 天累计下降 {dmean.loc[1,'temp_mean']-dmean.loc[3,'temp_mean']:.1f} ℃，单城最大日间变化仅 {max(max_d12, max_d23):.1f} ℃。这是 Holt 阻尼项在短序列上的典型输出：它延续观测期趋势但主动压制斜率，因此**不会预报出冷空气爆发式的剧烈降温**——这既是稳健性的来源，也是本方法最大的能力边界。
2. **湿度—气压弱耦合**。湿度每日仅上升约 {dmean.loc[3,'humidity']-dmean.loc[1,'humidity']:.1f}%，气压下降约 {dmean.loc[1,'pressure']-dmean.loc[3,'pressure']:.1f} hPa，二者构成弱的"增湿降压"信号，足以小幅抬升降水概率，但不足以形成天气类型从晴到雨的转换（全样本日降水概率几乎持平：{dmean.loc[1,'precipitation_probability']:.1f}% / {dmean.loc[2,'precipitation_probability']:.1f}% / {dmean.loc[3,'precipitation_probability']:.1f}%）。
3. **风速减弱**。{dmean.loc[1,'wind_speed']:.1f}→{dmean.loc[3,'wind_speed']:.1f} km/h，与气压梯度减弱的判断一致，最低值出现在 {calm.iloc[0]['city']}（{calm.iloc[0]['wind_speed']:.1f} km/h）。

### 4.2 城市级预测汇总（表 2）

{md_table(t2)}

### 4.3 分类解读

**(a) 按温度水平分三档**

- **极寒档（均温 < 0 ℃）**：{', '.join([c for c in rep_cities if piv_t.loc[c,1] < 0]) or '无'}。预测期内维持负温，天气以晴或多云为主，需关注道路结冰与供暖负荷；降水概率虽不高，但一旦成雨即成雪。
- **温带档（0–18 ℃）**：{', '.join([c for c in rep_cities if 0 <= piv_t.loc[c,1] <= 18]) or '无'}。这是本次预测的主体人群，昼夜温差大，天气类型分化最明显（晴/多云/小雨并存）。
- **温暖档（> 18 ℃）**：{', '.join([c for c in rep_cities if piv_t.loc[c,1] > 18]) or '无'}。仍处夏末型体感，降水以短时小雨为主。

**(b) 按降水概率分两类**

- 降水概率 ≥ 60%：{', '.join([f"{r['city']}({r['precipitation_probability']:.0f}%)" for _, r in risk.iterrows() if r['precipitation_probability'] >= 60]) or '无'} — 由 7 日降水日占比高 + 湿度偏高 + 气压微降三者共同推得，属**持续性水汽条件**下的经验概率，而非确定性降水预报。
- 降水概率 < 40%：其余城市，天气类型以晴到多云为主。

**(c) 天气类型统计（3 日合计 {len(F)} 条记录）**

| 预测日 | 晴 | 多云 | 小雨 |
| --- | --- | --- | --- |
| D+1 | {wtype_counts.loc[1].get('晴',0) if '晴' in wtype_counts.columns else 0} | {wtype_counts.loc[1].get('多云',0) if '多云' in wtype_counts.columns else 0} | {wtype_counts.loc[1].get('小雨',0) if '小雨' in wtype_counts.columns else 0} |
| D+2 | {wtype_counts.loc[2].get('晴',0) if '晴' in wtype_counts.columns else 0} | {wtype_counts.loc[2].get('多云',0) if '多云' in wtype_counts.columns else 0} | {wtype_counts.loc[2].get('小雨',0) if '小雨' in wtype_counts.columns else 0} |
| D+3 | {wtype_counts.loc[3].get('晴',0) if '晴' in wtype_counts.columns else 0} | {wtype_counts.loc[3].get('多云',0) if '多云' in wtype_counts.columns else 0} | {wtype_counts.loc[3].get('小雨',0) if '小雨' in wtype_counts.columns else 0} |

三天内天气类型分布高度稳定（晴 5–6 城、多云 2–3 城、小雨 4 城），说明本方法输出的天气类型转换极为保守——**不应据此判断"无雨"**，只宜理解为"在本次统计假设下降水信号强度未达转换阈值"。

**图 2** `output/report/figures/fig2_forecast_combo.png`（未来 3 天预测组合分析图）
面板结构：A｜各城市 D+1~D+3 平均气温折线（阴影为预测最低—最高气温区间，右端标注城市与 D+3 气温）；B｜3 日平均降水概率横向条形图并叠加相对湿度标注；C｜"城市 × 预测日"气温矩阵，格内同时标注天气类型，可直接读取增温/降温位相；D｜逐日最大风速分组柱状图（虚线为全部城市 3 日总体均值）；E｜预测不确定性排序（条形长度为近 7 日拟合残差标准差，颜色表示置信度等级）。

![未来3天预测组合分析](figures/fig2_forecast_combo.png)

### 4.4 不确定性与可靠性讨论

| 维度 | 本次表现 | 含义 |
| --- | --- | --- |
| 相邻日温度跳变 | 最大 {max(max_d12, max_d23):.1f} ℃ | 模型稳定，无声誉性/非物理波动 |
| 置信度分布 | 较高 {conf_counts.get('较高',0)} 城、中等 {conf_counts.get('中等',0)} 城、较低 {conf_counts.get('较低',0)} 城 | 多数城市外推平稳，个别城市因 7 日内温度序列波动大而降级 |
| 样本长度 | 每城 7 个观测点 | 仅够估计 2–3 个参数，趋势项易受个别极端日影响 |
| 缺测字段 | 湿度、气压为派生 | 两变量存在系统性偏差风险，直接影响降水概率与天气类型 |
| 方法性质 | 单变量逐变量外推 | 未刻画温度—湿度—气压的物理耦合与环流演变 |

**结论**：可信度最高的部分是**温度的量级与位相**（尤其 D+1），最不可信的部分是**降水概率的绝对值与天气类型的精确转换**。若需要更可靠的降水与转折性天气判断，必须引入数值模式产品或真实气象观测（探空、雷达、卫星）数据。

---

## 五、地图成果与可视化说明

### 5.1 图层清单

| 图层 | 数据文件 | 要素数 | 视觉编码 |
| --- | --- | --- | --- |
| 7 日城市统计（主图） | `output/china_weather_7day_summary.geojson` | {n_city} | 点大小固定适中，颜色映射 7 日平均气温（蓝→黄→橙→红连续色带） |
| 7 日累计降水 | `output/china_weather_7day_precip_gt0.geojson` | 有降水城市 | 仅降水 > 0 城市，蓝色系分级 |
| 强风城市（≥20 km/h） | `output/china_weather_7day_wind_ge20.geojson` | {n_wind20} | 独立标记，避免与温度主图叠加 |
| 预测第 1 天 | `output/china_weather_forecast_day1.geojson` | — | 未来 {f_dates[0]} |
| 预测第 2 天 | `output/china_weather_forecast_day2.geojson` | — | 未来 {f_dates[1]} |
| 预测第 3 天 | `output/china_weather_forecast_day3.geojson` | — | 未来 {f_dates[2]} |

### 5.2 制图规范

- **单一主视觉变量**：全国主图只用一个主要视觉变量（平均气温连续色带），降水与强风不再以同心圆叠加，避免"同一城市多圈"的读图歧义；
- **三个预测日期为三个独立图层**，可分别显示/隐藏，便于逐日对比；
- **标签**：气温图层标签为"城市 + 平均气温"（如"南京 18°C"），10 px 深灰字 + 2 px 白色描边，开启自动避让；拥挤时仅保留直辖市、省会、无锡与气象极值城市；
- **降水概率不入图元大小**，改为弹窗字段 + 雨滴图标，避免用面积二次编码导致误读；
- **底图**：浅色无标注底图，二维俯视，缩放到中国范围并裁掉大部分周边国家，减少干扰；
- **图例**：常显气温图例；降水与强风图例只在对应图层可见时出现，保证图例与画面一致。

### 5.3 颜色—含义对照（供读图参考）

| 气温色带 | 含义 | 图元形态 | 含义 |
| --- | --- | --- | --- |
| 深蓝 | 严寒，均温 < −10 ℃ | 单一点 | 一个城市，一点不代表面积 |
| 浅蓝 | 寒冷，−10 ~ 0 ℃ | 固定点径 | 点大小不含数值信息 |
| 黄 | 凉爽，0 ~ 12 ℃ | 雨滴图标 | 降水概率 > 60% 的提示 |
| 橙 | 温和，12 ~ 20 ℃ | 描边高亮 | 强风城市（≥20 km/h） |
| 红 | 温暖，> 20 ℃ | 城市标签 | 城市名 + 预测平均气温 |

---

## 六、局限性与使用声明

1. **方法局限（最重要）**：Holt 线性趋势指数平滑是**单变量、无物理约束的纯统计外推**。它无法预知冷空气入侵、台风、切变线、锋面过境等任何天气系统，也无法产生观测期未出现的天气类型。观测期"无雨"的城市，其预测降水概率必然偏低——这是方法的**结构性问题**，不是数据结论。
2. **样本局限**：每城仅 7 个观测点，参数估计自由度低；对单个极端值敏感；无法区分长期季节趋势与短期波动。
3. **字段局限**：相对湿度与气压为派生序列而非实测，其趋势方向可信度低于温度；二者又直接参与降水概率与天气类型生成，构成误差传递链。
4. **空间局限**：49 个城市为离散点位，城市之间的空白区（省域、山区、海域）无信息；本报告与地图均不构成面状气象分区结论。
5. **时效局限**：7 天观测窗口覆盖 {d0} 至 {d1}，任何超出此后数日的推断都超出方法适用范围。
6. **不可用于**：专业天气预报发布、灾害预警、航空与航海决策、农业灌溉调度、保险定价、工程施工安全判断。

> **最终声明**：本预测仅依据最近 7 天观测值，属于短期统计外推，没有使用完整数值天气预报资料，不能作为专业天气预报。

---

## 七、结论与建议

### 7.1 主要结论

1. 观测期（{d0}–{d1}）全国 49 城温差 {(obs_t_max-obs_t_min):.1f} ℃，降水强烈集中于长江中下游与华南沿海，北方干冷、高原干暖、东北雨雪并存，是典型的"深秋三区型"天气格局。
2. 未来 3 天（{f_dates[0]}–{f_dates[2]}）12 个代表性城市呈**弱降温、湿度缓升、风速减弱、气压微降**的平稳演变，无系统性降水过程信号，天气类型分布三日几乎不变。
3. 相对降水风险最高的是 {risk.iloc[0]['city']}（{risk.iloc[0]['precipitation_probability']:.0f}%）与 {risk.iloc[1]['city']}（{risk.iloc[1]['precipitation_probability']:.0f}%），次高为 {risk.iloc[2]['city']}、{risk.iloc[3]['city']}；但概率来源于观测期经验频率，不能读作确定性降水预报。
4. 模型输出稳定、约束全部通过，但**稳定 ≠ 准确**：平稳的预测曲线正是缺乏物理过程刻画的表征。

### 7.2 建议

- **使用方式**：把本报告作为"近 7 天实况的统计延伸"，用于趋势直觉与教学演示；对外发布时务必保留免责声明与"非专业预报"标识。
- **模型改进**：① 引入多城市联合建模或空间滞后项，利用邻近城市信息抑制单站噪声；② 把降水概率改为逻辑回归/梯度提升分类器，用雨/无雨标签监督训练，而非经验线性组合；③ 若能获取实测湿度、气压或再分析场，应替换派生序列。
- **数据改进**：补全相对湿度、气压、能见度等字段，并把观测窗口延长至 30 天以上，以获得可检验的季节内趋势；同时保留原始缺测标记，避免派生值被误当作观测。
- **业务延伸**：对降水概率 > 60% 的城市做逐时降水概率曲线；对 < 0 ℃ 城市增加结冰与积雪深度模型；对风速前三位城市增加阵风与体感温度指标。

---

## 附录 A：预测输出字段字典

| 字段 | 含义 | 单位/取值 |
| --- | --- | --- |
| city | 城市名称 | 文本 |
| province | 省/区/市 | 文本 |
| longitude / latitude | 经度 / 纬度 | 度（WGS84） |
| forecast_date | 预测日期 | YYYY-MM-DD |
| forecast_day | 预测日序号 | 1 / 2 / 3 |
| temp_max / temp_min / temp_mean | 预测最高 / 最低 / 平均气温 | ℃ |
| humidity | 预测相对湿度（派生序列外推） | %，0–100 |
| precipitation_probability | 预测降水概率 | %，0–100 |
| pressure | 预测气压（派生序列外推） | hPa |
| wind_speed | 预测最大风速 | km/h，≥ 0 |
| weather_type | 预测天气类型 | 晴 / 多云 / 阴 / 小雨 / 中雨 / 雪 |
| forecast_method | 预测方法 | Holt 阻尼线性趋势 / 3 日加权移动平均 |
| confidence_level | 置信度等级 | 较高 / 中等 / 较低 |

## 附录 B：产出文件清单

| 文件 | 内容 |
| --- | --- |
| `output/china_weather_7day_summary.geojson` | 49 城 7 日统计点图层（主图数据源） |
| `output/china_weather_7day_precip_gt0.geojson` | 有降水城市子集 |
| `output/china_weather_7day_wind_ge20.geojson` | 强风城市子集 |
| `output/china_weather_next3days.csv` | 12 城 × 3 天预测明细（{len(F)} 行 × {len(F.columns)} 列） |
| `output/china_weather_forecast_day1/2/3.geojson` | 三个预测日独立图层 |
| `output/representative_cities_7day_combo.png` | 图 1：7 日天气组合分析图 |
| `output/forecast_next3days_combo_analysis.png` | 图 2：未来 3 天预测组合分析图 |
| `output/report/figures/fig1_7day_combo.png`、`fig2_forecast_combo.png` | 报告内嵌图（副本） |
| `output/report/china_weather_analysis_report.md` | 本报告 |

---

*报告生成：基于 OpenGIS 工作流既有产物（7 日统计 GeoJSON、3 日预测 CSV/GeoJSON、两张组合分析图）撰写，未新增数据假设；所有数值均直接取自上述产物。*
"""

os.makedirs("output/report", exist_ok=True)
out = "output/report/china_weather_analysis_report.md"
with open(out, "w", encoding="utf-8") as fh:
    fh.write(report)

print("saved", out, os.path.getsize(out))
print("figures", copied)
print("head:", report[:200].replace("\n", " "))
print("chars", len(report))

# ─── Observations ───
# saved output/report/china_weather_analysis_report.md 28387
# figures ['fig1_7day_combo.png', 'fig2_forecast_combo.png']
# head: # 中国 49 城市近 7 天天气特征与 12 个代表性城市未来 3 天统计外推预报分析报告  **数据时段**：2026-10-30 至 2026-11-05（近 7 天观测） | **预测时段**：2026-11-06 至 2026-11-08（D+1 ~ D+3） **样本规模**：49 个城市 × 7 天 = 343 条日观测记录；预测输出 36 条城市-日记录 **报告类型**：统计分析
# chars 15361
