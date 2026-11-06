"""Robust CSV parser: validate WGS84 lon/lat, split valid vs rejected rows.

Reads input.csv (UTF-8 with BOM, quoted commas, malformed trailing rows),
validates the WGS84 coordinate columns, and writes result.json with
`valid_rows` and `rejected_rows` (each rejection carries a reason).
"""

import csv
import json
import math
import os

CSV_PATH = "input.csv"
OUT_PATH = "result.json"
LON_COL = "经度(WGS84)"
LAT_COL = "纬度(WGS84)"

FULLWIDTH_SPACES = "\u3000\xa0"


def clean(value):
    """Strip whitespace incl. BOM/NBSP/full-width spaces; None stays None."""
    if value is None:
        return ""
    return value.replace("\ufeff", "").strip().strip(FULLWIDTH_SPACES).strip()


def parse_coord(raw, lo, hi, axis):
    """Return (value, None) on success or (None, reason) on failure."""
    text = clean(raw)
    if text == "" or text.lower() in {"na", "n/a", "null", "none", "nan", "无"}:
        return None, f"missing_{axis}"
    try:
        value = float(text)
    except (TypeError, ValueError):
        return None, f"non_numeric_{axis}"
    if not math.isfinite(value):
        return None, f"non_finite_{axis}"
    if value < lo or value > hi:
        return None, f"out_of_range_{axis}"
    return value, None


def main():
    with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh)
        raw_header = next(reader)
        header = [clean(h) for h in raw_header]

        lon_idx = header.index(LON_COL)
        lat_idx = header.index(LAT_COL)

        valid_rows, rejected_rows = [], []
        blank_rows = 0

        for row_number, row in enumerate(reader, start=2):
            if not any(clean(cell) for cell in row):
                blank_rows += 1
                continue

            padded = list(row) + [""] * (len(header) - len(row))
            record = dict(zip(header, padded))
            reasons = []

            if len(row) != len(header):
                reasons.append(f"malformed_field_count:{len(row)}!={len(header)}")

            lon, lon_err = parse_coord(row[lon_idx] if lon_idx < len(row) else "",
                                       -180.0, 180.0, "longitude")
            lat, lat_err = parse_coord(row[lat_idx] if lat_idx < len(row) else "",
                                       -90.0, 90.0, "latitude")
            reasons.extend(e for e in (lon_err, lat_err) if e)

            if reasons:
                rejected_rows.append(
                    {
                        "row_number": row_number,
                        "POI_ID": clean(record.get("POI_ID", "")),
                        "name": clean(record.get("名称", "")),
                        "raw_longitude": clean(padded[lon_idx] if lon_idx < len(padded) else ""),
                        "raw_latitude": clean(padded[lat_idx] if lat_idx < len(padded) else ""),
                        "reason": "; ".join(reasons),
                        "raw_row": row,
                    }
                )
            else:
                out = {key: clean(value) for key, value in record.items()}
                out["lon_wgs84"] = lon
                out["lat_wgs84"] = lat
                valid_rows.append(out)

    result = {
        "source_file": os.path.abspath(CSV_PATH),
        "coordinate_columns": {"longitude": LON_COL, "latitude": LAT_COL},
        "crs": "WGS84 / EPSG:4326",
        "valid_row_count": len(valid_rows),
        "rejected_row_count": len(rejected_rows),
        "blank_row_count": blank_rows,
        "valid_rows": valid_rows,
        "rejected_rows": rejected_rows,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)

    print("valid:", len(valid_rows), "rejected:", len(rejected_rows), "blank:", blank_rows)
    for item in rejected_rows:
        print(item["row_number"], item["POI_ID"], "->", item["reason"])


if __name__ == "__main__":
    main()
