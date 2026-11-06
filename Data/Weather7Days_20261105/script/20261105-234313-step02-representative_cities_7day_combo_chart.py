# ─── OpenGIS Agent · run 39db82f7 · step 2 · representative_cities_7day_combo_chart ───
# Timestamp : 2026-11-05T23:43:13
# Semantic : representative_cities_7day_combo_chart
# Metadata : 20261105-234313-step02-representative_cities_7day_combo_chart.metadata.json
# User query: 绘制代表性城市七天天气的组合分析图
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from matplotlib.gridspec import GridSpec

cands = ["PingFang SC", "STHeiti", "Heiti SC", "SimHei", "Microsoft YaHei", "Noto Sans CJK SC"]
avail = set(f.name for f in fm.fontManager.ttflist)
plt.rcParams["font.sans-serif"] = [c for c in cands if c in avail] or ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_csv("data/china_weather_last7days.csv", encoding="utf-8-sig")
df["日期"] = pd.to_datetime(df["日期"])
dates = np.array(sorted(df["日期"].unique()))
x = np.arange(len(dates))
xlab = [pd.Timestamp(d).strftime("%m/%d") for d in dates]

cities = ["漠河", "哈尔滨", "北京", "乌鲁木齐", "西安", "拉萨",
          "上海", "武汉", "成都", "昆明", "广州", "三亚"]
missing = [c for c in cities if c not in set(df["城市"])]
print("missing:", missing)

PM = df["降水量(mm)"].max()
PM_TOP = max(PM * 1.35, 6)


def wx_color(s):
    s = str(s)
    if "雪" in s:
        return "#C7D2FE"
    if "雷" in s:
        return "#A78BFA"
    if "雨" in s:
        return "#7DD3FC"
    if s.startswith("晴"):
        return "#FCD34D"
    if "云" in s:
        return "#CBD5E1"
    if "阴" in s:
        return "#94A3B8"
    if "雾" in s or "霾" in s:
        return "#D6D3D1"
    return "#E5E7EB"


fig = plt.figure(figsize=(19, 13.2), facecolor="white")
gs = GridSpec(4, 4, figure=fig, height_ratios=[1, 1, 1, 0.92],
              hspace=0.52, wspace=0.20, left=0.055, right=0.965, top=0.90, bottom=0.075)

for i, city in enumerate(cities):
    r, c = divmod(i, 4)
    ax = fig.add_subplot(gs[r, c])
    d = df[df["城市"] == city].sort_values("日期")
    tmax, tmin, tmean = d["最高气温(℃)"].values, d["最低气温(℃)"].values, d["平均气温(℃)"].values
    prec, wind, sun = d["降水量(mm)"].values, d["最大风速(km/h)"].values, d["日照时长(h)"].values

    axp = ax.twinx()
    axp.bar(x, prec, width=0.72, color="#7DD3FC", alpha=0.55, edgecolor="#38BDF8",
            linewidth=0.6, zorder=1)
    axp.set_ylim(PM_TOP, 0)
    axp.set_yticks([])
    for sp in axp.spines.values():
        sp.set_visible(False)

    ax.fill_between(x, tmin, tmax, color="#FCA5A5", alpha=0.45, zorder=2,
                    label="最高/最低气温")
    ax.plot(x, tmean, color="#DC2626", lw=2.2, marker="o", ms=4.2, zorder=4, label="平均气温")
    ax.plot(x, tmax, color="#EF4444", lw=0.8, alpha=0.8, zorder=3)
    ax.plot(x, tmin, color="#F87171", lw=0.8, alpha=0.8, zorder=3)

    axw = ax.twinx()
    axw.plot(x, wind, color="#64748B", lw=1.2, ls=(0, (2.5, 2)), marker="v", ms=3.6,
             alpha=0.85, zorder=5)
    axw.set_ylim(0, max(df["最大风速(km/h)"].max() * 1.6, 10))
    axw.set_yticks([])
    for sp in axw.spines.values():
        sp.set_visible(False)

    lo, hi = min(tmin.min(), tmean.min()), max(tmax.max(), tmean.max())
    pad = (hi - lo) * 0.22 + 1.5
    ax.set_ylim(lo - pad, hi + pad)
    ax.set_xlim(-0.62, len(dates) - 0.38)

    strip_y = ax.get_ylim()[0]
    for k, wxs in enumerate(d["天气现象"].values):
        ax.axvspan(k - 0.5, k + 0.5, ymin=0, ymax=0.045, color=wx_color(wxs),
                   alpha=0.95, zorder=1, lw=0)

    ax.set_xticks(x)
    ax.set_xticklabels(xlab, fontsize=7.2, color="#475569")
    ax.tick_params(axis="y", labelsize=7.2, colors="#334155", length=2.5)
    ax.grid(axis="y", color="#E2E8F0", lw=0.6, zorder=0)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]:
        ax.spines[s].set_color("#94A3B8")
        ax.spines[s].set_linewidth(0.7)
    prov = d["省/区/市"].iloc[0]
    ax.set_title(f"{city}", fontsize=11.5, fontweight="bold", color="#0F172A", pad=12, loc="left")
    ax.text(0.0, 1.015, f"{prov}｜累计降水 {prec.sum():.1f} mm｜均温 {tmean.mean():.1f} ℃｜"
                        f"最大风 {wind.max():.0f} km/h｜均日照 {sun.mean():.1f} h",
            transform=ax.transAxes, fontsize=6.9, color="#64748B", va="bottom")
    ax.text(-0.055, 0.5, "气温 ℃", transform=ax.transAxes, rotation=90,
            fontsize=6.8, color="#B91C1C", va="center", ha="center")
    if c == 3:
        axw.set_yticks([0, 20, 40, 60])
        axw.tick_params(axis="y", labelsize=6.2, colors="#64748B", length=2)
        axw.spines["right"].set_visible(True)
        axw.spines["right"].set_color("#CBD5E1")
        axw.spines["right"].set_linewidth(0.7)

axs = fig.add_subplot(gs[3, :])
agg = (df[df["城市"].isin(cities)].groupby("城市")
       .agg(p=("降水量(mm)", "sum"), t=("平均气温(℃)", "mean"),
            w=("最大风速(km/h)", "mean"), s=("日照时长(h)", "mean"))
       .reindex(cities))
xb = np.arange(len(cities))
bars = axs.bar(xb, agg["p"], width=0.55, color="#60A5FA", alpha=0.85,
               edgecolor="#2563EB", linewidth=0.7, label="7日累计降水量 (mm)")
for xi, v in zip(xb, agg["p"]):
    axs.text(xi, v + 0.6, f"{v:.1f}", ha="center", va="bottom", fontsize=7.5, color="#1E40AF")
axs.set_ylabel("累计降水量 (mm)", fontsize=8.5, color="#1E40AF")
axs.set_ylim(0, agg["p"].max() * 1.35 + 1)
axs.set_xticks(xb)
axs.set_xticklabels(cities, fontsize=9)
axs.tick_params(labelsize=7.8, colors="#334155")
axs.grid(axis="y", color="#E2E8F0", lw=0.6)
for s in ["top", "right"]:
    axs.spines[s].set_visible(False)

ax2 = axs.twinx()
ax2.plot(xb, agg["t"], color="#DC2626", lw=2.2, marker="o", ms=6,
         label="7日平均气温 (℃)")
for xi, v in zip(xb, agg["t"]):
    ax2.annotate(f"{v:.1f}", (xi, v), textcoords="offset points", xytext=(0, 9),
                 ha="center", fontsize=7.5, color="#B91C1C")
ax2.set_ylabel("7日平均气温 (℃)", fontsize=8.5, color="#B91C1C")
lo, hi = agg["t"].min(), agg["t"].max()
ax2.set_ylim(lo - (hi - lo) * 0.55 - 1, hi + (hi - lo) * 0.55 + 1)
ax2.tick_params(labelsize=7.8, colors="#B91C1C")
for s in ["top", "left"]:
    ax2.spines[s].set_visible(False)
axs.set_title("综合对比：代表性城市 7 日累计降水与平均气温", fontsize=11.5,
              fontweight="bold", color="#0F172A", loc="left", pad=10)

fig.suptitle("中国代表性城市 2026-10-30 至 2026-11-05 七日天气组合分析",
             fontsize=18, fontweight="bold", color="#0F172A", y=0.965)
fig.text(0.5, 0.925,
         "每个城市面板：浅红带 = 日最高/最低气温区间，红线 = 日平均气温，自上而下的浅蓝柱 = 日降水量，"
         "灰色虚线 = 日最大风速，底部色条 = 当日天气现象",
         ha="center", fontsize=9.2, color="#475569")

legend_items = [
    Line2D([0], [0], color="#DC2626", lw=2.2, marker="o", ms=4, label="日平均气温 (℃)"),
    Patch(facecolor="#FCA5A5", alpha=0.6, label="日最高/最低气温区间"),
    Patch(facecolor="#7DD3FC", alpha=0.7, edgecolor="#38BDF8", label="日降水量 (mm，自上而下)"),
    Line2D([0], [0], color="#64748B", lw=1.2, ls=(0, (2.5, 2)), marker="v", ms=4, label="日最大风速 (km/h)"),
    Patch(facecolor="#FCD34D", label="晴"),
    Patch(facecolor="#CBD5E1", label="多云"),
    Patch(facecolor="#94A3B8", label="阴"),
    Patch(facecolor="#7DD3FC", label="雨"),
    Patch(facecolor="#C7D2FE", label="雪"),
]
fig.legend(handles=legend_items, loc="lower center", ncol=9, frameon=False,
           fontsize=8.6, bbox_to_anchor=(0.5, 0.012))

out = "output/representative_cities_7day_combo.png"
import os
os.makedirs("output", exist_ok=True)
fig.savefig(out, dpi=150, facecolor="white", bbox_inches="tight")
print("saved", out, os.path.getsize(out))
print(agg.round(1).to_string())

# ─── Observations ───
# missing: []
# saved output/representative_cities_7day_combo.png 573330
#          p     t     w     s
# 城市                          
# 漠河     1.5 -17.3   8.5   7.8
# 哈尔滨    2.0  -1.8  17.0   6.1
# 北京     0.0  10.1  12.1   8.7
# 乌鲁木齐   0.0   5.2  12.0   9.9
# 西安     9.7  11.7  11.2   6.7
# 拉萨     0.6   9.4  11.8  10.8
# 上海    36.1  17.4  13.6   6.9
# 武汉    35.4  16.8  10.7   4.9
# 成都     0.3  16.4   8.1   4.7
# 昆明     8.0  19.1  14.5   9.7
# 广州    11.8  26.8  10.8   9.2
# 三亚    38.9  26.7  17.4   9.1
# [save_plot] ✅ Plot saved → D:\Study\大三\申威高级语言编译与程序设计\GIS\GeoVela\Data\Weather7Days_20261105\assets\plots\plot_1793893391666.png
