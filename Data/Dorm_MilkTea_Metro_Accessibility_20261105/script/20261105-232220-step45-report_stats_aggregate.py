# ─── OpenGIS Agent · run d2fe2b18 · step 45 · report_stats_aggregate ───
# Timestamp : 2026-11-05T23:22:20
# Semantic : report_stats_aggregate
# Metadata : 20261105-232220-step45-report_stats_aggregate.metadata.json
# User query: 基于以上workflow做分析报告
import pandas as pd, numpy as np
d=pd.read_csv('output/dorm_accessibility_summary.csv')
p=pd.read_csv('output/poi_accessibility_grades.csv')
r=pd.read_csv('data/processed/accessibility_results.csv')

print('DORM level dist:'); print(d['level'].value_counts().to_string())
print('best_near min_min:', d.min_min.min(), 'worst min_min:', d.min_min.max(), 'mean of min_min:', round(d.min_min.mean(),2))
print('mean_min range:', d.mean_min.min(), d.mean_min.max(), round(d.mean_min.mean(),2))
print('avg n30/n45/n60:', [round(d[c].mean(),1) for c in ['n30','n45','n60']])
print('n45 range', d.n45.min(), d.n45.max())
print('worst dorm rows:'); print(d.nlargest(3,'mean_min')[['dorm','mean_min','min_min','n45','level']].to_string(index=False))
print('best dorm rows:'); print(d.nsmallest(3,'mean_min')[['dorm','mean_min','min_min','n45','n60','level']].to_string(index=False))

print('\nTIME COMPOSITION (all pairs):')
comp=r[['walk_to_station_min','ride_min','walk_to_poi_min','total_min']].describe().loc[['mean','50%','min','max']].round(1)
print(comp.to_string())
s=r[['walk_to_station_min','ride_min','walk_to_poi_min']].sum()
tot=s.sum()
print('share %:', {k: round(v/tot*100,1) for k,v in s.items()})

print('\nPOI grades:')
g=p.groupby(['grade','grade_num']).agg(n=('poi_id','count'),mean_min=('mean_total','mean'),min_min=('min_total','min'),maxn=('max_total','max')).round(1)
print(g.to_string())
print('share within60 (n60>=n_dorm*0.5?) naive mean n60:', round(p.n60.mean(),1))
print('total POI:', len(p), 'poi with any dorm <=45:', (p.n45>0).sum(), '<=60:', (p.n60>0).sum())

print('\nTOP brands by count (>=5):')
b=p.groupby('brand').agg(n=('poi_id','count'),mean=('mean_total','mean')).query('n>=5').sort_values('n',ascending=False).round(1)
print(b.to_string())

print('\nSTATION PAIRS (top 8 by dorm-poi fastest counts):')
fast=r.loc[r.groupby(['dorm','poi_id'])['total_min'].idxmin()]
print(fast.groupby(['board_station','alight_station']).size().sort_values(ascending=False).head(8).to_string())
print('\nboard station usage share S023:', round((fast.board_station=='S023').mean()*100,1),'%')
print('alight top:'); print(fast.alight_station.value_counts().head(6).to_string())
print('\nride time mean by alight (top6):')
print(fast.groupby('alight_station')['ride_min'].mean().sort_index().head(6).round(1).to_string())
print('\ndistrict dist of POI:'); print(p.district.value_counts().to_string())
print('\nrating/price:', p.rating.mean().round(2), p.price_cny.mean().round(1))

# ─── Observations ───
# DORM level dist:
# level
# 较差     5
# 非常好    4
# 较好     4
# 很差     4
# 一般     3
# best_near min_min: 16.6 worst min_min: 29.6 mean of min_min: 23.92
# mean_min range: 52.3 65.7 59.85
# avg n30/n45/n60: [np.float64(16.0), np.float64(75.4), np.float64(145.6)]
# n45 range 42 108
# worst dorm rows:
#         dorm  mean_min  min_min  n45 level
# 江南大学蠡湖校区桂园公寓      65.7     29.6   42    很差
# 江南大学蠡湖校区桃园公寓      65.5     29.4   42    很差
# 江南大学蠡湖校区橙园公寓      65.5     29.4   42    很差
# best dorm rows:
#         dorm  mean_min  min_min  n45  n60 level
# 江南大学蠡湖校区瀚苑公寓      52.3     16.6  108  199   非常好
#        留学生公寓      52.8     17.1  106  193   非常好
# 江南大学蠡湖校区浩苑公寓      53.8     17.7  105  183   非常好
# 
# TIME COMPOSITION (all pairs):
#       walk_to_station_min  ride_min  walk_to_poi_min  total_min
# mean                 17.6      15.7             22.5       59.9
# 50%                  17.3      19.3             19.1       58.8
# min                   9.0       0.0              0.0       16.6
# max                  24.1      42.5             94.1      143.4
# share %: {'walk_to_station_min': np.float64(31.6), 'ride_min': np.float64(28.2), 'walk_to_poi_min': np.float64(40.2)}
# 
# POI grades:
#                   n  mean_min  min_min   maxn
# grade grade_num                              
# Ⅰ级 极优 1          40      31.1     16.6   44.3
# Ⅱ级 优  2          73      45.1     29.0   58.8
# Ⅲ级 良  3          98      62.7     46.7   75.3
# Ⅳ级 一般 4          50      80.5     64.6  108.5
# Ⅴ级 较差 5          14     125.3     97.4  143.4
# share within60 (n60>=n_dorm*0.5?) naive mean n60: 10.6
# total POI: 275 poi with any dorm <=45: 108 <=60: 199
# 
# TOP brands by count (>=5):
#            n  mean
# brand             
# 其他/独立门店  100  55.6
# 蜜雪冰城      43  65.1
# 一点点       21  63.9
# CoCo都可    20  59.6
# 茶百道       20  61.9
# 古茗        10  68.4
# 霸王茶姬      10  52.0
# 喜茶        10  58.4
# 沪上阿姨       9  64.5
# 茶颜悦色       8  52.8
# 
# STATION PAIRS (top 8 by dorm-poi fastest counts):
# board_station  alight_station
# S023           S079              572
#                S013              336
#                S014              312
# S024           S079              308
# S023           S021              286
#                S022              260
#                S023              247
#                S031              234
# 
# board station usage share S023: 62.9 %
# alight top:
# alight_station
# S079    880
# S013    560
# S014    520
# S021    440
# S022    400
# S023    380
# 
# ride time mean by alight (top6):
# alight_station
# S013    21.6
# S014    20.1
# S015    18.1
# S016    16.0
# S017    13.4
# S018    11.3
# 
# district dist of POI:
# district
# 滨湖区    181
# 梁溪区     70
# 新吴区     24
# 
# rating/price: 4.0 16.1
