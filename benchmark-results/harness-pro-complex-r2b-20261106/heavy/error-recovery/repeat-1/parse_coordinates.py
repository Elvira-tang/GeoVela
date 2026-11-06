"""Robust POI CSV parser for WGS84 longitude/latitude validation.

Handles deliberately malformed rows:
  * shifted / wrong field counts (repairable by one-cell insert/delete)
  * missing coordinate values
  * non-numeric coordinate values
  * out-of-range coordinate values

Outputs result.json with valid_rows and rejected_rows.
"""

import csv
import json
import math
import os

SRC = "input.csv"
OUT = "result.json"

LON_FIELD = "经度(WGS84)"
LAT_FIELD = "纬度(WGS84)"
ID_FIELD = "POI_ID"
NAME_FIELD = "名称"

EMPTY_TOKENS = {"", "na", "n/a", "nan", "null", "none", "-", "--"}

# reason priority: most specific defect first
REASON_PRIORITY = [
    "non_numeric_longitude",
    "non_numeric_latitude",
    "out_of_range_longitude",
    "out_of_range_latitude",
    "missing_longitude",
    "missing_latitude",
]


def read_rows(path):
    for enc in ("utf-8-sig", "utf-8", "gbk", "latin-1"):
        try:
            with open(path, "r", encoding=enc, newline="") as f:
                rows = list(csv.reader(f))
            return rows, enc
        except UnicodeDecodeError:
            continue
    raise RuntimeError("cannot decode source file")


def to_float(token):
    """Return (value_or_None, is_missing, is_numeric)."""
    if token is None:
        return None, True, False
    s = str(token).strip().replace("\u3000", "")
    if s.lower() in EMPTY_TOKENS:
        return None, True, False
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None, False, False
    if math.isnan(v) or math.isinf(v):
        return None, True, False
    return v, False, True


def coord_status(lon_tok, lat_tok):
    lon, lon_missing, lon_num = to_float(lon_tok)
    lat, lat_missing, lat_num = to_float(lat_tok)
    reasons = []
    if not lon_missing and not lon_num:
        reasons.append("non_numeric_longitude")
    if not lat_missing and not lat_num:
        reasons.append("non_numeric_latitude")
    if lon_num and not (-180.0 <= lon <= 180.0):
        reasons.append("out_of_range_longitude")
    if lat_num and not (-90.0 <= lat <= 90.0):
        reasons.append("out_of_range_latitude")
    if lon_missing:
        reasons.append("missing_longitude")
    if lat_missing:
        reasons.append("missing_latitude")
    return {
        "lon": lon,
        "lat": lat,
        "reasons": reasons,
        "valid": not reasons,
        "has_both": (not lon_missing) and (not lat_missing),
        "filled": int(not lon_missing) + int(not lat_missing),
    }


def best_reason(statuses):
    for code in REASON_PRIORITY:
        for st in statuses:
            if code in st["reasons"]:
                return code
    return "invalid_coordinates"


def reconcile(row, header, i_lon, i_lat, n_cols):
    """Return (aligned_row, repaired_flag) minimizing coordinate defects."""
    if len(row) == n_cols:
        return row, False

    candidates = []
    diff = len(row) - n_cols
    # shift repairs: insert one blank at `pos` and drop the overflowing tail cell
    if diff > 0:
        for pos in range(n_cols):
            cand = row[:pos] + [""] + row[pos:n_cols - 1]
            if len(cand) == n_cols:
                candidates.append(cand)
    if diff == -1:
        for pos in range(len(row) + 1):
            candidates.append(row[:pos] + [""] + row[pos:])
    elif diff == 1:
        for pos in range(len(row)):
            candidates.append(row[:pos] + row[pos + 1:])
    elif diff < -1:
        for pos in range(len(row) + 1):
            candidates.append(row[:pos] + [""] * (-diff) + row[pos:])
    else:
        for pos in range(len(row)):
            candidates.append(row[:pos] + row[pos + diff:])

    def score(cand):
        st = coord_status(cand[i_lon], cand[i_lat])
        # 0 = fully valid; otherwise prefer the most specific, most populated pair
        return (0 if st["valid"] else 1, -st["filled"])

    for cand in candidates:
        st = coord_status(cand[i_lon], cand[i_lat])
        if st["valid"]:
            return cand, True

    ranked = sorted(candidates, key=score)
    # among equally ranked, prefer the defect set that is most specific on both coords
    best_rank = score(ranked[0])
    tied = [c for c in candidates if score(c) == best_rank]
    tied.sort(key=lambda c: -len(coord_status(c[i_lon], c[i_lat])["reasons"]))
    return tied[0], True


def main():
    rows, encoding = read_rows(SRC)
    header = [h.strip() for h in rows[0]]
    n_cols = len(header)
    idx = {name: i for i, name in enumerate(header)}
    missing_cols = [c for c in (LON_FIELD, LAT_FIELD) if c not in idx]
    if missing_cols:
        raise SystemExit(f"missing required columns: {missing_cols}")

    i_lon, i_lat = idx[LON_FIELD], idx[LAT_FIELD]
    i_id = idx.get(ID_FIELD)
    i_name = idx.get(NAME_FIELD)

    valid_rows, rejected_rows = [], []
    blank_rows = 0

    for n, raw in enumerate(rows[1:], start=2):  # 1-based physical line number
        if not any(str(c).strip() for c in raw):
            blank_rows += 1
            continue

        aligned, repaired = reconcile(raw, header, i_lon, i_lat, n_cols)
        record = {header[i]: (aligned[i] if i < len(aligned) else "") for i in range(n_cols)}
        st = coord_status(record[LON_FIELD], record[LAT_FIELD])

        base = {
            "row_number": n,
            "POI_ID": record.get(ID_FIELD, "") if i_id is not None else "",
            "名称": record.get(NAME_FIELD, "") if i_name is not None else "",
        }

        if st["valid"]:
            out = dict(record)
            out[LON_FIELD] = st["lon"]
            out[LAT_FIELD] = st["lat"]
            out["longitude_wgs84"] = st["lon"]
            out["latitude_wgs84"] = st["lat"]
            out["row_number"] = n
            out["field_count_repaired"] = repaired
            valid_rows.append(out)
        else:
            reasons = [c for c in REASON_PRIORITY if c in st["reasons"]]
            if repaired:
                reasons = reasons + ["field_count_mismatch"]
            rejected_rows.append({
                **base,
                "reasons": reasons,
                "reason_summary": best_reason([st]),
                "raw_longitude_wgs84": record[LON_FIELD],
                "raw_latitude_wgs84": record[LAT_FIELD],
                "field_count": len(raw),
                "expected_field_count": n_cols,
                "field_count_repaired": repaired,
                "raw_row": raw,
            })

    result = {
        "source_file": os.path.abspath(SRC),
        "encoding": encoding,
        "coordinate_fields": {"longitude": LON_FIELD, "latitude": LAT_FIELD},
        "validation_rules": {
            "longitude_range": [-180.0, 180.0],
            "latitude_range": [-90.0, 90.0],
            "reject": ["missing", "non_numeric", "out_of_range"],
        },
        "summary": {
            "total_data_rows_excluding_blank": len(valid_rows) + len(rejected_rows),
            "blank_rows_skipped": blank_rows,
            "valid_rows": len(valid_rows),
            "rejected_rows": len(rejected_rows),
        },
        "valid_rows": valid_rows,
        "rejected_rows": rejected_rows,
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(json.dumps(result["summary"], ensure_ascii=False))
    for r in rejected_rows:
        print(r["POI_ID"], r["名称"], r["raw_longitude_wgs84"], r["raw_latitude_wgs84"], r["reasons"])


if __name__ == "__main__":
    main()
