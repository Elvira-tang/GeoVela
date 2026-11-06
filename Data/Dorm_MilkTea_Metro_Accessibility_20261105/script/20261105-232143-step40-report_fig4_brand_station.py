# ─── OpenGIS Agent · run d2fe2b18 · step 40 · report_fig4_brand_station ───
# Timestamp : 2026-11-05T23:21:43
# Semantic : report_fig4_brand_station
# Metadata : 20261105-232143-step40-report_fig4_brand_station.metadata.json
# User query: 基于以上workflow做分析报告
import pandas as pd, numpy as np, os, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
_c=['PingFang SC','STHeiti','Heiti SC','SimHei','Microsoft YaHei','Noto Sans CJK SC']
_a=set(f.name for f in fm.fontManager.ttflist)
plt.rcParams['font.sans-serif']=[x for x in _c if x in _a] or ['DejaVu Sans']
plt.rcParams['axes.unicode_minus']=False
os.makedirs('output/report/figures',exist_ok=True)

gg=pd.read_csv('output/poi_accessibility_grades.csv')
gg['brand']=gg['brand'].fillna('未标注')
order=['Ⅰ级 极优','Ⅱ级 优','Ⅲ级 良','Ⅳ级 一般','Ⅴ级 较差']
pal={'Ⅰ级 极优':'#1A9850','Ⅱ级 优':'#91CF60','Ⅲ级 良':'#FEE08B','Ⅳ级 一般':'#FC8D59','Ⅴ级 较差':'#D73027'}
b=gg.groupby('brand').agg(n=('mean_total','size'),mean_t=('mean_total','mean')).sort_values('mean_t')
b=b[b.n>=3]

fig,axes=plt.subplots(1,2,figsize=(15,6),gridspec_kw={'width_ratios':[1.25,1]})
ax=axes[0]
share=gg.groupby(['brand','grade']).size().unstack(fill_value=0).reindex(columns=order,fill_value=0)
share=share.loc[b.index]
share_pct=share.div(share.sum(1),axis=0)*100
left=np.zeros(len(share_pct))
for g in order:
    ax.barh(share_pct.index,share_pct[g],left=left,color=pal[g],label=g)
    left+=share_pct[g].values
for i,(idx,row) in enumerate(share.iterrows()):
    ax.text(101,i,f'均值 {b.loc[idx,"mean_t"]:.1f} min (n={int(b.loc[idx,"n"])})',va='center',fontsize=8)
ax.set_xlim(0,140); ax.set_xlabel('该品牌门店可达性等级构成 (%)')
ax.set_title('奶茶品牌 × 可达性等级构成（门店数≥3）',fontsize=13)
ax.legend(fontsize=8,loc='lower right',ncol=2); ax.grid(axis='x',alpha=.3)

ax=axes[1]
st=pd.read_csv('data/processed/accessibility_results.csv')
al=st.groupby('alight_station').size().sort_values(ascending=False).head(12)
ax.barh(range(len(al))[::-1],al.values,color='#4C78A8')
ax.set_yticks(range(len(al))[::-1]); ax.set_yticklabels(al.index,fontsize=9)
for i,v in zip(range(len(al))[::-1],al.values): ax.text(v+10,i,str(v),va='center',fontsize=8)
ax.set_xlabel('出现于 O-D 组合中的次数 (总 5500)')
ax.set_title('主要落客站点使用频次（前12）',fontsize=13); ax.grid(axis='x',alpha=.3)
plt.tight_layout(); fig.savefig('output/report/figures/fig4_brand_station.png',dpi=160,bbox_inches='tight')
try: save_plot(fig,'fig4_brand_station.png')
except Exception as e: print('skip',e)
plt.close(fig)

import shutil
for f in ['fig1_dorm_accessibility.png','fig2_time_composition.png','fig3_poi_grading.png']:
    shutil.copy(f'output/figures/{f}',f'output/report/figures/{f}')
print(sorted(os.listdir('output/report/figures')))

# ─── Observations ───
# [save_plot] ✅ Plot saved → D:\Study\大三\申威高级语言编译与程序设计\GIS\GeoVela\Data\Dorm_MilkTea_Metro_Accessibility_20261105\assets\plots\fig4_brand_station.png.png
# ['fig1_dorm_accessibility.png', 'fig2_time_composition.png', 'fig3_poi_grading.png', 'fig4_brand_station.png']
