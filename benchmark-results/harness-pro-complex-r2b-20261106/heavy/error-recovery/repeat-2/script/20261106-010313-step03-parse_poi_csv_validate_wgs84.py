# ─── OpenGIS Agent · run 410ab959 · step 3 · parse_poi_csv_validate_wgs84 ───
# Timestamp : 2026-11-06T01:03:13
# Semantic : parse_poi_csv_validate_wgs84
# Metadata : 20261106-010313-step03-parse_poi_csv_validate_wgs84.metadata.json
# User query: input.csv contains deliberately appended malformed rows. Parse it robustly using the WGS84 longitude/latitude columns. Reject rows whose coordinates are missing, non-numeric, or outside valid ranges. …
import csv, json, math, re, unicodedata

SRC = 'input.csv'
OUT = 'result.json'

def norm(s):
    s = unicodedata.normalize('NFKC', s or '')
    return re.sub(r'\s+', '', s)

with open(SRC, 'rb') as fh:
    raw = fh.read()
text = raw.decode('utf-8-sig', errors='replace')
reader = csv.reader(text.splitlines(), delimiter=',')
rows = list(reader)
header = [norm(h) for h in rows[0]]

def find_col(pred):
    for i, h in enumerate(header):
        if pred(h):
            return i
    return None

lon_idx = find_col(lambda h: 'WGS84' in h.upper() and ('经度' in h or 'lon' in h.lower()))
lat_idx = find_col(lambda h: 'WGS84' in h.upper() and ('纬度' in h or 'lat' in h.lower()))
if lon_idx is None or lat_idx is None:
    lon_idx = find_col(lambda h: h.upper() in ('LONGITUDE','LON','LNG','经度'))
    lat_idx = find_col(lambda h: h.upper() in ('LATITUDE','LAT','纬度'))
if lon_idx is None or lat_idx is None:
    raise SystemExit('cannot locate WGS84 longitude/latitude columns: %s' % header)

poi_idx = find_col(lambda h: h.upper() in ('POI_ID','ID','POIID'))
name_idx = find_col(lambda h: h in ('名称','NAME','NAME_CN'))

def parse_num(v):
    s = (v or '').strip()
    if s == '' or s.lower() in ('na','n/a','null','none','nan','-','--'):
        return None, 'missing'
    s2 = s.replace('°', '').replace(',', '')
    try:
        x = float(s2)
    except (TypeError, ValueError):
        return None, 'non_numeric'
    if not math.isfinite(x):
        return None, 'non_numeric'
    return x, None

valid, rejected = [], []
blank_lines = 0

for i, row in enumerate(rows[1:], start=1):
    line_no = i + 1
    if not any((c or '').strip() for c in row):
        blank_lines += 1
        continue
    issues = []
    if len(row) != len(header):
        issues.append('field_count_mismatch:%d!=%d' % (len(row), len(header)))
    rec = {}
    for j, h in enumerate(header):
        rec[h] = row[j] if j < len(row) else ''
    lon_raw = row[lon_idx].strip() if lon_idx < len(row) else ''
    lat_raw = row[lat_idx].strip() if lat_idx < len(row) else ''
    lon, lon_err = parse_num(lon_raw)
    lat, lat_err = parse_num(lat_raw)
    malformed = any(x.startswith('field_count_mismatch') for x in issues)

    defects = []
    if lon_err == 'non_numeric' or lat_err == 'non_numeric':
        defects.append('non_numeric_coordinate')
    if not lon_err and not (-180.0 <= lon <= 180.0):
        defects.append('out_of_range_longitude')
    if not lat_err and not (-90.0 <= lat <= 90.0):
        defects.append('out_of_range_latitude')
    if lon_err == 'missing' or lat_err == 'missing':
        defects.append('missing_coordinate')

    # Rows with the wrong field count are shifted: any coordinate-block value may
    # sit in the wrong column, so validate every value found in the block.
    block_detail = {'longitude_raw': lon_raw, 'latitude_raw': lat_raw}
    if malformed:
        extra_defects = []
        for j, h in enumerate(header):
            if not any(k in h for k in ('经度', '纬度', 'LON', 'LAT')):
                continue
            v = row[j].strip() if j < len(row) else ''
            block_detail[h + '@' + str(j)] = v
            if v == '':
                continue
            num, err = parse_num(v)
            if err == 'non_numeric':
                extra_defects.append('non_numeric_coordinate')
            elif num is not None and '纬度' in h and not (-90.0 <= num <= 90.0):
                extra_defects.append('out_of_range_latitude')
            elif num is not None and '经度' in h and not (-180.0 <= num <= 180.0):
                extra_defects.append('out_of_range_longitude')
        defects = extra_defects + defects

    priority = ['non_numeric_coordinate', 'out_of_range_longitude',
                'out_of_range_latitude', 'missing_coordinate',
                'malformed_row_structure']
    if malformed:
        defects.append('malformed_row_structure')
    reason = next((p for p in priority if p in defects), None)
    detail = None
    if reason:
        detail = dict(block_detail)
        detail['defects'] = defects
        detail['fields_found'] = len(row)
        detail['fields_expected'] = len(header)

    if reason:
        entry = {'row_number': line_no,
                 'poi_id': rec.get(header[poi_idx], '') if poi_idx is not None else '',
                 'name': rec.get(header[name_idx], '') if name_idx is not None else '',
                 'reason': reason,
                 'issues': issues or [reason]}
        if detail:
            entry['detail'] = detail
        entry['raw_row'] = row
        rejected.append(entry)
        continue

    props = dict(rec)
    valid.append({
        'row_number': line_no,
        'poi_id': rec.get(header[poi_idx], '') if poi_idx is not None else '',
        'name': rec.get(header[name_idx], '') if name_idx is not None else '',
        'longitude': lon,
        'latitude': lat,
        'properties': props,
    })

reason_counts = {}
for r in rejected:
    reason_counts[r['reason']] = reason_counts.get(r['reason'], 0) + 1

result = {
    'source_file': SRC,
    'coordinate_columns': {'longitude': header[lon_idx], 'latitude': header[lat_idx],
                           'crs': 'WGS84', 'index_longitude': lon_idx, 'index_latitude': lat_idx},
    'validation_rules': {
        'longitude_range': [-180.0, 180.0],
        'latitude_range': [-90.0, 90.0],
        'reject_if': ['missing', 'non_numeric', 'out_of_range', 'malformed_row_structure'],
    },
    'summary': {
        'header_columns': len(header),
        'data_lines_read': len(rows) - 1 - blank_lines,
        'valid_count': len(valid),
        'rejected_count': len(rejected),
        'blank_lines_skipped': blank_lines,
        'rejected_by_reason': reason_counts,
    },
    'valid_rows': valid,
    'rejected_rows': rejected,
}

with open(OUT, 'w', encoding='utf-8') as fh:
    json.dump(result, fh, ensure_ascii=False, indent=2)

print(json.dumps(result['summary'], ensure_ascii=False, indent=2))
print('lon col:', header[lon_idx], lon_idx, '| lat col:', header[lat_idx], lat_idx)
for r in rejected:
    print(r['row_number'], r['poi_id'], r['name'], r['reason'], r['issues'], r.get('detail'))

# ─── Observations ───
# {
#   "header_columns": 21,
#   "data_lines_read": 1657,
#   "valid_count": 1654,
#   "rejected_count": 3,
#   "blank_lines_skipped": 1,
#   "rejected_by_reason": {
#     "missing_coordinate": 3
#   }
# }
# lon col: 经度(WGS84) 12 | lat col: 纬度(WGS84) 13
# 1657 BROKEN-1 损坏数据 missing_coordinate ['field_count_mismatch:22!=21'] {'longitude_raw': '31.5', 'latitude_raw': ''}
# 1658 BROKEN-2 缺失经度 missing_coordinate ['field_count_mismatch:22!=21'] {'longitude_raw': '31.5', 'latitude_raw': ''}
# 1659 BROKEN-3 超出范围 missing_coordinate ['field_count_mismatch:22!=21'] {'longitude_raw': '999', 'latitude_raw': ''}
