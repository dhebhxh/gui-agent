import json
import pyarrow.parquet as pq

PARQUET = "/root/autodl-tmp/mind2web_raw/data/train-00000-of-00027-4d11798d7219186d.parquet"

pf = pq.ParquetFile(PARQUET)
row = next(pf.iter_batches(batch_size=1)).to_pylist()[0]

print("=" * 60)
print("所有字段：")
print("=" * 60)
for k, v in row.items():
    print(f"\n--- {k} ---")
    print(f"  type: {type(v)}")
    if isinstance(v, dict):
        print(f"  dict keys: {list(v.keys())}")
        for kk, vv in v.items():
            print(f"    {kk}: type={type(vv)}, value={repr(vv)[:200]}")
    elif isinstance(v, list):
        print(f"  list len: {len(v)}")
        if v:
            print(f"  first item type: {type(v[0])}")
            print(f"  first item: {repr(v[0])[:500]}")
    else:
        print(f"  value: {repr(v)[:500]}")

print("\n" + "=" * 60)
print("operation 详细：")
print("=" * 60)
op = row["operation"]
print(f"type: {type(op)}")
print(f"value: {repr(op)[:500]}")
if isinstance(op, str):
    print("是字符串，尝试 json.loads：")
    try:
        parsed = json.loads(op)
        print(f"  parsed type: {type(parsed)}")
        print(f"  parsed: {parsed}")
    except Exception as e:
        print(f"  json.loads 失败: {e}")

print("\n" + "=" * 60)
print("pos_candidates 详细：")
print("=" * 60)
pcs = row["pos_candidates"]
print(f"type: {type(pcs)}")
if isinstance(pcs, str):
    print("是字符串，尝试 json.loads：")
    try:
        pcs = json.loads(pcs)
        print(f"  parsed type: {type(pcs)}")
    except Exception as e:
        print(f"  json.loads 失败: {e}")

if isinstance(pcs, list):
    print(f"list len: {len(pcs)}")
    if pcs:
        first = pcs[0]
        print(f"first item type: {type(first)}")
        print(f"first item: {repr(first)[:800]}")
        if isinstance(first, dict):
            print(f"first item keys: {list(first.keys())}")
        if isinstance(first, str):
            print("first item 是字符串，尝试 json.loads：")
            try:
                parsed = json.loads(first)
                print(f"  parsed type: {type(parsed)}")
                print(f"  parsed keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'not dict'}")
            except Exception as e:
                print(f"  json.loads 失败: {e}")

print("\n" + "=" * 60)
print("screenshot 详细：")
print("=" * 60)
shot = row["screenshot"]
print(f"type: {type(shot)}")
if isinstance(shot, dict):
    print(f"keys: {list(shot.keys())}")
    for kk, vv in shot.items():
        print(f"  {kk}: type={type(vv)}, len={len(vv) if hasattr(vv, '__len__') else 'N/A'}, preview={repr(vv)[:100]}")