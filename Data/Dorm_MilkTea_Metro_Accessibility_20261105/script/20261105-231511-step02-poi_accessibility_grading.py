# ─── OpenGIS Agent · run 1f747b07 · step 2 · poi_accessibility_grading ───
# Timestamp : 2026-11-05T23:15:11
# Semantic : poi_accessibility_grading
# Metadata : 20261105-231511-step02-poi_accessibility_grading.metadata.json
# User query: 绘制可达性分析图表，并对poi进行分级
import pandas as pd, numpy as np, json, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
_c = ['PingFang SC','STHeiti','Heiti SC','SimHei','Microsoft YaHei','Noto Sans CJK SC']
_a = set(f.name for f in fm.fontManager.ttflist)
plt.rcParams['font.sans-serif'] = [x for x in _c if x in _a] or ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

df = pd.read_csv('data/processed/accessibility_results.csv')
mt = pd.read_csv('data/processed/milktea_wgs84.csv')
os.makedirs('output', exist_ok=True)

# ---------- POI 分级 ----------
g = df.groupby('poi_id').agg(
    poi_name=('poi_name','first'), brand=('brand','first'),
    mean_total=('total_min','mean'), min_total=('total_min','min'),
    median_total=('total_min','median'), max_total=('total_min','max'),
    n45=('total_min', lambda s: int((s<=45).sum())),
    n60=('total_min', lambda s: int((s<=60).sum())),
    n_dorm=('dorm','nunique'),
).reset_index()

# jenks 自然断点(1D k-means 初始化+迭代) 5 级
from sklearn.cluster import KMeans
def jenks(vals, k=5):
    v = np.asarray(vals).reshape(-1,1)
    km = KMeans(n_clusters=k, n_init=20, random_state=0).fit(v)
    c = np.sort(km.cluster_centers_.ravel())
    breaks = [(c[i]+c[i+1])/2 for i in range(len(c)-1)]
    return c, breaks

centers, breaks = jenks(g['mean_total'], 5)
labels = ['Ⅰ级 极优','Ⅱ级 优','Ⅲ级 良','Ⅳ级 一般','Ⅴ级 较差']
g['grade'] = pd.cut(g['mean_total'], bins=[-np.inf]+list(breaks)+[np.inf], labels=labels)
g['grade_num'] = g['grade'].cat.codes + 1
print('breaks', [round(b,2) for b in breaks])
print(g.groupby('grade', observed=True).agg(n=('poi_id','size'), mean=('mean_total','mean'), n45=('n45','mean')).round(2).to_string())

# 合并坐标
gg = g.merge(mt[['poi_id','longitude','latitude','district','rating','price_cny']], on='poi_id', how='left')
print('missing coord', gg.longitude.isna().sum())
gg.to_csv('output/poi_accessibility_grades.csv', index=False, encoding='utf-8-sig')

feats = []
for _, r in gg.dropna(subset=['longitude','latitude']).iterrows():
    feats.append({"type":"Feature",
        "geometry":{"type":"Point","coordinates":[float(r.longitude), float(r.latitude)]},
        "properties":{"poi_id":r.poi_id,"name":r.poi_name,"brand":r.brand,
            "grade":str(r.grade),"grade_num":int(r.grade_num),
            "mean_total":round(float(r.mean_total),1),"min_total":round(float(r.min_total),1),
            "n45":int(r.n45),"n60":int(r.n60),"district":r.district,
            "rating":None if pd.isna(r.rating) else float(r.rating),
            "price":None if pd.isna(r.price_cny) else float(r.price_cny)}})
with open('output/poi_accessibility_grades.geojson','w',encoding='utf-8') as f:
    json.dump({"type":"FeatureCollection","features":feats}, f, ensure_ascii=False)
print('geojson features', len(feats))

# ─── Observations ───
# [auto-install] Auto-installed: scikit-learn
# breaks [np.float64(38.1), np.float64(53.91), np.float64(71.59), np.float64(102.88)]
#         n    mean    n45
# grade                   
# Ⅰ级 极优  40   31.09  20.00
# Ⅱ级 优   73   45.11   9.68
# Ⅲ级 良   98   62.72   0.00
# Ⅳ级 一般  50   80.46   0.00
# Ⅴ级 较差  14  125.30   0.00
# missing coord 0
# geojson features 275
