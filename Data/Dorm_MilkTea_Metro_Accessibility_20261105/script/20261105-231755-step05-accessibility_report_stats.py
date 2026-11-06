# ─── OpenGIS Agent · run d2fe2b18 · step 5 · accessibility_report_stats ───
# Timestamp : 2026-11-05T23:17:55
# Semantic : accessibility_report_stats
# Metadata : 20261105-231755-step05-accessibility_report_stats.metadata.json
# User query: 基于以上workflow做分析报告
import pandas as pd, numpy as np, json, os, shutil
df = pd.read_csv('data/processed/accessibility_results.csv')
gg = pd.read_csv('output/poi_accessibility_grades.csv')
dorms = pd.read_csv('data/processed/dormitories.csv')
os.makedirs('output/report/figures', exist_ok=True)
for f in os.listdir('output/figures'):
    shutil.copy2(os.path.join('output/figures', f), os.path.join('output/report/figures', f))

S = {}
S['n_obs'] = int(len(df)); S['n_dorm'] = int(df.dorm.nunique()); S['n_poi'] = int(df.poi_id.nunique())
t = df.total_min
S['total'] = dict(mean=float(t.mean()), median=float(t.median()), std=float(t.std()),
                  min=float(t.min()), p25=float(t.quantile(.25)), p75=float(t.quantile(.75)),
                  max=float(t.max()))
for c in ['walk_to_station_min','ride_min','walk_to_poi_min']:
    S.setdefault('components',{})[c]=dict(mean=float(df[c].mean()), share=float(df[c].mean()/t.mean()*100))
for th in (30,45,60,90):
    S.setdefault('reach',{})[f'le{th}']=float((t<=th).mean()*100)

g = df.groupby('dorm').agg(mean_t=('total_min','mean'), min_t=('total_min','min'), max_t=('total_min','max'),
                           median_t=('total_min','median'),
                           w1=('walk_to_station_min','mean'), w2=('ride_min','mean'), w3=('walk_to_poi_min','mean'),
                           n30=('total_min',lambda s:int((s<=30).sum())), n45=('total_min',lambda s:int((s<=45).sum())),
                           n60=('total_min',lambda s:int((s<=60).sum())), n90=('total_min',lambda s:int((s<=90).sum())))
g = g.sort_values('mean_t').round(2)
S['dorm_table'] = g.reset_index().to_dict('records')

r = df.groupby('dorm').total_min.rank(pct=True)
S['gini_mean'] = float(np.mean(np.abs(g.mean_t.values[:,None]-g.mean_t.values[None,:]))/(2*g.mean_t.mean()))
cnt = gg.grade.value_counts().reindex(['Ⅰ级 极优','Ⅱ级 优','Ⅲ级 良','Ⅳ级 一般','Ⅴ级 较差'])
S['grade_counts'] = {k:int(v) for k,v in cnt.items()}
S['grade_share'] = {k:round(v/len(gg)*100,1) for k,v in cnt.items()}
S['grade_stats'] = gg.groupby('grade').agg(n=('poi_id','size'), mean=('mean_total','mean'), mn=('min_total','min'),
                    mx=('max_total','max'), n45=('n45','mean'), n60=('n60','mean')).round(2).reindex(cnt.index).reset_index().to_dict('records')
S['district'] = gg.district.value_counts().to_dict()
S['district_grade'] = pd.crosstab(gg.district, gg.grade).reindex(columns=cnt.index).to_dict('index')
S['brand_n'] = int(gg.brand.nunique())
S['brand_top'] = gg.brand.value_counts().head(10).to_dict()
S['brand_grade'] = gg.groupby('brand').agg(n=('poi_id','size'), mean=('mean_total','mean')).sort_values('mean').round(2).reset_index().to_dict('records')
S['stations'] = dict(n_board=int(df.board_station.nunique()), n_alight=int(df.alight_station.nunique()),
                     board=df.board_station.value_counts().to_dict(), alight_top=df.alight_station.value_counts().head(10).to_dict())
S['dorm_coords'] = dorms.to_dict('records') if len(dorms)<30 else None
S['corr_price'] = float(np.corrcoef(gg.mean_total, gg.price_cny.fillna(gg.price_cny.median()))[0,1]) if gg.price_cny.notna().any() else None
S['corr_rating'] = float(np.corrcoef(gg.mean_total, gg.rating.fillna(gg.rating.median()))[0,1]) if gg.rating.notna().any() else None
json.dump(S, open('output/report/stats.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({k:v for k,v in S.items() if k not in ('dorm_table','poi')}, ensure_ascii=False, indent=1)[:4000])
print(g.reset_index().to_string())

# ─── Observations ───
# {
#  "n_obs": 5500,
#  "n_dorm": 20,
#  "n_poi": 275,
#  "total": {
#   "mean": 59.85567272727272,
#   "median": 58.8,
#   "std": 22.856434739954647,
#   "min": 16.6,
#   "p25": 43.6,
#   "p75": 70.6,
#   "max": 143.4
#  },
#  "components": {
#   "walk_to_station_min": {
#    "mean": 17.643581818181822,
#    "share": 29.476874979875845
#   },
#   "ride_min": {
#    "mean": 15.748090909090912,
#    "share": 26.310105945756803
#   },
#   "walk_to_poi_min": {
#    "mean": 22.464,
#    "share": 37.53027737630701
#   }
#  },
#  "reach": {
#   "le30": 5.818181818181818,
#   "le45": 27.400000000000002,
#   "le60": 52.92727272727272,
#   "le90": 92.2
#  },
#  "gini_mean": 0.03874938392267914,
#  "grade_counts": {
#   "Ⅰ级 极优": 40,
#   "Ⅱ级 优": 73,
#   "Ⅲ级 良": 98,
#   "Ⅳ级 一般": 50,
#   "Ⅴ级 较差": 14
#  },
#  "grade_share": {
#   "Ⅰ级 极优": 14.5,
#   "Ⅱ级 优": 26.5,
#   "Ⅲ级 良": 35.6,
#   "Ⅳ级 一般": 18.2,
#   "Ⅴ级 较差": 5.1
#  },
#  "grade_stats": [
#   {
#    "grade": "Ⅰ级 极优",
#    "n": 40,
#    "mean": 31.09,
#    "mn": 16.6,
#    "mx": 44.3,
#    "n45": 20.0,
#    "n60": 20.0
#   },
#   {
#    "grade": "Ⅱ级 优",
#    "n": 73,
#    "mean": 45.11,
#    "mn": 29.0,
#    "mx": 58.8,
#    "n45": 9.68,
#    "n60": 20.0
#   },
#   {
#    "grade": "Ⅲ级 良",
#    "n": 98,
#    "mean": 62.72,
#    "mn": 46.7,
#    "mx": 75.3,
#    "n45": 0.0,
#    "n60": 6.64
#   },
#   {
#    "grade": "Ⅳ级 一般",
#    "n": 50,
#    "mean": 80.46,
#    "mn": 64.6,
#    "mx": 108.5,
#    "n45": 0.0,
#    "n60": 0.0
#   },
#   {
#    "grade": "Ⅴ级 较差",
#    "n": 14,
#    "mean": 125.3,
#    "mn": 97.4,
#    "mx": 143.4,
#    "n45": 0.0,
#    "n60": 0.0
#   }
#  ],
#  "district": {
#   "滨湖区": 181,
#   "梁溪区": 70,
#   "新吴区": 24
#  },
#  "district_grade": {
#   "新吴区": {
#    "Ⅰ级 极优": 0,
#    "Ⅱ级 优": 0,
#    "Ⅲ级 良": 14,
#    "Ⅳ级 一般": 10,
#    "Ⅴ级 较差": 0
#   },
#   "梁溪区": {
#    "Ⅰ级 极优": 0,
#    "Ⅱ级 优": 27,
#    "Ⅲ级 良": 26,
#    "Ⅳ级 一般": 17,
#    "Ⅴ级 较差": 0
#   },
#   "滨湖区": {
#    "Ⅰ级 极优": 40,
#    "Ⅱ级 优": 46,
#    "Ⅲ级 良": 58,
#    "Ⅳ级 一般": 23,
#    "Ⅴ级 较差": 14
#   }
#  },
#  "brand_n": 19,
#  "brand_top": {
#   "其他/独立门店": 100,
#   "蜜雪冰城": 43,
#   "一点点": 21,
#   "CoCo都可": 20,
#   "茶百道": 20,
#   "喜茶": 10,
#   "古茗": 10,
#   "霸王茶姬": 10,
#   "沪上阿姨": 9,
#   "茶颜悦色": 8
#  },
#  "brand_grade": [
#   {
#    "brand": "乐乐茶",
#    "n": 4,
#    "mean": 46.09
#   },
#   {
#    "brand": "茉酸奶",
#    "n": 3,
#    "mean": 47.32
#   },
#   {
#    "brand": "霸王茶姬",
#    "n": 10,
#    "mean": 52.02
#   },
#   {
#    "brand": "茶颜悦色",
#    "n": 8,
#    "mean": 52.75
#   },
#   {
#    "brand": "其他/独立门店",
#    "n": 100,
#    "mean": 55.62
#   },
#   {
#    "brand": "喜茶",
#    "n": 10,
#    "mean": 58.39
#   },
#   {
#    "brand": "奈雪的茶",
#    "n": 2,
#    "mean": 59.16
#   },
#   {
#    "brand": "CoCo都可",
#    "n": 20,
#    "mean": 59.59
#   },
#   {
#    "brand": "茶百道",
#    "n": 20,
#    "mean": 61.92
#   },
#   {
#    "brand": "一点点",
#    "n": 21,
#    "mean": 63.86
#   },
#   {
#    "brand": "沪上阿姨",
#    "n": 9,
#    "mean": 64.54
#   },
#   {
#    "brand": "柠檬森林",
#    "n": 4,
#    "mean": 64.61
#   },
#   {
#    "brand": "蜜雪冰城",
#    "n": 43,
#    "mean": 65.07
#   },
#   {
#    "brand": "贡茶",
#    "n": 2,
#    "mean": 66.46
#   },
#   {
#    "brand": "古茗",
#    "n": 10,
#    "mean": 68.35
#   },
#   {
#    "brand": "益禾堂",
#    "n": 4,
#    "mean": 69.81
#   },
#   {
#    "brand": "柠季",
#    "n": 3,
#    "mean": 78.81
#   },
#   {
#    "brand": "悸动烧仙草",
#    "n": 1,
#    "mean": 79.02
#   },
#   {
#    "brand": "7分甜",
#    "n": 1,
#    "mean": 107.61
#   }
#  ],
#  "stations": {
#   "n_board": 2,
#   "n_alight": 21,
#   "board": {
#    "S023": 3461,
#    "S024": 2039
#   },
#   "alight_top": {
#    "S079": 880,
#    "S013": 560,
#    "S014": 520,
#    "S021": 440,
#    "S022": 400,
#    "S023": 380,
#    "S031": 360,
#    "S078": 340,
#    "S015": 300,
#    "S024": 220
#   }
#  },
#  "dorm_coords": [
#   {
#    "宿舍名称": "江南大学蠡湖校区鸿苑公寓",
#    "经度": 120.270024,
#    "纬度": 31.479262,
#    "层数": 6,
#    "高度(m)": 18.0,
#    "面积(m2)": 1003.7,
#    "学生人数": NaN,
#    "备注": "学生人数待学校数据补充"
#   },
#   {
#    "宿舍名称": "江南大学蠡湖校区瀚苑公寓",
#    "经度": 120.26764,
#    "纬度": 31.477461,
#    "层数": 6,
#    "高度(m)": 18.0,
#    "面积(m2)": 2401.8,
#    "学生人数": NaN,
#    "备注": "学生人数待学校数据补充"
#   },
#   {
#    "宿舍名称": "浩苑公寓",
#    "经度": 120.264037,
#    "纬度": 31.47717,
#    "层数": 6,
#    "高度(m)": 18.0,
#    "面积(m2)": 7408.1,
#    "学生人数": NaN,
#    "备注": "学生人数待学校数据补充"
#   },
#   {
#    "宿舍名称": "江南大学蠡湖校区澈苑公寓",
#    "经度": 120.265615,
#    "纬度": 31.477635,
#    "层数": 6,
#    "高度(m)": 18.0,
#    "面积(m2)": 2836.9,
#  
#             dorm  mean_t  min_t  max_t  median_t     w1     w2     w3  n30  n45  n60  n90
# 0   江南大学蠡湖校区瀚苑公寓   52.34   16.6  130.4      51.7   9.00  16.88  22.46   41  108  199  260
# 1          留学生公寓   52.84   17.1  130.9      52.2   9.50  16.88  22.46   41  106  193  260
# 2   江南大学蠡湖校区浩苑公寓   53.79   17.7  131.5      52.8  12.20  15.13  22.46   36  105  183  255
# 3   江南大学蠡湖校区鸿苑公寓   55.28   19.4  133.2      54.5  13.87  14.95  22.46   38  100  173  255
# 4   江南大学蠡湖校区澈苑公寓   56.34   20.6  134.4      55.7  13.00  16.88  22.46   31   95  167  254
# 5           浩苑公寓   58.14   22.4  136.2      57.5  14.80  16.88  22.46   15   88  154  253
# 6   江南大学蠡湖校区清苑公寓   58.34   22.6  136.4      57.7  15.00  16.88  22.46   15   88  153  253
# 7           青教公寓   58.89   22.8  136.6      57.9  17.30  15.13  22.46   14   87  149  253
# 8   江南大学蠡湖校区溪苑公寓   59.14   23.4  137.2      58.5  17.21  15.47  22.46   11   81  144  253
# 9        涓苑公寓臻善楼   60.14   24.4  138.2      59.5  16.80  16.88  22.46   10   75  142  253
# 10  江南大学蠡湖校区涓苑公寓   60.14   24.4  138.2      59.5  16.80  16.88  22.46   10   75  142  253
# 11  江南大学蠡湖校区杏园公寓   61.29   25.2  139.0      60.3  19.70  15.13  22.46   10   70  131  253
# 12          鸿园公寓   61.29   25.2  139.0      60.3  19.70  15.13  22.46   10   70  131  253
# 13  江南大学蠡湖校区梅园公寓   61.89   25.8  139.6      60.9  20.30  15.13  22.46   10   67  130  253
# 14  江南大学蠡湖校区李园公寓   62.59   26.5  140.3      61.6  21.00  15.13  22.46   10   62  130  253
# 15  江南大学蠡湖校区桔园公寓   62.59   26.5  140.3      61.6  21.00  15.13  22.46   10   62  130  253
# 16  江南大学蠡湖校区榴园公寓   65.39   29.3  143.1      64.4  23.80  15.13  22.46    2   42  115  251
# 17  江南大学蠡湖校区桃园公寓   65.49   29.4  143.2      64.5  23.90  15.13  22.46    2   42  115  251
# 18  江南大学蠡湖校区橙园公寓   65.49   29.4  143.2      64.5  23.90  15.13  22.46    2   42  115  251
# 19  江南大学蠡湖校区桂园公寓   65.69   29.6  143.4      64.7  24.10  15.13  22.46    2   42  115  251
