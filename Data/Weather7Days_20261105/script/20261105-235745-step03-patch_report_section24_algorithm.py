# ─── OpenGIS Agent · run 9fbf6c38 · step 3 · patch_report_section24_algorithm ───
# Timestamp : 2026-11-05T23:57:45
# Semantic : patch_report_section24_algorithm
# Metadata : 20261105-235745-step03-patch_report_section24_algorithm.metadata.json
# User query: 预测的算法也需要在分析报告中指出
import re, pathlib

rp = pathlib.Path("output/report/china_weather_analysis_report.md")
text = rp.read_text(encoding="utf-8")
new_sec = pathlib.Path("output/report/_tmp_algo_section.md").read_text(encoding="utf-8").rstrip("\n")

def rep(pat, repl, s, count=1, flags=0):
    new, n = re.subn(pat, lambda m: repl, s, count=count, flags=flags)
    print(n, "|", pat[:46])
    return new

text = rep(r"### 2\.4 预测模型与约束.*?(?=\n---\n\n## 三、)", new_sec + "\n", text, count=1, flags=re.S)
text = rep(r"\| 相对湿度 \| —（原始表未直接提供） \| % \| \*\*派生指标\*\*：[^|]*\|",
           "| 相对湿度 | —（原始表未直接提供） | % | **派生指标**：由降水量、降水时长、日照时长与天气现象联合重构，系数为经验设定而非拟合，公式见 2.4.2 |", text)
text = rep(r"\| 气压 \| —（原始表未直接提供） \| hPa \| \*\*派生指标\*\*：[^|]*\|",
           "| 气压 | —（原始表未直接提供） | hPa | **派生指标**：由降水量、气温距平与风速修正重构（无海拔项），公式见 2.4.2；仅用于趋势判断 |", text)
text = rep(r"置信度分级为 较高 11 城 / 中等 11 城 / 较低 1 城。",
           "置信度分级按 36 条预测记录统计为 较高 22 条 / 中等 11 条 / 较低 3 条（分级规则见 2.4.8）。", text)
text = rep(r"\| 置信度分布 \| 较高 11 城、中等 11 城、较低 1 城 \|",
           "| 置信度分布 | 较高 22 条、中等 11 条、较低 3 条（共 36 条预测记录） |", text)
text = rep(r"是\*\*单变量、无物理约束的纯统计外推\*\*。",
           "是**单变量、无物理约束的纯统计外推**（完整公式、参数与伪代码见 2.4 节）。", text)

text = text.replace("\n\n\n\n", "\n\n\n")
rp.write_text(text, encoding="utf-8")

chk = rp.read_text(encoding="utf-8")
print("lines", len(chk.splitlines()), "chars", len(chk))
for h in ["2.4.1", "2.4.2", "2.4.3", "2.4.4", "2.4.5", "2.4.6", "2.4.7", "2.4.8", "2.4.9", "2.4.10"]:
    print(h, chk.count("#### " + h))
print("old heading left:", chk.count("### 2.4 预测模型与约束"))
print("sec3 exists:", "## 三、" in chk, "| stale 11城:", chk.count("较高 11 城"))
pathlib.Path("output/report/_tmp_algo_section.md").unlink()

# ─── Observations ───
# Error: Traceback (most recent call last):
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\GeoVela\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 471, in _run_exec
#     exec(compile(code, "<agent>", "exec"), namespace, namespace)
#     ~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "<agent>", line 12, in <module>
#   File "<agent>", line 8, in rep
#   File "D:\Download\Miniconda\Lib\re\__init__.py", line 238, in subn
#     return _compile(pattern, flags).subn(repl, string, count)
#            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
#   File "D:\Download\Miniconda\Lib\re\__init__.py", line 377, in _compile_template
#     return _sre.template(pattern, _parser.parse_template(repl, pattern))
#                                   ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
#   File "D:\Download\Miniconda\Lib\re\_parser.py", line 1076, in parse_template
#     raise s.error('bad escape %s' % this, len(this)) from None
# re.PatternError: bad escape \h at position 1516 (line 37, column 3)
# 
# --- stdout before error ---
