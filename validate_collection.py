"""validate_collection.py — 연도별로 수집한 OECD 값과 국가별로 따로 수집한 값을 1:1 대조한다.
(KOR 시계열은 2026-10-22에 별도 질의로 받은 값. 2013 SVK 이상치 제거 전 원자료 기준으로 비교)"""
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
def read(pattern):
    rows = []
    for f in sorted(RAW.glob(pattern)):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#"):
                y, a, age, v, s = line.split("|"); rows.append((int(y), a, age, float(v)))
    return pd.DataFrame(rows, columns=["year", "area", "age", "v"]).set_index(["year", "area", "age"]).v
src = {"EARN": read("oecd_earn_rel_upper_FT_part*.txt"), "ATTAIN": read("oecd_attain_tertiary_part*.txt")}
n = mism = missing = 0; out = []
for line in (RAW / "crosscheck_by_country.txt").read_text(encoding="utf-8").splitlines():
    if not line or line.startswith("#"): continue
    ds, a, age, cells = line.split("|")
    for c in cells.split(";"):
        y, v = c.split("="); key = (int(y), a, age); n += 1
        if key not in src[ds].index: missing += 1; out.append(f"MISSING {ds} {key} check={v}"); continue
        if abs(src[ds][key] - float(v)) > 0.006: mism += 1; out.append(f"MISMATCH {ds} {key} year-sliced={src[ds][key]} by-country={v}")
print(f"대조한 값 {n}개 | 불일치 {mism}개 | 연도별 수집에 없는 값 {missing}개")
print("\n".join(out) if out else "모든 값이 소수점 둘째 자리까지 일치")
