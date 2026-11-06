# ─── OpenGIS Agent · run 1f747b07 · step 3 · accessibility_charts_fig1 ───
# Timestamp : 2026-11-05T23:15:19
# Semantic : accessibility_charts_fig1
# Metadata : 20261105-231519-step03-accessibility_charts_fig1.metadata.json
# User query: 绘制可达性分析图表，并对poi进行分级
import pandas as pd, numpy as np, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
_c=['PingFang SC','STHeiti','Heiti SC','SimHei','Microsoft YaHei','Noto Sans CJK SC']
_a=set(f.name for f in fm.fontManager.ttflist)
plt.rcParams['font.sans-serif']=[x for x in _c if x in _a] or ['DejaVu Sans']
plt.rcParams['axes.unicode_minus']=False
os.makedirs('output/figures', exist_ok=True)

df = pd.read_csv('data/processed/accessibility_results.csv')
gg = pd.read_csv('output/poi_accessibility_grades.csv')
short = lambda s: s.replace('江南大学蠡湖校区','').replace('公寓','')

# --- 图1：宿舍可达性水平 ---
d = df.groupby('dorm').agg(mean_t=('total_min','mean'), min_t=('total_min','min'),
                           n30=('total_min',lambda s:(s<=30).sum()),
                           n45=('total_min',lambda s:(s<=45).sum()),
                           n60=('total_min',lambda s:(s<=60).sum())).reset_index()
d['w1']=df.groupby('dorm').walk_to_station_min.mean().values
d['w2']=df.groupby('dorm').ride_min.mean().values
d['w3']=df.groupby('dorm').walk_to_poi_min.mean().values
d['lab']=d.dorm.map(short)
d=d.sort_values('mean_t')

fig,axes=plt.subplots(1,2,figsize=(15,6))
ax=axes[0]
ax.barh(d.lab,d.mean_t,color='#4C78A8',label='平均全程时间')
ax.barh(d.lab,d.min_t,color='#F58518',height=0.45,label='最短全程时间')
ax.axvline(45,ls='--',c='crimson',lw=1.2); ax.text(45.6,0.2,'45 min',color='crimson',fontsize=9)
for y,(m,t) in enumerate(zip(d.mean_t,d.min_t)):
    ax.text(m+1,y,f'{m:.1f}',va='center',fontsize=8)
ax.set_xlabel('时间 (分钟)'); ax.set_title('各宿舍→奶茶店全程时间（平均/最短）',fontsize=13)
ax.legend(fontsize=9); ax.grid(axis='x',alpha=.3)

ax=axes[1]
y=np.arange(len(d))
ax.barh(y,d.n60,color='#C9D9E8',label='≤60 min')
ax.barh(y,d.n45,color='#7BA7CB',label='≤45 min')
ax.barh(y,d.n30,color='#2F5D8A',label='≤30 min')
ax.set_yticks(y); ax.set_yticklabels(d.lab,fontsize=9)
for i,(a_,b_,c_) in enumerate(zip(d.n30,d.n45,d.n60)):
    ax.text(c_+2,i,f'{c_}/{b_}/{a_}',va='center',fontsize=8,color='#333')
ax.set_xlabel('可达奶茶店数量 (家 / 共275家)'); ax.set_title('不同时间阈值下可达奶茶店数量',fontsize=13)
ax.legend(fontsize=9); ax.grid(axis='x',alpha=.3)
plt.tight_layout()
fig.savefig('output/figures/fig1_dorm_accessibility.png',dpi=160,bbox_inches='tight')
try:
    save_plot(fig,'fig1_dorm_accessibility.png')
except Exception as e:
    print('save_plot skip',e)
plt.close(fig)
print(os.listdir('output/figures'))

# ─── Observations ───
# [save_plot] ✅ Plot saved → D:\Study\大三\申威高级语言编译与程序设计\GIS\GeoVela\Data\Dorm_MilkTea_Metro_Accessibility_20261105\assets\plots\fig1_dorm_accessibility.png.png
# ['fig1_dorm_accessibility.png']
