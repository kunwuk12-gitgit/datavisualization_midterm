"""
prepare_data.py — 원자료(OECD·Gapminder)를 읽어 분석용 패널 데이터로 결합·정제한다.

입력 (data/raw/)
  oecd_earn_rel_upper_FT_part*.txt   OECD EAG: 대졸 상대임금(고졸=100), 전일제 근로자, 25-34 / 55-64세
  oecd_attain_tertiary_part*.txt     OECD EAG: 대졸자(고등교육 이수) 비율, 25-34 / 55-64세
  oecd_emp_rate_tertiary_25_34.txt   OECD EAG: 25-34세 대졸자 고용률
  gapminder/gapminder_gdp_pcap.csv   Gapminder: 1인당 GDP (PPP, 2021년 불변 국제달러)
  gapminder/gapminder_youth_unemployment.csv  Gapminder(ILOSTAT): 15-24세 실업률
  gapminder/gapminder_countries.csv  Gapminder: 국가 메타데이터(지역, World Bank 소득그룹)

출력 (data/processed/)
  panel.csv            국가×연도 패널 (OECD 회원국 + 자료가 있는 파트너국)
  oecd_average.csv     OECD가 공표한 OECD 평균(집계값) — 기준선용
  change_2014_2023.csv 국가별 2014→2023 변화량
  prep_log.md          전처리 단계별 로그(자동 생성)
"""
from pathlib import Path
import re
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

log = []
def L(msg=""):
    log.append(msg)
    print(msg)

# ---------------------------------------------------------------- 0. 국가 기준표
OECD_MEMBERS = ["AUS","AUT","BEL","CAN","CHL","COL","CRI","CZE","DNK","EST","FIN","FRA","DEU","GRC",
                "HUN","ISL","IRL","ISR","ITA","JPN","KOR","LVA","LTU","LUX","MEX","NLD","NZL","NOR",
                "POL","PRT","SVK","SVN","ESP","SWE","CHE","TUR","GBR","USA"]
AGGREGATES = ["OECD", "EU25", "G20"]
NAME_KO = {
 "AUS":"호주","AUT":"오스트리아","BEL":"벨기에","CAN":"캐나다","CHL":"칠레","COL":"콜롬비아","CRI":"코스타리카",
 "CZE":"체코","DNK":"덴마크","EST":"에스토니아","FIN":"핀란드","FRA":"프랑스","DEU":"독일","GRC":"그리스",
 "HUN":"헝가리","ISL":"아이슬란드","IRL":"아일랜드","ISR":"이스라엘","ITA":"이탈리아","JPN":"일본","KOR":"한국",
 "LVA":"라트비아","LTU":"리투아니아","LUX":"룩셈부르크","MEX":"멕시코","NLD":"네덜란드","NZL":"뉴질랜드",
 "NOR":"노르웨이","POL":"폴란드","PRT":"포르투갈","SVK":"슬로바키아","SVN":"슬로베니아","ESP":"스페인",
 "SWE":"스웨덴","CHE":"스위스","TUR":"튀르키예","GBR":"영국","USA":"미국",
 "ARG":"아르헨티나","BRA":"브라질","BGR":"불가리아","HRV":"크로아티아","PER":"페루","ROU":"루마니아",
 "ZAF":"남아프리카공화국","IDN":"인도네시아","IND":"인도","CHN":"중국",
}
REGION_KO = {"europe":"유럽", "americas":"미주", "asia":"아시아·태평양", "africa":"아프리카"}
INCOME_KO = {"high_income":"고소득", "upper_middle_income":"중상위소득",
             "lower_middle_income":"중하위소득", "low_income":"저소득"}

# ---------------------------------------------------------------- 1. OECD 원자료 파싱
def read_pipe(pattern, value_name):
    rows = []
    for f in sorted(RAW.glob(pattern)):
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#"):
                continue
            y, area, age, val, status = line.split("|")
            rows.append((int(y), area, age, float(val), status))
    df = pd.DataFrame(rows, columns=["year", "area", "age", value_name, "status"])
    return df

L("# 전처리 로그 (prepare_data.py 자동 생성)\n")
L("## 1. 원자료 읽기")
earn = read_pipe("oecd_earn_rel_upper_FT_part*.txt", "premium")
att = read_pipe("oecd_attain_tertiary_part*.txt", "attain")
L(f"- 상대임금: {len(earn)}행, 지역 {earn.area.nunique()}개, 연도 {[int(y) for y in sorted(earn.year.unique())]}")
L(f"- 대졸자 비율: {len(att)}행, 지역 {att.area.nunique()}개, 연도 {[int(y) for y in sorted(att.year.unique())]}")

emp_rows = []
for line in (RAW / "oecd_emp_rate_tertiary_25_34.txt").read_text(encoding="utf-8").splitlines():
    if not line or line.startswith("#"):
        continue
    area, *cells = line.split("|")
    for c in cells:
        m = re.match(r"(\d{4})=([\d.]+)\[(\w)\]", c)
        emp_rows.append((int(m.group(1)), area, float(m.group(2)), m.group(3)))
emp = pd.DataFrame(emp_rows, columns=["year", "area", "emp_tert_25_34", "emp_status"])
L(f"- 대졸 고용률(25-34): {len(emp)}행, 지역 {emp.area.nunique()}개")

# 1-1. 중복 점검 (연도별로 나눠 받은 데이터가 겹치지 않는지)
for name, df, keys in [("상대임금", earn, ["year","area","age"]), ("대졸자 비율", att, ["year","area","age"]),
                       ("고용률", emp, ["year","area"])]:
    d = df.duplicated(keys).sum()
    L(f"- 중복 키 점검({name}): {d}건")
    assert d == 0

# ---------------------------------------------------------------- 2. 정제 규칙
L("\n## 2. 정제")
# 2-1. 명백한 이상치: 슬로바키아 2013년 상대임금 2.97 / 3.94 (다른 해·다른 나라는 100~300 범위)
bad = (earn.area == "SVK") & (earn.year == 2013)
L(f"- [이상치 제거] 슬로바키아 2013 상대임금 {earn.loc[bad,'premium'].tolist()} → 결측 처리 "
  f"(인접 연도 2012: 144.4 / 2014: 141.4, 고졸=100 기준에서 3은 불가능한 값 → 단위·코딩 오류로 판단)")
earn = earn.loc[~bad]

# 2-2. 낮은 신뢰도 플래그(U) — 남아공 2023
u = earn.status.eq("U")
L(f"- [저신뢰 플래그] OBS_STATUS=U {u.sum()}건 ({earn.loc[u,['area','year']].values.tolist()}) → 제외")
earn = earn.loc[~u]

# 2-3. 시계열 단절(B) 플래그: OECD가 2014년부터 ISCED 2011 분류로 전환 → 이전 연도 다수에 B
for name, df in [("상대임금", earn), ("대졸자 비율", att)]:
    b = df[df.status == "B"]
    L(f"- [시계열 단절] {name} B 플래그 {len(b)}건, 연도 범위 {b.year.min()}–{b.year.max()} "
      f"→ 값은 보존하되 flag 열로 표시, 변화량 분석은 단절 이후(2014~)로 한정")
L(f"- 고용률 이상값 점검: 남아공 2024 = 35.5% (전년 66.0%) → 파트너국이라 분석 범위 밖, 패널에는 결측 처리")
emp.loc[(emp.area == "ZAF") & (emp.year == 2024), "emp_tert_25_34"] = np.nan

# ---------------------------------------------------------------- 3. long → wide
L("\n## 3. 형태 변환 (long → wide)")
def widen(df, val):
    w = df.pivot_table(index=["area", "year"], columns="age", values=val, aggfunc="first")
    w.columns = [f"{val}_{'25_34' if c=='Y25T34' else '55_64'}" for c in w.columns]
    f = df.pivot_table(index=["area", "year"], columns="age", values="status", aggfunc="first")
    f.columns = [f"{val}_flag_{'25_34' if c=='Y25T34' else '55_64'}" for c in f.columns]
    return w.join(f).reset_index()
earn_w, att_w = widen(earn, "premium"), widen(att, "attain")
oecd = (earn_w.merge(att_w, on=["area","year"], how="outer")
              .merge(emp[["area","year","emp_tert_25_34"]], on=["area","year"], how="outer"))

# 3-1. 집계값(OECD 평균 등)은 국가 패널에서 분리
agg = oecd[oecd.area.isin(AGGREGATES)].copy()
oecd = oecd[~oecd.area.isin(AGGREGATES)].copy()
L(f"- 집계 지역 {AGGREGATES} 분리 → oecd_average.csv (기준선 용도), 국가 패널 {oecd.area.nunique()}개국")

# ---------------------------------------------------------------- 4. Gapminder 결합
L("\n## 4. Gapminder 결합 (국가 코드 통일)")
gdp = pd.read_csv(RAW / "gapminder" / "gapminder_gdp_pcap.csv")
une = pd.read_csv(RAW / "gapminder" / "gapminder_youth_unemployment.csv")
meta = pd.read_csv(RAW / "gapminder" / "gapminder_countries.csv")
# Gapminder는 소문자 ISO3('kor'), 열 이름도 country/geo로 다름 → 대문자 ISO3 'area'로 통일
gdp = gdp.rename(columns={"country": "area", "time": "year", "gdp_pcap": "gdp_pcap"})
une = une.rename(columns={"geo": "area", "time": "year", "aged_15_24_unemployment_rate_percent": "youth_unemp"})
for d in (gdp, une):
    d["area"] = d["area"].str.upper()
meta = meta.rename(columns={"country": "gm_code"})
meta["area"] = meta["iso3166_1_alpha3"].str.upper()
L(f"- Gapminder 코드 소문자 → 대문자 변환, meta는 iso3166_1_alpha3 열로 매칭")
miss_meta = sorted(set(oecd.area) - set(meta.area))
L(f"- 메타데이터 미매칭 국가: {miss_meta if miss_meta else '없음'}")

panel = (oecd.merge(gdp, on=["area","year"], how="left")
             .merge(une, on=["area","year"], how="left")
             .merge(meta[["area","name","world_4region","income_groups"]], on="area", how="left"))
L(f"- 결합 후 GDP 결측 {panel.gdp_pcap.isna().sum()}행, 청년실업률 결측 {panel.youth_unemp.isna().sum()}행 "
  f"{panel.loc[panel.youth_unemp.isna(), ['area','year']].values.tolist()} (Gapminder에 해당 국가·연도 값 없음 → 결측 유지)")

panel["country"] = panel.area.map(NAME_KO)
panel["country_en"] = panel["name"]
panel["region"] = panel.world_4region.map(REGION_KO)
panel["income_group"] = panel.income_groups.map(INCOME_KO)
panel["oecd_member"] = panel.area.isin(OECD_MEMBERS)
assert panel.country.notna().all(), panel[panel.country.isna()].area.unique()

# ---------------------------------------------------------------- 5. 파생 변수
L("\n## 5. 파생 변수")
panel["premium_gap"] = panel.premium_55_64 - panel.premium_25_34
panel["premium_ratio"] = panel.premium_25_34 / panel.premium_55_64
L("- premium_gap = 55-64세 프리미엄 − 25-34세 프리미엄 (세대 격차, %p)")
L("- premium_ratio = 25-34세 / 55-64세 프리미엄")

panel = panel.drop(columns=["name","world_4region","income_groups"]).sort_values(["area","year"])
cols = ["area","country","country_en","region","income_group","oecd_member","year",
        "premium_25_34","premium_55_64","premium_gap","premium_ratio",
        "attain_25_34","attain_55_64","emp_tert_25_34","gdp_pcap","youth_unemp",
        "premium_flag_25_34","premium_flag_55_64","attain_flag_25_34","attain_flag_55_64"]
panel = panel[cols]
panel.to_csv(OUT / "panel.csv", index=False, encoding="utf-8-sig")

agg = agg[agg.area == "OECD"][["year","premium_25_34","premium_55_64","attain_25_34","attain_55_64","emp_tert_25_34"]]
agg.to_csv(OUT / "oecd_average.csv", index=False)

# ---------------------------------------------------------------- 6. 변화량 표 (2014-15 → 2022-23)
L("\n## 6. 변화량 (OECD 회원국, 25-34세)")
m = panel[panel.oecd_member]
def window_mean(lo, hi, col):
    return m[(m.year >= lo) & (m.year <= hi)].groupby("area")[col].mean()
# 기본: 시작 = 2014·2015 평균, 끝 = 2022·2023 평균
#  - 2014: ISCED 2011 전환 후 첫해(시계열 단절 이후) / 2024는 자료 국가 수가 적어(24개국) 제외
#  - 단일 연도 대신 2개 연도 평균: 한 해 결측이 있어도 포함(26→34개국), 연도별 표본 변동 완화
ch = pd.DataFrame({
    "attain_start": window_mean(2014, 2015, "attain_25_34"), "attain_end": window_mean(2022, 2023, "attain_25_34"),
    "premium_start": window_mean(2014, 2015, "premium_25_34"), "premium_end": window_mean(2022, 2023, "premium_25_34"),
}).dropna()
ch["d_attain"] = ch.attain_end - ch.attain_start
ch["d_premium"] = ch.premium_end - ch.premium_start
names = m.drop_duplicates("area").set_index("area")
ch.insert(0, "country", names.country.reindex(ch.index))
ch.insert(1, "region", names.region.reindex(ch.index))
ch.index.name = "area"
ch.reset_index().round(2).to_csv(OUT / "change_2014_2023.csv", index=False, encoding="utf-8-sig")
r_main = ch.d_attain.corr(ch.d_premium)
L(f"- 기본 정의(2014–15 평균 → 2022–23 평균): {len(ch)}개국, 상관계수 r = {r_main:.2f}, "
  f"프리미엄 하락 국가 {int((ch.d_premium < 0).sum())}개 / 상승 {int((ch.d_premium > 0).sum())}개")

# 6-1. 강건성 점검: 기간 정의를 바꿔도 결론이 같은가?
L("- 강건성 점검 (기간 정의별 대졸자 비율 변화 vs 프리미엄 변화 상관):")
L("  | 시작 | 끝 | 국가 수 | Pearson r | Spearman ρ |")
L("  |---|---|---|---|---|")
robust = []
for (a0, a1), (b0, b1) in [((2014, 2014), (2023, 2023)), ((2014, 2015), (2022, 2023)),
                           ((2014, 2016), (2021, 2023)), ((2015, 2015), (2024, 2024)), ((2014, 2014), (2024, 2024))]:
    d = pd.DataFrame({"da": window_mean(b0, b1, "attain_25_34") - window_mean(a0, a1, "attain_25_34"),
                      "dp": window_mean(b0, b1, "premium_25_34") - window_mean(a0, a1, "premium_25_34")}).dropna()
    r, rho = d.da.corr(d.dp), d.da.corr(d.dp, method="spearman")
    robust.append(dict(start=f"{a0}-{a1}", end=f"{b0}-{b1}", n=len(d), pearson=round(r, 2), spearman=round(rho, 2)))
    L(f"  | {a0}–{a1} | {b0}–{b1} | {len(d)} | {r:.2f} | {rho:.2f} |")
pd.DataFrame(robust).to_csv(OUT / "robustness_windows.csv", index=False)

# 6-2. 횡단면(같은 해) 상관과 소득 교란 점검
L("- 같은 해 횡단면 상관 (대졸자 비율 vs 프리미엄, 25-34세) 및 1인당 GDP(log)와의 상관:")
for y in [2014, 2018, 2023]:
    d = m[m.year == y].dropna(subset=["premium_25_34", "attain_25_34"])
    L(f"  - {y}: n={len(d)}, r(대졸자 비율, 프리미엄) = {d.attain_25_34.corr(d.premium_25_34):.2f}, "
      f"r(log GDP, 프리미엄) = {np.log(d.gdp_pcap).corr(d.premium_25_34):.2f}, "
      f"r(log GDP, 대졸자 비율) = {np.log(d.gdp_pcap).corr(d.attain_25_34):.2f}")

# ---------------------------------------------------------------- 7. 범위 요약
L("\n## 7. 최종 범위")
mm = panel[panel.oecd_member]
L(f"- 패널: {len(panel)}행 (국가 {panel.area.nunique()}개 × 연도 {panel.year.nunique()}개)")
L(f"- OECD 회원국 중 25-34세 프리미엄이 한 해라도 있는 나라: {mm.dropna(subset=['premium_25_34']).area.nunique()}개")
no_prem = sorted(set(OECD_MEMBERS) - set(mm.dropna(subset=['premium_25_34']).area))
L(f"- 프리미엄 자료가 전혀 없는 회원국: {[NAME_KO[x] for x in no_prem]}")
(OUT / "prep_log.md").write_text("\n".join(log), encoding="utf-8")
