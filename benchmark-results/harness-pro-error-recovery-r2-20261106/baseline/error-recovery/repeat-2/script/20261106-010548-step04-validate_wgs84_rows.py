# ─── OpenGIS Agent · run aff6073b · step 4 · validate_wgs84_rows ───
# Timestamp : 2026-11-06T01:05:48
# Semantic : validate_wgs84_rows
# Metadata : 20261106-010548-step04-validate_wgs84_rows.metadata.json
# User query: input.csv contains deliberately appended malformed rows. Parse it robustly using the WGS84 longitude/latitude columns. Reject rows whose coordinates are missing, non-numeric, or outside valid ranges. …
import csv
import json
import math

INPUT = "input.csv"
OUTPUT = "result.json"


def _is_number(s):
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v):
        return None
    return v


def count_coords(csv_path=INPUT):
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            header = [h.strip() for h in next(reader)]
        except StopIteration:
            return 0, 0
        i_lon = i_lat = None
        for i, h in enumerate(header):
            if "经度" in h and "WGS84" in h.upper():
                i_lon = i
            if "纬度" in h and "WGS84" in h.upper():
                i_lat = i
        if i_lon is None or i_lat is None:
            raise ValueError("WGS84 longitude/latitude columns not found in header")

        valid = rejected = 0
        for row in reader:
            if not row or all(not c.strip() for c in row):
                continue
            if len(row) <= max(i_lon, i_lat):
                rejected += 1
                continue
            lon = _is_number(row[i_lon].strip())
            lat = _is_number(row[i_lat].strip())
            if lon is None or lat is None:
                rejected += 1
            elif not (-180.0 <= lon <= 180.0) or not (-90.0 <= lat <= 90.0):
                rejected += 1
            else:
                valid += 1
    return valid, rejected


valid_rows, rejected_rows = count_coords()
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump({"valid_rows": valid_rows, "rejected_rows": rejected_rows}, f)

# ─── Observations ───
# (no output)
