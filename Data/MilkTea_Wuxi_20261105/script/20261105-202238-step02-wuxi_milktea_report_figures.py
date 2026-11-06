# ─── OpenGIS Agent · run a4753f1c · step 2 · wuxi_milktea_report_figures ───
# Timestamp : 2026-11-05T20:22:38
# Semantic : wuxi_milktea_report_figures
# Metadata : 20261105-202238-step02-wuxi_milktea_report_figures.metadata.json
# User query: 使用上述workflow撰写分析报告
import pandas as pd, numpy as np, json, os, shutil
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

cands = ['PingFang SC','STHeiti','Heiti SC','SimHei','Microsoft YaHei','Noto Sans CJK SC']
avail = set(f.name for f in fm.fontManager.ttflist)
plt.rcParams['font.sans-serif'] = [c for c in cands if c in avail] or ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

os.makedirs('output/report/figures', exist_ok=True)
shutil.copy('figures/wuxi_milktea_composite_analysis.png', 'output/report/figures/fig01_composite_analysis.png')

df = pd.read_csv('data/wuxi_milktea_poi.csv', encoding='utf-8-sig')
df['price'] = pd.to_numeric(df['人均消费(元)'], errors='coerce')
df['district'] = df['区县'].fillna('未知')
df['brand'] = df['品牌'].fillna('其他/独立门店')
d = df.dropna(subset=['price']).copy()

edges = [0,8,12,15,18,22,30,60,1e9]
labels = ['5-8元','8-12元','12-15元','15-18元','18-22元','22-30元','30-60元','≥60元']
warm = ['#fff7bc','#fee391','#fec44f','#fe9929','#ec7014','#cc4c02','#993404','#662506']
d['pcls'] = pd.cut(d['price'], bins=edges, labels=labels, right=True)

order = d['district'].value_counts().index.tolist()
ct = pd.crosstab(d['district'], d['pcls'], normalize='index').reindex(index=order, columns=labels).fillna(0)*100

fig, axes = plt.subplots(1, 2, figsize=(15.5, 5.6), gridspec_kw={'width_ratios':[1.5,1]})
ax = axes[0]
left = np.zeros(len(ct))
for i, lab in enumerate(labels):
    ax.barh(range(len(ct)), ct[lab].values, left=left, color=warm[i], edgecolor='white', linewidth=0.7, label=lab)
    for j, v in enumerate(ct[lab].values):
        if v >= 6:
            ax.text(left[j]+v/2, j, f'{v:.0f}', ha='center', va='center', fontsize=8, color='#3a2a1a')
    left += ct[lab].values
ax.set_yticks(range(len(ct))); ax.set_yticklabels(ct.index, fontsize=10)
ax.invert_yaxis(); ax.set_xlim(0,100); ax.set_xlabel('价格分层占比（%）')
ax.set_title('各区县价格分层构成', fontsize=13, fontweight='bold', loc='left')
ax.legend(ncol=4, fontsize=8, loc='lower center', bbox_to_anchor=(0.5,-0.32), frameon=False)
ax.spines[['top','right']].set_visible(False)

ax = axes[1]
bg = d.groupby('brand')['price'].agg(['size','median','mean'])
bg = bg[bg['size']>=20].sort_values('median')
colors = plt.cm.YlOrBr(np.linspace(0.3,0.92,len(bg)))
ax.scatter(bg['median'], range(len(bg)), s=bg['size']*2.2, c=colors, edgecolor='#7a5a3a', lw=0.9, alpha=0.9, zorder=3)
for i,(b,r) in enumerate(bg.iterrows()):
    ax.plot([r['mean'], r['median']], [i,i], color='#b0b0b0', lw=1.4, zorder=1)
ax.set_yticks(range(len(bg))); ax.set_yticklabels([f'{b} (n={int(r["size"])})' for b,r in bg.iterrows()], fontsize=9)
ax.set_xlabel('人均消费（元） ｜ 点=中位数，灰线端=均值')
ax.set_title('品牌价格梯度（≥20 店，气泡=门店数）', fontsize=13, fontweight='bold', loc='left')
ax.grid(axis='x', alpha=0.25, ls=':')
ax.spines[['top','right']].set_visible(False)

fig.tight_layout()
fig.savefig('output/report/figures/fig02_district_brand_price.png', dpi=170, bbox_inches='tight', facecolor='white')
print('ok', os.listdir('output/report/figures'))
print(ct.round(1).to_string())

# ─── Observations ───
# ok ['fig01_composite_analysis.png', 'fig02_district_brand_price.png']
# pcls      5-8元  8-12元  12-15元  15-18元  18-22元  22-30元  30-60元  ≥60元
# district                                                           
# 江阴市       17.7   10.5    33.3    21.8    13.3     2.4     0.7   0.3
# 梁溪区       15.7    8.1    25.0    16.1    23.3     7.6     2.5   1.7
# 宜兴市       10.5   13.6    39.0    14.9    17.1     3.5     0.9   0.4
# 新吴区       19.2   12.1    26.2    22.0    17.3     1.4     1.9   0.0
# 滨湖区       14.3    8.1    31.9    19.5    18.1     5.7     1.9   0.5
# 惠山区       16.9   17.4    30.8    16.4    15.9     1.5     0.5   0.5
# 锡山区       17.0   13.4    28.4    20.6    13.9     4.1     1.5   1.0
# [save_plot] ✅ Plot saved → D:\Study\大三\申威高级语言编译与程序设计\GIS\GeoVela\Data\MilkTea_Wuxi_20261105\assets\plots\plot_1793881358620.png
