# ─── OpenGIS Agent · run 1f747b07 · step 4 · accessibility_charts_fig2_fig3 ───
# Timestamp : 2026-11-05T23:15:29
# Semantic : accessibility_charts_fig2_fig3
# Metadata : 20261105-231529-step04-accessibility_charts_fig2_fig3.metadata.json
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
os.makedirs('output/figures',exist_ok=True)
df=pd.read_csv('data/processed/accessibility_results.csv')
gg=pd.read_csv('output/poi_accessibility_grades.csv')
short=lambda s:s.replace('江南大学蠡湖校区','').replace('公寓','')

# ---- 图2：出行时间构成 ----
comp=df.groupby('dorm')[['walk_to_station_min','ride_min','walk_to_poi_min']].mean()
comp['total']=comp.sum(axis=1); comp=comp.sort_values('total'); comp.index=[short(i) for i in comp.index]
fig,axes=plt.subplots(1,2,figsize=(15,6))
ax=axes[0]; y=np.arange(len(comp))
cols=['#4C78A8','#F58518','#54A24B']; labs=['宿舍→地铁站步行','地铁乘车','地铁站→奶茶店步行']
left=np.zeros(len(comp))
for c,l,cl in zip(['walk_to_station_min','ride_min','walk_to_poi_min'],labs,cols):
    ax.barh(y,comp[c],left=left,color=cl,label=l); left+=comp[c].values
for i,t in enumerate(comp.total): ax.text(t+0.6,i,f'{t:.1f}',va='center',fontsize=8)
ax.set_yticks(y); ax.set_yticklabels(comp.index,fontsize=9)
ax.set_xlabel('平均时间 (分钟)'); ax.set_title('平均出行时间构成（按宿舍）',fontsize=13)
ax.legend(fontsize=9,loc='lower right'); ax.grid(axis='x',alpha=.3)

# 半径衰减曲线
ax=axes[1]
th=np.arange(15,145,5)
share=[]
for d_,sub in df.groupby('dorm'):
    s=sub.total_min.values; share.append([(s<=t).mean()*100 for t in th])
share=np.array(share)
ax.fill_between(th,share.min(0),share.max(0),color='#9ECAE1',alpha=.5,label='20所宿舍区间')
ax.plot(th,share.mean(0),color='#1F4E79',lw=2.2,label='平均可达比例')
for t in (30,45,60,90):
    ax.axvline(t,ls=':',c='grey',lw=1)
    ax.text(t+0.7,share.mean(0)[th.tolist().index(t) if t in th.tolist() else 0]+2,f'{t}min',fontsize=8,color='grey')
ax.set_xlabel('时间阈值 (分钟)'); ax.set_ylabel('可达奶茶店比例 (%)')
ax.set_title('可达奶茶店比例随时间的衰减曲线',fontsize=13); ax.legend(fontsize=9); ax.grid(alpha=.3)
plt.tight_layout(); fig.savefig('output/figures/fig2_time_composition.png',dpi=160,bbox_inches='tight')
try: save_plot(fig,'fig2_time_composition.png')
except Exception as e: print('skip',e)
plt.close(fig)

# ---- 图3：POI 分级 ----
order=['Ⅰ级 极优','Ⅱ级 优','Ⅲ级 良','Ⅳ级 一般','Ⅴ级 较差']
pal=['#1A9850','#91CF60','#FEE08B','#FC8D59','#D73027']
cnt=gg.grade.value_counts().reindex(order)
fig,axes=plt.subplots(1,2,figsize=(15,6))
ax=axes[0]
bars=ax.bar(range(5),cnt.values,color=pal,edgecolor='white')
for i,v in enumerate(cnt.values):
    ax.text(i,v+2,f'{v}家\n({v/len(gg)*100:.1f}%)',ha='center',fontsize=10)
ax.set_xticks(range(5)); ax.set_xticklabels([o.replace(' ','\n') for o in order],fontsize=10)
ax.set_ylabel('奶茶店数量 (家)'); ax.set_title('275家奶茶店可达性等级分布（Jenks自然断点）',fontsize=13)
ax.grid(axis='y',alpha=.3); ax.set_ylim(0,cnt.max()*1.25)

ax=axes[1]
data=[gg.loc[gg.grade==o,'mean_total'].values for o in order]
bp=ax.boxplot(data,patch_artist=True,widths=.6,medianprops=dict(color='black'))
for p,c in zip(bp['boxes'],pal): p.set_facecolor(c); p.set_alpha(.85)
for i,v in enumerate(data,1):
    x=np.random.default_rng(i).normal(i,.055,len(v))
    ax.scatter(x,v,s=10,color='#333',alpha=.5)
ax.set_xticklabels([o.replace(' ','\n') for o in order],fontsize=10)
ax.set_ylabel('20所宿舍平均全程时间 (分钟)'); ax.set_title('各等级平均时间分布',fontsize=13)
for b in (38.10,53.91,71.59,102.88): ax.axhline(b,ls=':',c='grey',lw=.9)
ax.grid(axis='y',alpha=.3)
plt.tight_layout(); fig.savefig('output/figures/fig3_poi_grading.png',dpi=160,bbox_inches='tight')
try: save_plot(fig,'fig3_poi_grading.png')
except Exception as e: print('skip',e)
plt.close(fig)
print('ok')

# ─── Observations ───
# [save_plot] ✅ Plot saved → D:\Study\大三\申威高级语言编译与程序设计\GIS\GeoVela\Data\Dorm_MilkTea_Metro_Accessibility_20261105\assets\plots\fig2_time_composition.png.png
# [save_plot] ✅ Plot saved → D:\Study\大三\申威高级语言编译与程序设计\GIS\GeoVela\Data\Dorm_MilkTea_Metro_Accessibility_20261105\assets\plots\fig3_poi_grading.png.png
# ok
