# ─── OpenGIS Agent · run 4cc7c41c · step 3 · parse_poi_csv_validate_wgs84 ───
# Timestamp : 2026-11-06T00:48:32
# Semantic : parse_poi_csv_validate_wgs84
# Metadata : 20261106-004832-step03-parse_poi_csv_validate_wgs84.metadata.json
# User query: input.csv contains deliberately appended malformed rows. Parse it robustly using the WGS84 longitude/latitude columns. Reject rows whose coordinates are missing, non-numeric, or outside valid ranges. …
import csv, io, json, math

INPUT = "input.csv"
OUTPUT = "result.json"

LON_H = "经度(WGS84)"
LAT_H = "纬度(WGS84)"


def read_rows(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    for enc in ("utf-8-sig", "gb18030", "utf-8", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    return text, list(csv.reader(io.StringIO(text)))


def is_blank(row):
    return all((c is None or str(c).strip() == "") for c in row)


def check_num(value, is_lat):
    """return (number_or_None, reason_or_None)"""
    if value is None or str(value).strip() == "":
        return None, "missing"
    try:
        num = float(str(value).strip())
    except (TypeError, ValueError):
        return None, "non_numeric"
    if math.isnan(num) or math.isinf(num):
        return None, "non_numeric"
    lo, hi = (-90.0, 90.0) if is_lat else (-180.0, 180.0)
    if num < lo or num > hi:
        return None, "out_of_range"
    return num, None


text, rows = read_rows(INPUT)
header = [h.strip() for h in rows[0]]
n = len(header)
i_lon, i_lat = header.index(LON_H), header.index(LAT_H)

valid, rejected, skipped = [], [], 0
for idx, row in enumerate(rows[1:], start=1):
    if is_blank(row):
        skipped += 1
        continue
    if [c.strip() for c in row] == header:
        skipped += 1
        continue

    notes = []
    cells = list(row)
    coord_problems = []

    if len(cells) != n:
        # column alignment is broken: do not trust fixed offsets, scan the
        # widened coordinate span for the coordinate values that are present
        notes.append("column_count_mismatch")
        surplus = abs(len(cells) - n)
        span_lo = max(0, i_lon - surplus)
        span_hi = i_lat + surplus
        span = [c.strip() for c in cells[span_lo:span_hi + 1]]
        tokens = [c for c in span if c != ""]
        lon_raw = tokens[0] if len(tokens) > 0 else ""
        lat_raw = tokens[1] if len(tokens) > 1 else ""
        notes.append("coordinate_values_found=%d" % len(tokens))
        if len(tokens) < 2:
            coord_problems.append("missing_coordinate_value")
    else:
        lon_raw, lat_raw = cells[i_lon].strip(), cells[i_lat].strip()

    lon, lon_err = check_num(lon_raw, is_lat=False)
    lat, lat_err = check_num(lat_raw, is_lat=True)

    if lon_err == "missing":
        coord_problems.append("missing_longitude")
    elif lon_err == "non_numeric":
        coord_problems.append("non_numeric_longitude")
    elif lon_err == "out_of_range":
        coord_problems.append("longitude_out_of_range")
    if lat_err == "missing":
        coord_problems.append("missing_latitude")
    elif lat_err == "non_numeric":
        coord_problems.append("non_numeric_latitude")
    elif lat_err == "out_of_range":
        coord_problems.append("latitude_out_of_range")
    if "missing_coordinate_value" in coord_problems:
        coord_problems = [p for p in coord_problems
                          if p not in ("missing_longitude", "missing_latitude")]

    reasons = notes + coord_problems
    if coord_problems:
        rejected.append({
            "data_row_index": idx,
            "poi_id": cells[0].strip() if cells else "",
            "name": cells[1].strip() if len(cells) > 1 else "",
            "longitude_raw": lon_raw,
            "latitude_raw": lat_raw,
            "field_count": len(cells),
            "reasons": reasons,
            "raw_row": cells,
        })
        continue

    record = {}
    for k, col in enumerate(header):
        record[col] = cells[k].strip() if k < len(cells) and cells[k] is not None else ""
    record[LON_H] = lon
    record[LAT_H] = lat
    record["_data_row_index"] = idx
    if notes:
        record["_notes"] = notes
    valid.append(record)

result = {
    "source_file": INPUT,
    "crs": "WGS84 (EPSG:4326)",
    "coordinate_columns": {"longitude": LON_H, "latitude": LAT_H},
    "validation_rules": {
        "missing": "blank / empty coordinate value",
        "non_numeric": "value that cannot be parsed as a finite float",
        "out_of_range": "longitude outside [-180, 180] or latitude outside [-90, 90]",
    },
    "summary": {
        "header_field_count": n,
        "data_rows_parsed": len(valid) + len(rejected),
        "blank_or_repeated_header_rows_skipped": skipped,
        "valid_count": len(valid),
        "rejected_count": len(rejected),
    },
    "valid_rows": valid,
    "rejected_rows": rejected,
}

with open(OUTPUT, "w", encoding="utf-8") as fh:
    json.dump(result, fh, ensure_ascii=False, indent=2)

print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
for r in rejected:
    print(r["data_row_index"], r["poi_id"], r["name"], r["longitude_raw"], r["latitude_raw"], r["reasons"])
print("sample valid:", {k: valid[0][k] for k in list(valid[0])[:6]}, valid[0][LON_H], valid[0][LAT_H])

# ─── Observations ───
# {
#   "header_field_count": 21,
#   "data_rows_parsed": 1657,
#   "blank_or_repeated_header_rows_skipped": 1,
#   "valid_count": 1654,
#   "rejected_count": 3
# }
# 1656 BROKEN-1 损坏数据 31.5  ['column_count_mismatch(22!=21)', 'missing_latitude']
# 1657 BROKEN-2 缺失经度 31.5  ['column_count_mismatch(22!=21)', 'missing_latitude']
# 1658 BROKEN-3 超出范围 999  ['column_count_mismatch(22!=21)', 'longitude_out_of_range', 'missing_latitude']
# sample valid: {'POI_ID': 'B0FFILMESX', '名称': '1点点(上马墩店)', '品牌': '一点点', '类型': '餐饮服务;冷饮店;冷饮店', '类型编码': '050700', '地址': '江苏省无锡市梁溪区梁溪区上马墩路140-4号(上马墩南片小区北门旁)'} 120.321536 31.584962
