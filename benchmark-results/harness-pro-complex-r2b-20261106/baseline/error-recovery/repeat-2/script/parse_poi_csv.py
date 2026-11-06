"""Robust CSV parsing + WGS84 coordinate validation for POI data.

Reads input.csv (UTF-8 with BOM, quoted fields, possibly misaligned rows),
validates the 经度(WGS84) / 纬度(WGS84) columns, and writes result.json with
`valid_rows` and `rejected_rows`.
"""

import csv
import io
import json
import math
from pathlib import Path

BASE = Path.cwd()
INPUT_CSV = BASE / "input.csv"
OUTPUT_JSON = BASE / "result.json"

LON_COL = "经度(WGS84)"
LAT_COL = "纬度(WGS84)"


def to_number(value):
    text = (value or "").strip()
    if text == "":
        return None
    try:
        num = float(text)
    except ValueError:
        return None
    if not math.isfinite(num):
        return None
    return num


def classify(value, low, high):
    """Return (issue, parsed_value); issue is 'ok' | 'missing' | 'non_numeric' | 'out_of_range'."""
    text = (value or "").strip()
    if text == "":
        return "missing", None
    num = to_number(text)
    if num is None:
        return "non_numeric", None
    if not (low <= num <= high):
        return "out_of_range", num
    return "ok", num


def read_rows(path):
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    return list(csv.reader(io.StringIO(raw), strict=False))


def main():
    rows = read_rows(INPUT_CSV)
    header = [h.strip() for h in rows[0]]
    n_cols = len(header)
    lon_idx = header.index(LON_COL)
    lat_idx = header.index(LAT_COL)

    valid_rows = []
    rejected_rows = []
    blank_lines = 0

    for offset, row in enumerate(rows[1:], start=2):  # 1-based line number in file
        if all(str(cell).strip() == "" for cell in row):
            blank_lines += 1
            continue

        record = {header[i]: (row[i].strip() if i < len(row) else "") for i in range(n_cols)}
        poi_id = record.get("POI_ID", "")
        name = record.get("名称", "")

        aligned = len(row) == n_cols
        if aligned:
            lon_issue, lon_val = classify(row[lon_idx], -180.0, 180.0)
            lat_issue, lat_val = classify(row[lat_idx], -90.0, 90.0)
            issues = [i for i in (lon_issue, lat_issue) if i != "ok"]
            reason_parts = []
            if lon_issue != "ok":
                reason_parts.append(f"{lon_issue}_longitude")
            if lat_issue != "ok":
                reason_parts.append(f"{lat_issue}_latitude")
            reason = "; ".join(reason_parts)
            detail = {
                "longitude_raw": row[lon_idx],
                "latitude_raw": row[lat_idx],
            }
        else:
            # Structurally misaligned row (field count != header count): recover the
            # coordinate tokens from the coordinate region and evaluate them in order.
            tokens = [c.strip() for c in row[len(header) - 11:] if c.strip() != ""]
            lon_raw = tokens[0] if len(tokens) > 0 else ""
            lat_raw = tokens[1] if len(tokens) > 1 else ""
            lon_issue, lon_val = classify(lon_raw, -180.0, 180.0)
            lat_issue, lat_val = classify(lat_raw, -90.0, 90.0)
            # A structurally broken row is always rejected, even if the tokens look fine.
            priority = ["non_numeric", "out_of_range", "missing"]
            issues = [i for i in (lon_issue, lat_issue) if i != "ok"] or ["malformed_row"]
            primary = next((p for p in priority if any(i.startswith(p) for i in issues)), "malformed_row")
            suffix = []
            if any(i.endswith("longitude") for i in issues) or primary != "malformed_row":
                if lon_issue != "ok":
                    suffix.append("longitude")
            if lat_issue != "ok":
                suffix.append("latitude")
            if primary == "malformed_row":
                reason = f"malformed_row_field_count_{len(row)}_vs_{n_cols}"
            else:
                reason = f"{primary}_{'_and_'.join(suffix)}"
            detail = {
                "note": f"field count {len(row)} != header {n_cols}",
                "longitude_raw": lon_raw,
                "latitude_raw": lat_raw,
            }

        if not issues:
            valid_rows.append(
                {
                    "row_number": offset,
                    **record,
                    "wgs84_lon": lon_val,
                    "wgs84_lat": lat_val,
                }
            )
        else:
            rejected_rows.append(
                {
                    "row_number": offset,
                    "poi_id": poi_id,
                    "name": name,
                    "reason": reason,
                    "issues": issues if aligned else list(dict.fromkeys(issues)),
                    **detail,
                    "raw_row": ",".join(row),
                }
            )

    result = {
        "summary": {
            "input_file": str(INPUT_CSV.name),
            "coordinate_columns": {"longitude": LON_COL, "latitude": LAT_COL},
            "valid_range": {"longitude": [-180.0, 180.0], "latitude": [-90.0, 90.0]},
            "total_data_rows": len(valid_rows) + len(rejected_rows),
            "valid_count": len(valid_rows),
            "rejected_count": len(rejected_rows),
            "blank_lines_skipped": blank_lines,
            "rejection_reasons": {
                r["reason"]: sum(1 for x in rejected_rows if x["reason"] == r["reason"])
                for r in rejected_rows
            },
        },
        "valid_rows": valid_rows,
        "rejected_rows": rejected_rows,
    }

    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


res = main()
print(json.dumps(res["summary"], ensure_ascii=False, indent=2))
print("\nrejected rows:")
for r in res["rejected_rows"]:
    print(f"  line {r['row_number']} | {r['poi_id']} | {r['reason']} | issues={r['issues']}")
print("\nfirst valid row:", json.dumps(res["valid_rows"][0], ensure_ascii=False)[:400])
