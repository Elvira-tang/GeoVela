# ─── OpenGIS Agent · run a4753f1c · step 1 · wuxi_milktea_report_stats ───
# Timestamp : 2026-11-05T20:22:31
# Semantic : wuxi_milktea_report_stats
# Metadata : 20261105-202231-step01-wuxi_milktea_report_stats.metadata.json
# User query: 使用上述workflow撰写分析报告
import pandas as pd, numpy as np, json, os
import geopandas as gpd
from shapely.geometry import Point
from scipy.spatial import cKDTree

df = pd.read_csv('data/wuxi_milktea_poi.csv', encoding='utf-8-sig')
df['price'] = pd.to_numeric(df['人均消费(元)'], errors='coerce')
df['rating'] = pd.to_numeric(df['评分'], errors='coerce')
df['brand'] = df['品牌'].fillna('其他/独立门店')
df['district'] = df['区县'].fillna('未知')
d = df.dropna(subset=['price']).copy()

R = {}
R['n_total'] = int(len(df)); R['n_price'] = int(len(d))
R['price'] = {k: round(float(v), 2) for k, v in d['price'].describe().items()}
R['price_q'] = {str(q): round(float(d['price'].quantile(q)), 1) for q in [0.05,0.25,0.5,0.75,0.9,0.95,0.99]}
R['price_iqr'] = round(float(d['price'].quantile(.75)-d['price'].quantile(.25)),1)
R['n_rating'] = int(df['rating'].notna().sum())
R['rating'] = {k: round(float(v), 3) for k, v in df['rating'].describe().items()}

edges = [0,8,12,15,18,22,30,60,1e9]
plabels = ['5-8元','8-12元','12-15元','15-18元','18-22元','22-30元','30-60元','≥60元']
d['pcls'] = pd.cut(d['price'], bins=edges, labels=plabels, right=True)
R['pclass'] = {k: [int(v), round(v/len(d)*100, 1)] for k, v in d['pcls'].value_counts().reindex(plabels).items()}
R['share_le18'] = round(float((d['price']<=18).mean()*100),1)
R['share_ge22'] = round(float((d['price']>=22).mean()*100),1)

bg = d.groupby('brand').agg(n=('price','size'), mp=('price','mean'), med=('price','median'),
                            p90=('price', lambda s: s.quantile(.9)), mr=('rating','mean')).sort_values('n', ascending=False)
R['brands'] = {b: [int(r.n), round(r.mp,2), round(r.med,1), round(r.p90,1),
                   (round(r.mr,3) if pd.notna(r.mr) else None)] for b, r in bg.head(12).iterrows()}
R['brand_named_share'] = round(float((d['brand']!='其他/独立门店').mean()*100),1)

gd = d.groupby('district').agg(n=('price','size'), mp=('price','mean'), med=('price','median'),
                               hi=('price', lambda s: (s>=22).sum())).sort_values('n', ascending=False)
gd['hi_share'] = (gd['hi']/gd['n']*100).round(1)
R['districts'] = {i: [int(r.n), round(r.mp,2), round(r.med,1), int(r.hi), round(r.hi_share,1)] for i, r in gd.iterrows()}

biz = d[d['商圈'].notna() & (d['商圈'].astype(str).str.len()>0)]['商圈'].value_counts().head(10)
R['top_biz'] = biz.to_dict()
R['n_biz'] = int(d['商圈'].nunique())

x = d['经度(WGS84)'].values; y = d['纬度(WGS84)'].values
pts = np.c_[x, y]
R['centroid'] = [round(float(x.mean()),5), round(float(y.mean()),5)]
obs = cKDTree(pts).query(pts, k=2)[0][:,1].mean()
area_km2 = 4627.47
lam = len(pts)/area_km2
R['nn_ratio'] = round(float(obs/(0.5/np.sqrt(lam))),3)
R['nearest_mean_m'] = round(float(obs*111320*np.cos(np.radians(31.5))),0)

R['corr_price_rating'] = round(float(d[['price','rating']].dropna().corr().iloc[0,1]),3)

hours = df['营业时间'].astype(str)
R['n_hours_field'] = int((hours.str.len()>3).sum())
R['top_hours'] = hours[hours.str.len()>3].value_counts().head(5).to_dict()
R['n_phone'] = int(df['电话'].notna().sum())

gd2 = gpd.read_file('data/wuxi_districts.json')
R['district_names'] = gd2['name'].tolist()

os.makedirs('output/report/figures', exist_ok=True)
with open('output/report/stats.json','w',encoding='utf-8') as f:
    json.dump(R, f, ensure_ascii=False, indent=2)
print(json.dumps({k: R[k] for k in ['price','price_q','price_iqr','rating','share_le18','share_ge22','brand_named_share','nn_ratio','nearest_mean_m','n_biz','n_phone','corr_price_rating']}, ensure_ascii=False, indent=1))
print('brands', R['brands'])
print('districts', R['districts'])
print('biz', R['top_biz'])
print('hours', R['top_hours'])

# ─── Observations ───
# [auto-install] Auto-installed: scipy
# {
#  "price": {
#   "count": 1571.0,
#   "mean": 15.8,
#   "std": 13.87,
#   "min": 5.0,
#   "25%": 12.0,
#   "50%": 15.0,
#   "75%": 18.0,
#   "max": 430.0
#  },
#  "price_q": {
#   "0.05": 7.0,
#   "0.25": 12.0,
#   "0.5": 15.0,
#   "0.75": 18.0,
#   "0.9": 21.0,
#   "0.95": 24.0,
#   "0.99": 45.9
#  },
#  "price_iqr": 6.0,
#  "rating": {
#   "count": 1571.0,
#   "mean": 4.006,
#   "std": 0.302,
#   "min": 1.5,
#   "25%": 3.9,
#   "50%": 4.0,
#   "75%": 4.2,
#   "max": 4.7
#  },
#  "share_le18": 77.3,
#  "share_ge22": 8.3,
#  "brand_named_share": 71.1,
#  "nn_ratio": 0.002,
#  "nearest_mean_m": 138.0,
#  "n_biz": 122,
#  "n_phone": 1418,
#  "corr_price_rating": 0.026
# }
# brands {'其他/独立门店': [454, np.float64(20.39), np.float64(17.0), np.float64(26.0), np.float64(3.919)], '蜜雪冰城': [289, np.float64(7.71), np.float64(7.0), np.float64(10.0), np.float64(4.008)], '古茗': [138, np.float64(15.1), np.float64(15.0), np.float64(16.0), np.float64(4.197)], 'CoCo都可': [118, np.float64(13.53), np.float64(12.0), np.float64(16.0), np.float64(3.928)], '一点点': [107, np.float64(15.41), np.float64(15.0), np.float64(19.0), np.float64(4.154)], '茶百道': [99, np.float64(14.62), np.float64(14.0), np.float64(17.0), np.float64(3.969)], '霸王茶姬': [87, np.float64(20.02), np.float64(20.0), np.float64(20.0), np.float64(4.184)], '沪上阿姨': [74, np.float64(13.99), np.float64(14.0), np.float64(14.0), np.float64(3.895)], '喜茶': [47, np.float64(19.09), np.float64(19.0), np.float64(23.0), np.float64(4.198)], '茶颜悦色': [27, np.float64(18.81), np.float64(19.0), np.float64(22.0), np.float64(4.393)], '7分甜': [23, np.float64(17.22), np.float64(17.0), np.float64(17.0), np.float64(3.909)], '悸动烧仙草': [21, np.float64(16.57), np.float64(17.0), np.float64(17.0), np.float64(3.914)]}
# districts {'江阴市': [294, np.float64(14.95), np.float64(15.0), 14, np.float64(4.8)], '梁溪区': [236, np.float64(17.31), np.float64(16.0), 38, np.float64(16.1)], '宜兴市': [228, np.float64(16.94), np.float64(15.0), 15, np.float64(6.6)], '新吴区': [214, np.float64(14.86), np.float64(15.0), 14, np.float64(6.5)], '滨湖区': [210, np.float64(16.08), np.float64(15.0), 24, np.float64(11.4)], '惠山区': [195, np.float64(14.43), np.float64(14.0), 8, np.float64(4.1)], '锡山区': [194, np.float64(16.07), np.float64(15.0), 17, np.float64(8.8)]}
# biz {'宜城': 82, '崇安寺': 55, '梅村': 36, '澄江': 32, '蠡湖': 31, '清扬路': 28, '丁蜀': 27, '旺庄': 25, '西漳': 21, '洛社': 20}
# hours {'10:00-22:00': 435, '10:00-21:30': 103, '09:00-22:00': 65, '10:00-21:00': 58, '09:30-21:30': 48}
