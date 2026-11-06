"""Robustly parse input.csv (BOM, CRLF, quoted commas), validate WGS84 lon/lat.

Handles deliberately appended malformed rows:
  * ragged field counts (shifted columns) -> try small offsets to realign
  * missing / non-numeric / out-of-range coordinates -> rejected with reason

Writes result.json with valid_rows / rejected_rows (+ summary).
"""

import csv
import io
import json
import math
import os
import re
from pathlib import Path

LON_FIELD = "经度(WGS84)"
LAT_FIELD = "纬度(WGS84)"
LON_IDX_FALLBACK = 12
LAT_IDX_FALLBACK = 13

NUM_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
EMPTY_TOKENS = {"", "na", "n/a", "nan", "null", "none", "-", "--", "\\n"}

# offsets tried, in order, when a row has the wrong number of fields
CANDIDATE_OFFSETS = (0, -1, 1, -2, 2, -3, 3)


def _resolve_base() -> Path:
    """Locate the workspace directory that contains input.csv."""
    roots = []
    f = globals().get("__file__")
    if f:
        roots.append(Path(os.path.abspath(f)).resolve().parent)
    roots.append(Path.cwd())
    for root in roots:
        for cand in (root, root.parent, root.parent.parent):
            if (cand / "input.csv").is_file():
                return cand
    return Path.cwd()


BASE = _resolve_base()
INPUT = BASE / "input.csv"
OUTPUT = BASE / "result.json"


def read_rows(path: Path) -> list[list[str]]:
    raw = path.read_bytes()
    text = None
    for enc in ("utf-8-sig", "gb18030", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:  # pragma: no cover
        raise RuntimeError("could not decode input.csv")
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    rows = list(csv.reader(io.StringIO(text)))
    # drop fully blank records (e.g. a stray blank line appended to the file)
    return [r for r in rows if any(cell.strip() for cell in r)]


def to_float(value: object) -> float | None:
    if value is None:
        return None
    s = str(value).strip().replace("\u3000", "")
    if not s or s.lower() in EMPTY_TOKENS:
        return None
    if not NUM_RE.match(s):
        return None
    f = float(s)
    if math.isnan(f) or math.isinf(f):
        return None
    return f


def _classify(lon_raw, lat_raw) -> tuple[int, str]:
    """Return (priority, preliminary_reason). Lower priority = better realignment."""
    lon_val = to_float(lon_raw)
    lat_val = to_float(lat_raw)
    lon_empty = not str(lon_raw).strip()
    lat_empty = not str(lat_raw).strip()

    if not lon_empty and not lat_empty and lon_val is not None and lat_val is not None:
        if -180.0 <= lon_val <= 180.0 and -90.0 <= lat_val <= 90.0:
            if not (lon_val == 0.0 and lat_val == 0.0):
                return 0, ""  # fully usable pair -> prefer this alignment
        return 1, "out_of_range_coordinate"
    if not lon_empty and not lat_empty:
        return 2, "non_numeric_coordinate"
    if lon_empty and lat_empty:
        return 4, "missing_coordinate"
    return 3, "missing_coordinate"


def choose_offset(row: list[str], lon_idx: int, lat_idx: int, n_cols: int) -> int:
    """Find offset `off` so that header index h maps to row[h + off]."""
    if len(row) == n_cols:
        return 0
    best_off, best_rank = 0, None
    for off in CANDIDATE_OFFSETS:
        li, ai = lon_idx + off, lat_idx + off
        if not (0 <= li < len(row) and 0 <= ai < len(row)):
            continue
        prio, _ = _classify(row[li], row[ai])
        rank = (prio, abs(off))
        if best_rank is None or rank < best_rank:
            best_off, best_rank = off, rank
    return best_off


def main() -> None:
    rows = read_rows(INPUT)
    if not rows:
        raise RuntimeError("input.csv is empty")
    header = [h.strip().lstrip("\ufeff") for h in rows[0]]
    n_cols = len(header)
    lon_idx = header.index(LON_FIELD) if LON_FIELD in header else LON_IDX_FALLBACK
    lat_idx = header.index(LAT_FIELD) if LAT_FIELD in header else LAT_IDX_FALLBACK

    valid_rows: list[dict] = []
    rejected_rows: list[dict] = []

    for i, row in enumerate(rows[1:], start=1):
        source_line = i + 1  # 1-based line number in the original file
        off = choose_offset(row, lon_idx, lat_idx, n_cols)

        def cell(h_idx: int) -> str:
            j = h_idx + off
            return row[j].strip() if 0 <= j < len(row) else ""

        record = {header[h]: cell(h) for h in range(n_cols)}
        lon_raw = record.get(LON_FIELD, "")
        lat_raw = record.get(LAT_FIELD, "")
        lon = to_float(lon_raw)
        lat = to_float(lat_raw)
        poi_id = record.get("POI_ID") or (row[0].strip() if row else None) or None

        reason = None
        detail = ""
        if lon is None or lat is None:
            missing = [
                name
                for name, raw in ((LON_FIELD, lon_raw), (LAT_FIELD, lat_raw))
                if not str(raw).strip()
            ]
            if missing:
                reason = "missing_coordinate"
                detail = "empty value for " + ", ".join(missing)
            else:
                reason = "non_numeric_coordinate"
                bad = [
                    f"{name}={raw!r}"
                    for name, val, raw in (
                        (LON_FIELD, lon, lon_raw),
                        (LAT_FIELD, lat, lat_raw),
                    )
                    if val is None
                ]
                detail = "unparseable " + ", ".join(bad)
        elif not (-180.0 <= lon <= 180.0):
            reason = "out_of_range_coordinate"
            detail = f"longitude {lon} outside [-180, 180]"
        elif not (-90.0 <= lat <= 90.0):
            reason = "out_of_range_coordinate"
            detail = f"latitude {lat} outside [-90, 90]"
        elif lon == 0.0 and lat == 0.0:
            reason = "out_of_range_coordinate"
            detail = "null island (0, 0) is not a valid POI location"

        if reason:
            entry = {
                "source_line": source_line,
                "poi_id": poi_id,
                "reason": reason,
                "detail": detail,
                "raw_coordinate_values": {
                    LON_FIELD: lon_raw,
                    LAT_FIELD: lat_raw,
                },
                "raw_row": row,
            }
            if len(row) != n_cols:
                entry["field_count"] = len(row)
                entry["column_alignment_offset"] = off
            rejected_rows.append(entry)
            continue

        geometry = {"type": "Point", "coordinates": [lon, lat]}
        entry = {
            "source_line": source_line,
            "poi_id": poi_id,
            "name": record.get("名称", ""),
            "brand": record.get("品牌", ""),
            "type": record.get("类型", ""),
            "type_code": record.get("类型编码", ""),
            "address": record.get("地址", ""),
            "province": record.get("省", ""),
            "city": record.get("市", ""),
            "district": record.get("区县", ""),
            "business_area": record.get("商圈", ""),
            "lon_wgs84": lon,
            "lat_wgs84": lat,
            "lon_gcj02": to_float(record.get("经度(GCJ-02)")),
            "lat_gcj02": to_float(record.get("纬度(GCJ-02)")),
            "phone": record.get("电话", ""),
            "rating": to_float(record.get("评分")),
            "avg_cost": to_float(record.get("人均消费(元)")),
            "open_hours": record.get("营业时间", ""),
            "source": record.get("来源", ""),
            "data_source": record.get("数据来源", ""),
            "collect_date": record.get("采集日期", ""),
            "geometry": geometry,
        }
        if len(row) != n_cols:
            entry["field_count"] = len(row)
            entry["column_alignment_offset"] = off
        valid_rows.append(entry)

    reasons: dict[str, int] = {}
    for r in rejected_rows:
        reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1

    result = {
        "input_file": INPUT.name,
        "coordinate_columns": {"longitude": LON_FIELD, "latitude": LAT_FIELD},
        "validation_rules": {
            "longitude_range": [-180.0, 180.0],
            "latitude_range": [-90.0, 90.0],
            "missing": "empty / null-like coordinate values are rejected",
            "non_numeric": "values that fail numeric parsing are rejected",
            "out_of_range": "values outside valid WGS84 ranges are rejected",
            "ragged_rows": "wrong field counts are realigned by small column offsets",
        },
        "summary": {
            "total_data_rows": len(valid_rows) + len(rejected_rows),
            "valid_count": len(valid_rows),
            "rejected_count": len(rejected_rows),
            "rejected_by_reason": reasons,
        },
        "valid_rows": valid_rows,
        "rejected_rows": rejected_rows,
    }

    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    print(f"wrote {OUTPUT}")


main()
