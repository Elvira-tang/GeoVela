# ─── OpenGIS Agent · run d2fe2b18 · step 56 · accessibility_report_generate ───
# Timestamp : 2026-11-05T23:23:20
# Semantic : accessibility_report_generate
# Metadata : 20261105-232320-step56-accessibility_report_generate.metadata.json
# User query: 基于以上workflow做分析报告
import json, statistics
from pathlib import Path

s = json.load(open('output/report/stats.json', encoding='utf-8'))
tot = s['total']; comp = s['components']; reach = s['reach']

grade_rows = "\n".join(
    f"| {g['grade']} | {g['n']} | {s['grade_share'][g['grade']]:.1f}% | {g['mean']:.1f} | {g['mn']:.1f}–{g['mx']:.1f} |"
    for g in s['grade_stats'])

dorm_rows = "\n".join(
    f"| {d['dorm']} | {d['mean_t']:.1f} | {d['median_t']:.1f} | {d['min_t']:.1f} | {d['max_t']:.1f} | {d['w1']:.1f} | {d['w2']:.1f} | {d['w3']:.1f} | {d['n30']} | {d['n45']} | {d['n60']} | {d['n90']} |"
    for d in s['dorm_table'])

dist_rows = "\n".join(
    f"| {k} | {v} | {s['district_grade'][k]['Ⅰ级 极优']} | {s['district_grade'][k]['Ⅱ级 优']} | {s['district_grade'][k]['Ⅲ级 良']} | {s['district_grade'][k]['Ⅳ级 一般']} | {s['district_grade'][k]['Ⅴ级 较差']} |"
    for k, v in s['district'].items())

brand_rows = "\n".join(
    f"| {b['brand']} | {b['n']} | {b['mean']:.1f} |" for b in s['brand_grade'])

alight = s['stations']['alight_top']
alight_txt = "、".join(f"{k}({v})" for k, v in list(alight.items())[:6])

report = f"""# 江南大学学生宿舍—无锡地铁—奶茶店 可达性分析报告

**研究区**：江苏省无锡市（滨湖区、梁溪区、新吴区）
**分析对象**：20 处江南大学学生宿舍 × 275 家奶茶店，共 5,500 条“宿舍—门店”OD 记录
**数据基准**：`data/processed/accessibility_results.csv`（已完成的全程时间结果，未重新计算步行网络）
**报告生成**：OpenGIS 工作流（数据构建 → 可达性承接 → POI 分级 → 图表 → 报告）

---

## 1. 摘要

本报告以江南大学蠡湖校区 20 处学生宿舍为起点，经无锡地铁（江南大学站上车）到达 275 家奶茶店，
量化“校门—地铁—门店”三段式出行的完整可达性。主要结论：

- **总体水平**：5,500 条 OD 的平均全程时间为 **{tot['mean']:.1f} 分钟**，中位数 **{tot['median']:.1f} 分钟**，
  四分位区间 {tot['p25']:.1f}–{tot['p75']:.1f} 分钟，极差 {tot['min']:.1f}–{tot['max']:.1f} 分钟。
- **构成**：步行至站点 {comp['walk_to_station_min']['mean']:.1f} 分钟（{comp['walk_to_station_min']['share']:.1f}%）、
  地铁乘车 {comp['ride_min']['mean']:.1f} 分钟（{comp['ride_min']['share']:.1f}%）、
  出站步行至门店 {comp['walk_to_poi_min']['mean']:.1f} 分钟（{comp['walk_to_poi_min']['share']:.1f}%）——
  **“两端步行”合计约三分之二（{comp['walk_to_station_min']['share']+comp['walk_to_poi_min']['share']:.1f}%），是时间成本的主体**。
- **可达覆盖**：45 分钟以内可达的门店占 **{reach['le45']:.1f}%**，60 分钟以内 **{reach['le60']:.1f}%**，
  30 分钟以内仅 **{reach['le30']:.1f}%**。
- **门店分级**：Ⅰ级（极优）40 家、Ⅱ级（优）73 家、Ⅲ级（良）98 家、Ⅳ级（一般）50 家、Ⅴ级（较差）14 家；
  **Ⅰ+Ⅱ 级合计 113 家，占 41.0%**，是学生高频可选的主力选项。
- **空间格局**：Ⅰ级门店高度集中于**滨湖区**（40 家全部在滨湖区），新吴区无Ⅰ、Ⅱ级门店；
  宿舍间差异主要体现在“步行至站点”这一段（9.0–23.9 分钟），地铁乘车段几乎相同（15.1–16.9 分钟）。

---

## 2. 数据与方法

### 2.1 数据源

| 数据 | 路径 | 角色 | 规模 |
|---|---|---|---|
| 学生宿舍 | `data/processed/dormitories.csv` | 起点 | 20 处（含重复命名条目，见 5.1） |
| 地铁站点 | `data/raw/metro_stations.csv` | 换乘/乘车节点 | 98 个站点，其中上车 2 个、下车 21 个被实际使用 |
| 奶茶店 | `data/processed/milktea_wgs84.csv` | 终点（WGS84） | 275 家（19 个品牌/类别） |
| 可达性结果 | `data/processed/accessibility_results.csv` | 全程时间 | 5,500 条 OD 记录 |

### 2.2 方法

1. **口径承接**：全程时间直接取自 `accessibility_results.csv` 的既有字段
   （步行至站点时间 `walk_to_station_min`、地铁乘车时间 `ride_min`、出站步行至门店时间 `walk_to_poi_min`、
   合计 `total_min`），**未重建步行网络**，以保证与既有成果一致、可复现。
2. **三段分解**：将全程时间拆解为“宿舍→站点、站间乘车、站点→门店”三段，用于识别成本瓶颈。
3. **住宿点汇总**：对每处宿舍统计其 275 家门店的时间均值/中位数/极值，以及 30/45/60/90 分钟门槛内的可达门店数。
4. **POI 分级**：按门店在所有宿舍上的平均全程时间 `mean_total` 划分 5 级
   （Ⅰ ≤45 分钟；Ⅱ 45–60；Ⅲ 60–75；Ⅳ 75–100；Ⅴ >100 分钟），用于刻画“对学生群体的整体友好度”。
5. **辅助分析**：按行政区、品牌、上下车站点做交叉统计；计算时间与门店评分/价格的相关性（Pearson）。

**分级标准说明**：门槛设定服务于“学生课间/晚间短途消费”的出行情境；等级反映的是**门店相对学生群体的可达便利度**，
不等同于门店品质或商业价值评价。

---

## 3. 关键发现

### 3.1 总体时间分布与可达覆盖

| 指标 | 数值（分钟） |
|---|---|
| 平均 | {tot['mean']:.1f} |
| 中位数 | {tot['median']:.1f} |
| 标准差 | {tot['std']:.1f} |
| 最小 / 最大 | {tot['min']:.1f} / {tot['max']:.1f} |
| P25 / P75 | {tot['p25']:.1f} / {tot['p75']:.1f} |

可达覆盖（以 5,500 条 OD 为样本）：≤30 分钟 **{reach['le30']:.1f}%**、≤45 分钟 **{reach['le45']:.1f}%**、
≤60 分钟 **{reach['le60']:.1f}%**、≤90 分钟 **{reach['le90']:.1f}%**。

解读：分布明显右偏（均值 > 中位数），说明少数远端门店拉长了长尾；**60 分钟是可达性的“半程线”**，
而 30 分钟以内仅剩校园周边极少数门店，符合“地铁出行 + 两端步行”的时间结构。

### 3.2 时间构成：两端步行占三分之二

| 段 | 平均时间（分钟） | 占比 |
|---|---|---|
| 宿舍 → 地铁站（步行） | {comp['walk_to_station_min']['mean']:.1f} | {comp['walk_to_station_min']['share']:.1f}% |
| 地铁乘车（站间） | {comp['ride_min']['mean']:.1f} | {comp['ride_min']['share']:.1f}% |
| 地铁站 → 奶茶店（步行） | {comp['walk_to_poi_min']['mean']:.1f} | {comp['walk_to_poi_min']['share']:.1f}% |

地铁本身只承担约四分之一的时间，**决定性变量是两个步行端**。这意味着：即便门店在地铁沿线，
若出站后步行距离长，实际体验仍可能劣于“更近但略远一站”的门店。

### 3.3 宿舍间差异（按平均全程时间升序）

| 宿舍 | 均值 | 中位数 | 最小 | 最大 | 步行至站 | 乘车 | 出站步行 | ≤30 | ≤45 | ≤60 | ≤90 |
|---|---|---|---|---|---|---|---|---|---|---|---|
{dorm_rows}

- **最优**：瀚苑公寓（均值 {s['dorm_table'][0]['mean_t']:.1f} 分钟）、留学生公寓（{s['dorm_table'][1]['mean_t']:.1f}）、浩苑公寓（{s['dorm_table'][2]['mean_t']:.1f}）；
- **最差**：橙园/桃园公寓（均值 {s['dorm_table'][-1]['mean_t']:.1f} 分钟）、榴园公寓（{s['dorm_table'][-2]['mean_t']:.1f}）；
- 宿舍间均值差距约 **13.2 分钟**（{s['dorm_table'][0]['mean_t']:.1f} vs {s['dorm_table'][-1]['mean_t']:.1f}），
  而 45 分钟可达门店数差距达 **10 倍以上**（42–108 家），**“住在哪一栋”对可选门店范围的影响远大于对平均时间的影响**；
- 该差距几乎全部来自“步行至站点”（{s['dorm_table'][0]['w1']:.1f} vs {s['dorm_table'][-1]['w1']:.1f} 分钟），
  乘车段在宿舍间基本恒定（15.1–16.9 分钟），因为上车集中在江南大学站（S023，3,461 条记录）与另一就近站（S024，2,039 条）。

### 3.4 门店可达性分级

| 等级 | 门店数 | 占比 | 平均全程时间（分钟） | 时间区间（分钟） |
|---|---|---|---|---|
{grade_rows}

- Ⅰ级门店全部位于**滨湖区**，平均 {s['grade_stats'][0]['mean']:.1f} 分钟可到，属于“顺路可买”层级；
- Ⅲ级（良）门店数量最多（98 家），是**覆盖面最广的中间带**；
- Ⅴ级 14 家门店平均 {s['grade_stats'][4]['mean']:.1f} 分钟，最远 {s['grade_stats'][4]['mx']:.1f} 分钟，
  基本不具备日常消费可行性，仅适合专程出行。

### 3.5 行政区分布

| 行政区 | 门店数 | Ⅰ级 | Ⅱ级 | Ⅲ级 | Ⅳ级 | Ⅴ级 |
|---|---|---|---|---|---|---|
{dist_rows}

滨湖区占据 181/275（65.8%），并囊括全部Ⅰ级与 14 家Ⅴ级门店——**近距离门店与超远门店在区内并存**，
呈“近校集聚 + 外围飞地”的结构；梁溪区 70 家门店以Ⅱ、Ⅲ级为主（27 + 26），是“一小时圈层”的主要补充；
新吴区 24 家门店全部落在Ⅲ、Ⅳ级，未见 45 分钟以内选项。

### 3.6 品牌差异

| 品牌/类别 | 门店数 | 平均全程时间（分钟） |
|---|---|---|
{brand_rows}

- “其他/独立门店”数量最多（100 家，占 36.4%），平均 {[b['mean'] for b in s['brand_grade'] if b['brand']=='其他/独立门店'][0]:.1f} 分钟，
  分布跨度大，是长尾的主要来源；
- 连锁品牌中，**霸王茶姬（{52.02:.1f}）、茶颜悦色（{52.75:.1f}）**平均最短，而**古茗（{68.35:.1f}）、益禾堂（{69.81:.1f}）**偏长；
- 门店数极少的品牌（如 7分甜 n=1、悸动烧仙草 n=1）平均值不具统计代表性，应仅作参考。

### 3.7 站点使用与相关性

- 上车高度集中：S023 **3,461 条**、S024 **2,039 条**（合计 100%），说明出行路径对校园最近站强依赖；
- 下车热门站点：{alight_txt}，反映奶茶消费目的地沿地铁走廊分布；
- 时间与价格相关性 r = **{s['corr_price']:.3f}**，与门店评分相关性 r = **{s['corr_rating']:.3f}**：
  两者均为弱负相关，说明**距离近的门店并不系统性地更贵或更受好评**，可达性核心由位置决定而非品质筛选。

---

## 4. 图表解读

![宿舍可达性对比](figures/fig1_dorm_accessibility.png)

**图 1　宿舍可达性对比**：对比 20 处宿舍的平均/中位全程时间与 45、60 分钟可达门店数。左侧显示宿舍间均值差异有限
（约 52–65 分钟），右侧柱状图则放大差异——**可达门店数对住宿位置更敏感**，可用于宿舍区“就近门店选择”的差异化引导。

![时间构成](figures/fig2_time_composition.png)

**图 2　全程时间构成**：三段式分解显示步行至站点（{comp['walk_to_station_min']['share']:.1f}%）与出站步行
（{comp['walk_to_poi_min']['share']:.1f}%）合计约 67%，地铁乘车仅 {comp['ride_min']['share']:.1f}%。**优化方向应优先指向接驳与选址，
而非线路本身**。

![POI 分级](figures/fig3_poi_grading.png)

**图 3　奶茶店可达性分级**：Ⅰ–Ⅴ级的数量与时间分布（含箱线/区间）。分级呈“中间大、两端小”的类正态形态，
Ⅲ级门店数量最多，Ⅰ级门店时间集中且上限 44.3 分钟，可直接作为“推荐清单”。

![品牌与站点](figures/fig4_brand_station.png)

**图 4　品牌与站点特征**：a) 各品牌门店的平均全程时间（门店数标注）；b) 上/下车站点使用频次。
站点图解释了两端步行占主导的原因——**上车端点几乎只有一个（江南大学站）**，学生的时间差异主要由“从哪栋楼走到校门站”决定。

> 说明：以上图件由 `output/figures/`（工作流阶段生成）复制至 `output/report/figures/`，均为本次数据的实测统计结果。

---

## 5. 局限性

1. **未重建步行网络**：本报告沿用 `accessibility_results.csv` 的既有时间，其步行时间依赖生成该文件时的路网、速度与出入口设定；
   若路网更新或校内通行规则变化，绝对时间会偏移，但**宿舍间相对排序与分级结构具有较强稳健性**。
2. **宿舍点存在重复命名**：20 处宿舍记录中含多组同名校验条目
   （如“涓苑公寓臻善楼/江南大学蠡湖校区涓苑公寓”“杏园公寓/鸿园公寓”“桔园公寓/李园公寓”“桃园公寓/橙园公寓”），
   其统计值完全一致，说明原数据中为同一坐标的别名记录。本节按原始记录逐一汇总，未合并去重；
   若用于对外发布，建议先做点位去重（预计实际独立宿舍点少于 20）。
3. **上车点集中**：仅 2 个站点被作为起点站使用，未考虑多站比选或骑行接驳，因此结果对“江南大学站”的步行距离格外敏感，
   不代表校园其他出行方式的真实选择集。
4. **单一出行方式**：未纳入公交、骑行、电动车与打车，实际上学生短途出行可能更快，报告中时间应视为“地铁方案”的时间，而非最短时间。
5. **门店属性未做质量筛选**：275 家门店仅以名称/品牌与坐标参与计算，未核查营业状态、营业时间与是否支持外卖；
   分级是**可达性**评价，不含品质与价格判断。
6. **时间口径**：未计入候车、进站安检、取餐排队等时间，实际体验应在此基础上上浮（通常 5–10 分钟量级），
   因此 45 分钟门槛应理解为乐观边界。

---

## 6. 结论与建议

**结论**

1. 江南大学宿舍到奶茶店的地铁方案平均约 **{tot['mean']:.0f} 分钟**，60 分钟覆盖 **{reach['le60']:.1f}%** 的门店，
   45 分钟覆盖 **{reach['le45']:.1f}%**；可达性整体处于“一小时生活圈”水平，但**30 分钟舒适圈极薄（{reach['le30']:.1f}%）**。
2. 时间瓶颈在**两端步行（约 67%）**，而非地铁乘车；宿舍位置通过“步行至站点”影响可达性，最优与最差宿舍相差约 13 分钟、
   45 分钟可达门店数相差 10 倍以上。
3. 门店层面形成清晰的 5 级结构：Ⅰ级 40 家（滨湖区集中）、Ⅱ级 73 家、Ⅲ级 98 家、Ⅳ级 50 家、Ⅴ级 14 家；
   **优先推荐Ⅰ、Ⅱ级共 113 家**，可作为学生日常消费的默认选项池。
4. 行政区与新吴区、梁溪区形成明显梯度：滨湖区“近者更近”，梁溪区“慢而稳”，新吴区“仅在良—一般区间”。
5. 时间与价格/评分弱负相关，说明**可达性与门店品质不是同一维度**，学生选择需要在“时间—品质”间权衡而非单向优化。

**建议（面向后续优化，非本次数据结论）**

1. **接驳优先**：改善宿舍区至江南大学站的步行通道（校门开口、步行捷径、非机动车停放），可直接压缩占比最高的 29% 段；
2. **站点端选址**：门店若面向学生客群，应优先评估“出站 5 分钟步行圈”内的布点，该段平均已占 37.5%，是差异化最大空间；
3. **分级运营**：以Ⅰ、Ⅱ级门店作为校园推广核心清单，Ⅲ级作为“一小时圈层”备选，Ⅳ、Ⅴ级不建议纳入学生向营销；
4. **数据完善**：补充去重后的宿舍点位、多站比选、骑行/公交方案与候车时间，以获得“最短时间”而非“地铁方案时间”的口径；
5. **可复现**：本次分析脚本与图层已保存在工作区（`script/`、`output/`），可直接替换新数据重跑。

---

## 附录：产出文件

| 文件 | 内容 |
|---|---|
| `output/dorm_accessibility_summary.csv/.geojson` | 20 处宿舍可达性汇总 |
| `output/poi_accessibility_grades.csv/.geojson` | 275 家门店分级结果 |
| `output/reachable_milktea.geojson` | 参与计算的奶茶店点位 |
| `output/metro_stations.geojson` | 地铁站点 |
| `output/top5_routes.geojson` | 宿舍→门店最快前 5 条线路 |
| `output/report/figures/fig1–fig4` | 本报告图件 |
| `output/report/stats.json` | 本报告引用的全部统计指标 |
"""
Path('output/report').mkdir(parents=True, exist_ok=True)
Path('output/report/report.md').write_text(report, encoding='utf-8')
print(len(report), 'chars written')

# ─── Observations ───
# Error: Traceback (most recent call last):
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\GeoVela\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 468, in _run_exec
#     compiled = compile(code, "<agent>", "eval")
#   File "<agent>", line 1
#     import json, statistics
#     ^^^^^^
# SyntaxError: invalid syntax
# 
# During handling of the above exception, another exception occurred:
# 
# Traceback (most recent call last):
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\GeoVela\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 471, in _run_exec
#     exec(compile(code, "<agent>", "exec"), namespace, namespace)
#     ~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "<agent>", line 43, in <module>
# KeyError: 'walk_to_poi'
# 
# --- stdout before error ---
