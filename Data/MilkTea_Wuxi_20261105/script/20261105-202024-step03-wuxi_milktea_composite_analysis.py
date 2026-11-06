# ─── OpenGIS Agent · run 58522149 · step 3 · wuxi_milktea_composite_analysis ───
# Timestamp : 2026-11-05T20:20:24
# Semantic : wuxi_milktea_composite_analysis
# Metadata : 20261105-202024-step03-wuxi_milktea_composite_analysis.metadata.json
# User query: 绘制对这些poi的一个组合分析图
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.gridspec import GridSpec
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
import geopandas as gpd
from shapely.geometry import Point
import os

cands = ['PingFang SC','STHeiti','Heiti SC','SimHei','Microsoft YaHei','Noto Sans CJK SC']
avail = set(f.name for f in fm.fontManager.ttflist)
plt.rcParams['font.sans-serif'] = [c for c in cands if c in avail] or ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['axes.edgecolor'] = '#888888'

df = pd.read_csv('data/wuxi_milktea_poi.csv', encoding='utf-8-sig')
df['price'] = pd.to_numeric(df['人均消费(元)'], errors='coerce')
df['rating'] = pd.to_numeric(df['评分'], errors='coerce')
df['brand'] = df['品牌'].fillna('其他/独立门店')
df['district'] = df['区县'].fillna('未知')
df['biz'] = df['商圈'].fillna('未知')
d = df.dropna(subset=['price']).copy()

edges = [0, 8, 12, 15, 18, 22, 30, 60, 1e9]
plabels = ['5-8元', '8-12元', '12-15元', '15-18元', '18-22元', '22-30元', '30-60元', '≥60元']
d['pcls'] = pd.cut(d['price'], bins=edges, labels=plabels, right=True)
warm = ['#fff7bc', '#fee391', '#fec44f', '#fe9929', '#ec7014', '#cc4c02', '#993404', '#662506']
cmap = LinearSegmentedColormap.from_list('warm', warm)

fig = plt.figure(figsize=(19, 15.5), facecolor='white')
gs = GridSpec(3, 3, figure=fig, hspace=0.42, wspace=0.28,
              left=0.055, right=0.975, top=0.905, bottom=0.055)

# 1 价格分布
ax = fig.add_subplot(gs[0, 0])
bins = np.arange(0, 65, 2)
ax.hist(d['price'].clip(upper=64), bins=bins, color='#e07b39', edgecolor='white', linewidth=0.7, alpha=0.9)
ax.axvline(d['price'].median(), color='#7a1f0f', ls='--', lw=1.8)
ax.text(d['price'].median() + 1, ax.get_ylim()[1] * 0.9, f'中位数 {d["price"].median():.0f} 元',
        color='#7a1f0f', fontsize=10)
ax.set_title('① 人均消费分布（≥64元已并入末段）', fontsize=13, fontweight='bold', loc='left')
ax.set_xlabel('人均消费（元）'); ax.set_ylabel('门店数')
ax.set_xlim(0, 65)
ax.grid(axis='y', alpha=0.25, ls=':')
ax.spines[['top', 'right']].set_visible(False)

# 2 价格分层构成
ax = fig.add_subplot(gs[0, 1])
cnt = d['pcls'].value_counts().reindex(plabels)
bars = ax.barh(range(len(cnt)), cnt.values, color=warm, edgecolor='#8c5a2b', linewidth=0.6)
ax.set_yticks(range(len(cnt))); ax.set_yticklabels(plabels)
ax.invert_yaxis()
for i, v in enumerate(cnt.values):
    ax.text(v + 6, i, f'{v} ({v / len(d) * 100:.1f}%)', va='center', fontsize=9.5, color='#333333')
ax.set_xlim(0, cnt.max() * 1.35)
ax.set_title('② 价格分层结构', fontsize=13, fontweight='bold', loc='left')
ax.set_xlabel('门店数')
ax.grid(axis='x', alpha=0.25, ls=':')
ax.spines[['top', 'right']].set_visible(False)

# 3 空间分布
ax = fig.add_subplot(gs[0, 2])
gdf = gpd.read_file('data/wuxi_districts.json')
gdf.plot(ax=ax, facecolor='#f5f2ec', edgecolor='#9c9c9c', linewidth=0.9)
for lab, col in zip(plabels, warm):
    sub = d[d['pcls'] == lab]
    ax.scatter(sub['经度(WGS84)'], sub['纬度(WGS84)'], s=9, c=col, alpha=0.85, linewidths=0, label=lab)
for _, r in gdf.iterrows():
    c = r.geometry.representative_point()
    ax.text(c.x, c.y, r['name'], fontsize=8, ha='center', color='#4a4a4a', alpha=0.75)
ax.set_title('③ 门店空间分布（按价格分层着色）', fontsize=13, fontweight='bold', loc='left')
ax.set_xlabel('经度'); ax.set_ylabel('纬度')
ax.set_aspect('equal', adjustable='datalim')
ax.legend(fontsize=7.5, loc='lower left', framealpha=0.85, markerscale=1.8, ncol=2, title='人均消费', title_fontsize=8)
ax.spines[['top', 'right']].set_visible(False)

# 4 Top10 品牌
ax = fig.add_subplot(gs[1, 0])
bc = d['brand'].value_counts().head(10)[::-1]
cols = ['#cc4c02' if b != '其他/独立门店' else '#bdbdbd' for b in bc.index]
ax.barh(bc.index, bc.values, color=cols, edgecolor='white', linewidth=0.6)
for i, v in enumerate(bc.values):
    ax.text(v + 4, i, str(v), va='center', fontsize=9.5)
ax.set_xlim(0, bc.max() * 1.15)
ax.set_title('④ 门店数 Top10 品牌', fontsize=13, fontweight='bold', loc='left')
ax.set_xlabel('门店数')
ax.tick_params(axis='y', labelsize=9.5)
ax.grid(axis='x', alpha=0.25, ls=':')
ax.spines[['top', 'right']].set_visible(False)

# 5 品牌价格箱线
ax = fig.add_subplot(gs[1, 1])
top8 = d['brand'].value_counts().head(8).index.tolist()
data = [d.loc[d['brand'] == b, 'price'].values for b in top8]
bp = ax.boxplot(data, vert=False, patch_artist=True, widths=0.6, showfliers=False,
                medianprops=dict(color='#3a1a08', lw=1.8))
for patch, col in zip(bp['boxes'], plt.cm.YlOrBr(np.linspace(0.35, 0.9, len(top8)))):
    patch.set_facecolor(col); patch.set_edgecolor('#7a5a3a'); patch.set_alpha(0.9)
ax.set_yticklabels([f'{b}\n(n={len(x)})' for b, x in zip(top8, data)], fontsize=9)
ax.invert_yaxis()
ax.set_title('⑤ 主要品牌价格区间对比', fontsize=13, fontweight='bold', loc='left')
ax.set_xlabel('人均消费（元）')
ax.grid(axis='x', alpha=0.25, ls=':')
ax.spines[['top', 'right']].set_visible(False)

# 6 区县门店数 + 均价
ax = fig.add_subplot(gs[1, 2])
g = d.groupby('district').agg(n=('price', 'size'), mp=('price', 'mean')).sort_values('n', ascending=False)
ax.bar(g.index, g['n'], color='#f0c27b', edgecolor='#b07a3a', linewidth=0.7, label='门店数')
ax.set_ylabel('门店数', color='#8a5a20')
ax.tick_params(axis='y', colors='#8a5a20')
for i, v in enumerate(g['n']):
    ax.text(i, v + 5, str(v), ha='center', fontsize=9, color='#8a5a20')
ax.set_ylim(0, g['n'].max() * 1.2)
ax2 = ax.twinx()
ax2.plot(g.index, g['mp'], marker='o', color='#b30000', lw=2, ms=6)
for i, v in enumerate(g['mp']):
    ax2.text(i, v + 0.6, f'{v:.1f}', ha='center', fontsize=8.5, color='#b30000')
ax2.set_ylabel('平均人均消费（元）', color='#b30000')
ax2.tick_params(axis='y', colors='#b30000')
ax2.set_ylim(0, g['mp'].max() * 1.6)
ax.set_title('⑥ 各区县门店数与平均价格', fontsize=13, fontweight='bold', loc='left')
ax.tick_params(axis='x', labelsize=9)
ax.spines[['top']].set_visible(False); ax2.spines[['top']].set_visible(False)

# 7 评分 vs 价格
ax = fig.add_subplot(gs[2, 0])
ax.scatter(d['price'], d['rating'], s=16, c='#e07b39', alpha=0.45, edgecolors='none')
x, y = d['price'].values, d['rating'].values
k, b0 = np.polyfit(x, y, 1)
r = np.corrcoef(x, y)[0, 1]
xs = np.linspace(x.min(), np.percentile(x, 99.5), 100)
ax.plot(xs, k * xs + b0, color='#7a1f0f', lw=2, label=f'线性拟合  r = {r:.3f}')
ax.set_xlim(0, np.percentile(d['price'], 99.5) * 1.05)
ax.set_title('⑦ 评分与人均消费关系', fontsize=13, fontweight='bold', loc='left')
ax.set_xlabel('人均消费（元）'); ax.set_ylabel('评分')
ax.legend(fontsize=9.5, loc='lower right')
ax.grid(alpha=0.2, ls=':')
ax.spines[['top', 'right']].set_visible(False)

# 8 商圈 Top10
ax = fig.add_subplot(gs[2, 1])
bz = d[d['biz'] != '未知']['biz'].value_counts().head(10)[::-1]
ax.barh(range(len(bz)), bz.values, color=plt.cm.YlOrBr(np.linspace(0.35, 0.9, len(bz))),
        edgecolor='#8c5a2b', linewidth=0.6)
ax.set_yticks(range(len(bz))); ax.set_yticklabels(bz.index, fontsize=9.5)
for i, v in enumerate(bz.values):
    ax.text(v + 2, i, str(v), va='center', fontsize=9.5)
ax.set_xlim(0, bz.max() * 1.18)
ax.set_title('⑧ 门店数 Top10 商圈', fontsize=13, fontweight='bold', loc='left')
ax.set_xlabel('门店数')
ax.grid(axis='x', alpha=0.25, ls=':')
ax.spines[['top', 'right']].set_visible(False)

# 9 品牌 门店数-均价 气泡
ax = fig.add_subplot(gs[2, 2])
bg = d.groupby('brand').agg(n=('price', 'size'), mp=('price', 'mean'), mr=('rating', 'mean'))
bg = bg[bg['n'] >= 20]
ax.scatter(bg['n'], bg['mp'], s=(bg['mr'] - 3.4) * 900 + 60,
           c=bg['mp'], cmap='YlOrBr', edgecolor='#7a5a3a', linewidth=0.9, alpha=0.85)
for b, rrow in bg.iterrows():
    ax.annotate(b, (rrow['n'], rrow['mp']), fontsize=8.5, xytext=(5, 5), textcoords='offset points')
ax.set_title('⑨ 品牌规模-均价-评分（气泡=平均评分，≥20店）', fontsize=12.5, fontweight='bold', loc='left')
ax.set_xlabel('门店数'); ax.set_ylabel('平均人均消费（元）')
ax.grid(alpha=0.2, ls=':')
ax.spines[['top', 'right']].set_visible(False)

fig.suptitle('无锡市奶茶门店 POI 组合分析（n = 1,654，有效价格样本 1,571）',
             fontsize=20, fontweight='bold', y=0.962)
fig.text(0.055, 0.018, '数据来源：高德地图 POI（GCJ-02 已转 WGS84），采集日期 2026-11-05',
         fontsize=9.5, color='#666666')

os.makedirs('figures', exist_ok=True)
out = 'figures/wuxi_milktea_composite_analysis.png'
fig.savefig(out, dpi=170, bbox_inches='tight', facecolor='white')
print('saved', out)

summary = {
    'n_total': int(len(df)), 'n_price': int(len(d)),
    'price_median': float(d['price'].median()), 'price_mean': round(float(d['price'].mean()), 2),
    'rating_mean': round(float(d['rating'].mean()), 3),
    'corr_price_rating': round(float(r), 3),
    'top_brand': d['brand'].value_counts().head(3).to_dict(),
    'top_district': g['n'].head(3).to_dict(),
}
print(summary)

# ─── Observations ───
# saved figures/wuxi_milktea_composite_analysis.png
# {'n_total': 1654, 'n_price': 1571, 'price_median': 15.0, 'price_mean': 15.8, 'rating_mean': 4.006, 'corr_price_rating': 0.026, 'top_brand': {'其他/独立门店': 454, '蜜雪冰城': 289, '古茗': 138}, 'top_district': {'江阴市': 294, '梁溪区': 236, '宜兴市': 228}}
# [save_plot] ✅ Plot saved → D:\Study\大三\申威高级语言编译与程序设计\GIS\GeoVela\Data\MilkTea_Wuxi_20261105\assets\plots\plot_1793881223369.png
