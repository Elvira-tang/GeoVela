# ─── OpenGIS Agent · run 984591d9 · step 4 · forecast_next3days_combo_analysis ───
# Timestamp : 2026-11-05T23:49:45
# Semantic : forecast_next3days_combo_analysis
# Metadata : 20261105-234945-step04-forecast_next3days_combo_analysis.metadata.json
# User query: 根据预测结果绘制组合分析图
import os

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

cands = ["PingFang SC", "STHeiti", "Heiti SC", "SimHei", "Microsoft YaHei", "Noto Sans CJK SC"]
avail = set(f.name for f in fm.fontManager.ttflist)
plt.rcParams["font.sans-serif"] = [c for c in cands if c in avail] or ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_csv("output/china_weather_next3days.csv", encoding="utf-8-sig")
df["forecast_date"] = pd.to_datetime(df["forecast_date"])
DAY_LAB = df.groupby("forecast_day")["forecast_date"].first().dt.strftime("%m/%d").to_dict()
days = sorted(df["forecast_day"].unique())
order = df[df.forecast_day == 1].sort_values("temp_mean", ascending=False)["city"].tolist()
n = len(order)

WX_C = {"晴": "#FCD34D", "多云": "#CBD5E1", "阴": "#94A3B8", "小雨": "#7DD3FC",
        "中雨": "#38BDF8", "大雨": "#2563EB", "雪": "#C7D2FE"}
CONF_C = {"较高": "#16A34A", "中等": "#F59E0B", "较低": "#DC2626"}


def wx_color(s):
    s = str(s)
    for k, v in WX_C.items():
        if k in s:
            return v
    if "雪" in s:
        return WX_C["雪"]
    if "雨" in s:
        return WX_C["小雨"]
    return "#E5E7EB"


city_cmap = plt.get_cmap("RdYlBu_r")
cCOL = {c: city_cmap(i / max(n - 1, 1)) for i, c in enumerate(order)}

fig = plt.figure(figsize=(20.0, 12.6), facecolor="white")
gs = GridSpec(2, 6, figure=fig, height_ratios=[1.0, 0.80], hspace=0.34, wspace=1.55,
              left=0.055, right=0.975, top=0.875, bottom=0.075)

# ── A 气温预测扇形图 ────────────────────────────────────────────
axA = fig.add_subplot(gs[0, 0:2])
for c in order:
    d = df[df.city == c].sort_values("forecast_day")
    x = d["forecast_day"].values
    axA.fill_between(x, d["temp_min"], d["temp_max"], color=cCOL[c], alpha=0.13, lw=0)
    axA.plot(x, d["temp_mean"], color=cCOL[c], lw=2.0, marker="o", ms=4.6,
             mec="white", mew=0.8, zorder=4)
ends = sorted([(df[(df.city == c) & (df.forecast_day == 3)]["temp_mean"].iloc[0], c) for c in order])
lab_y, last = [], None
for y, c in ends:
    y = y if last is None else max(y, last + 1.9)
    lab_y.append((y, c))
    last = y
for y, c in lab_y:
    yy = df[(df.city == c) & (df.forecast_day == 3)]["temp_mean"].iloc[0]
    axA.plot([3.0, 3.16], [yy, y], color=cCOL[c], lw=0.7, alpha=0.7, clip_on=False)
    axA.text(3.22, y, f"{c} {yy:.0f}°", fontsize=8.2, color=cCOL[c], va="center",
             fontweight="bold")
axA.set_xlim(0.88, 3.05)
axA.set_ylim(-34, 33)
axA.set_xticks(days)
axA.set_xticklabels([f"D+{d}\n{DAY_LAB[d]}" for d in days], fontsize=9, color="#334155")
axA.set_ylabel("平均气温 (℃)", fontsize=9.5, color="#334155")
axA.grid(color="#EEF2F7", lw=0.7, zorder=0)
for s in ["top", "right"]:
    axA.spines[s].set_visible(False)
for s in ["left", "bottom"]:
    axA.spines[s].set_color("#94A3B8")
axA.set_title("A｜未来3天各城市平均气温（阴影为最低—最高气温区间）",
              fontsize=12, fontweight="bold", color="#0F172A", loc="left", pad=14)

# ── B 降水概率 + 湿度 ──────────────────────────────────────────
axB = fig.add_subplot(gs[0, 2:4])
b = (df.groupby("city")
     .agg(pp=("precipitation_probability", "mean"), rh=("humidity", "mean"))
     .reindex(order).sort_values("pp"))
yb = np.arange(len(b))
pp_cmap = LinearSegmentedColormap.from_list("pp", ["#EFF6FF", "#93C5FD", "#2563EB"])
cols = [pp_cmap(min(v / 100.0, 1.0)) for v in b["pp"]]
axB.barh(yb, b["pp"], height=0.64, color=cols, edgecolor="#94A3B8", lw=0.5)
for i, (c, r) in enumerate(zip(b["pp"], b["rh"])):
    axB.text(c + 1.6, i, f"{c:.0f}%", va="center", fontsize=7.8, color="#1E3A8A")
    axB.text(99.5, i, f"RH {r:.0f}%", va="center", ha="right", fontsize=7.2, color="#64748B")
axB.set_yticks(yb)
axB.set_yticklabels(b.index, fontsize=8.0, color="#334155")
axB.set_xlim(0, 100)
axB.set_xlabel("3日平均降水概率 (%)", fontsize=9, color="#1E3A8A")
axB.grid(axis="x", color="#EEF2F7", lw=0.7)
for s in ["top", "right", "left"]:
    axB.spines[s].set_visible(False)
axB.spines["bottom"].set_color("#94A3B8")
axB.set_title("B｜降水概率与相对湿度（右侧灰色为RH）",
              fontsize=12, fontweight="bold", color="#0F172A", loc="left", pad=14)

# ── C 气温热力图 ──────────────────────────────────────────────
axC = fig.add_subplot(gs[0, 4:6])
mat = np.array([[df[(df.city == c) & (df.forecast_day == d)]["temp_mean"].iloc[0] for d in days]
                for c in order])
tcmap = LinearSegmentedColormap.from_list(
    "t", ["#1D4ED8", "#38BDF8", "#34D399", "#FACC15", "#FB923C", "#DC2626"])
im = axC.imshow(mat, cmap=tcmap, aspect="auto")
for i, c in enumerate(order):
    for j, d in enumerate(days):
        row = df[(df.city == c) & (df.forecast_day == d)]["temp_mean"].iloc[0]
        wxs = df[(df.city == c) & (df.forecast_day == d)]["weather_type"].iloc[0]
        axC.text(j, i - 0.13, f"{row:.0f}°", ha="center", va="center", fontsize=8.6,
                 fontweight="bold", color="white" if abs(row) > 14 else "#0F172A")
        axC.text(j, i + 0.26, str(wxs), ha="center", va="center", fontsize=7.0, color="#334155")
axC.set_xticks(range(len(days)))
axC.set_xticklabels([f"D+{d} {DAY_LAB[d]}" for d in days], fontsize=8.0, color="#334155")
axC.set_yticks(range(len(order)))
axC.set_yticklabels(order, fontsize=8.0, color="#334155")
axC.set_xticks(np.arange(-0.5, len(days), 1), minor=True)
axC.set_yticks(np.arange(-0.5, len(order), 1), minor=True)
axC.grid(which="minor", color="white", lw=1.4)
axC.tick_params(which="minor", length=0)
for s in axC.spines.values():
    s.set_visible(False)
cb = fig.colorbar(im, ax=axC, orientation="horizontal", fraction=0.045, pad=0.10, aspect=45)
cb.set_label("预测平均气温 (℃)", fontsize=8.2, color="#334155")
cb.ax.tick_params(labelsize=7.5)
axC.set_title("C｜城市 × 预测日 气温矩阵（格内标注天气类型）",
              fontsize=12, fontweight="bold", color="#0F172A", loc="left", pad=14)

# ── D 逐日风速 ────────────────────────────────────────────────
axD = fig.add_subplot(gs[1, 0:3])
xd = np.arange(len(order))
bw = 0.26
shade = ["#94A3B8", "#64748B", "#334155"]
for k, d in enumerate(days):
    v = [df[(df.city == c) & (df.forecast_day == d)]["wind_speed"].iloc[0] for c in order]
    bars = axD.bar(xd + (k - 1) * bw, v, width=bw, color=shade[k],
                   edgecolor="white", lw=0.6, label=f"D+{d} {DAY_LAB[d]}")
    for xi, vv in zip(xd + (k - 1) * bw, v):
        axD.text(xi, vv + 0.35, f"{vv:.0f}", ha="center", fontsize=6.2, color="#475569")
axD.axhline(df["wind_speed"].mean(), color="#DC2626", lw=1.0, ls=(0, (4, 3)), alpha=0.8)
axD.text(len(order) - 0.4, df["wind_speed"].mean() + 0.5, f"总体均值 {df['wind_speed'].mean():.1f}",
         ha="right", fontsize=7.8, color="#DC2626")
axD.set_xticks(xd)
axD.set_xticklabels(order, fontsize=8.4, color="#334155")
axD.set_ylabel("最大风速 (km/h)", fontsize=9.5, color="#334155")
axD.set_ylim(0, df["wind_speed"].max() * 1.30)
axD.grid(axis="y", color="#EEF2F7", lw=0.7)
for s in ["top", "right"]:
    axD.spines[s].set_visible(False)
for s in ["left", "bottom"]:
    axD.spines[s].set_color("#94A3B8")
axD.legend(frameon=False, fontsize=8.2, ncol=3, loc="upper right")
axD.set_title("D｜逐日最大风速预测（虚线为全部城市3日总体均值）",
              fontsize=12, fontweight="bold", color="#0F172A", loc="left", pad=12)

# ── E 不确定性 / 置信度 ────────────────────────────────────────
axE = fig.add_subplot(gs[1, 3:6])
u = (df.groupby("city")
     .agg(sd=("resid_std", "mean"), conf=("confidence_level", "first"))
     .reindex(order).sort_values("sd"))
ye = np.arange(len(u))
axE.barh(ye, u["sd"], height=0.62, color=[CONF_C.get(c, "#94A3B8") for c in u["conf"]],
         edgecolor="white", lw=0.6)
for i, (v, c) in enumerate(zip(u["sd"], u["conf"])):
    axE.text(v + 0.04, i, f"{v:.2f}  {c}", va="center", fontsize=7.6, color="#334155")
axE.set_yticks(ye)
axE.set_yticklabels(u.index, fontsize=8.4, color="#334155")
axE.set_xlabel("近7日拟合残差标准差 (℃)｜越小越稳定", fontsize=9, color="#334155")
axE.set_xlim(0, u["sd"].max() * 1.32)
axE.grid(axis="x", color="#EEF2F7", lw=0.7)
for s in ["top", "right", "left"]:
    axE.spines[s].set_visible(False)
axE.spines["bottom"].set_color("#94A3B8")
axE.legend(handles=[Patch(facecolor=v, label=f"置信度{k}") for k, v in CONF_C.items()],
           frameon=False, fontsize=8.2, ncol=3, loc="lower right")
axE.set_title("E｜预测不确定性（Holt阻尼趋势·近7日残差）",
              fontsize=12, fontweight="bold", color="#0F172A", loc="left", pad=12)

fig.suptitle("中国12个代表性城市 未来3天天气预测组合分析（2026-11-06 至 2026-11-08）",
             fontsize=18, fontweight="bold", color="#0F172A", x=0.055, ha="left", y=0.955)
fig.text(0.055, 0.918,
         "预测方法：Holt 线性趋势指数平滑（阻尼）；仅依据最近7天观测值做短期统计外推，"
         "未使用数值天气预报资料，不能作为专业天气预报使用。",
         fontsize=9.6, color="#B45309")

out = "output/forecast_next3days_combo_analysis.png"
os.makedirs("output", exist_ok=True)
fig.savefig(out, dpi=150, facecolor="white", bbox_inches="tight")
print("saved", out, os.path.getsize(out))
print(df.groupby("forecast_day")[["temp_mean", "humidity", "precipitation_probability", "wind_speed"]].mean().round(1).to_string())

# ─── Observations ───
# saved output/forecast_next3days_combo_analysis.png 403303
#               temp_mean  humidity  precipitation_probability  wind_speed
# forecast_day                                                            
# 1                  10.6      48.4                       34.1        11.3
# 2                  10.4      49.4                       34.0        11.1
# 3                  10.3      50.4                       33.9        10.9
# [save_plot] ✅ Plot saved → D:\Study\大三\申威高级语言编译与程序设计\GIS\GeoVela\Data\Weather7Days_20261105\assets\plots\plot_1793893783687.png
