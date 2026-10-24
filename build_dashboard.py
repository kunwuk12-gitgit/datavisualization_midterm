"""
build_dashboard.py — Part A 탐색용 대시보드 (안내형 구성)

구성 (위에서 아래로 읽는 질문 순서)
  컨트롤  ① 국가  ② 비교 국가  ③ 연도  ④ 연령대
  결론 문장 (선택에 따라 다시 쓰임) + 색 범례 (선택 = 파랑, 비교 = 주황, OECD 평균·기타 = 회색)
  1. 어디에 서 있나?        KPI 카드 4개 (값 · 비교국 · OECD 평균 · OECD 내 순위)        [HTML, JS 계산]
  2. 2014년 이후 얼마나 변했나?  기준연도 대비 변화 선 그래프 + 변화표                 [Vega-Lite + HTML]
  3. 대졸자 비율로 설명되나?   산점도 + 추세선 + "추세보다 몇 높/낮다"                  [Vega-Lite]
  4. 부모 세대와 비교하면?    덤벨 차트 (25–34세 ● / 55–64세 ○)                       [Vega-Lite]
  5. 세 가지 요점             숫자가 들어간 동적 요약                                   [HTML, JS 계산]
차트는 Altair로 만든 Vega-Lite 스펙이며, 컨트롤 값은 JS가 각 차트의 신호(sel, cmp, year, age …)에 넣는다.
출력: site/dashboard/index.html, site/artifact_dashboard.html
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import altair as alt

ROOT = Path(__file__).resolve().parent
P = ROOT / "data" / "processed"
SITE = ROOT / "site" / "dashboard"; SITE.mkdir(parents=True, exist_ok=True)

SEL, CMP = "#2a78d6", "#eb6834"                  # 선택 국가 / 비교 국가 (검증 팔레트)
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
OTHER, OTHER_LINE = "#c9c8c0", "#e3e2dc"
FONT = "IBM Plex Sans KR, Apple SD Gothic Neo, Noto Sans KR, Noto Sans CJK KR, Malgun Gothic, sans-serif"

panel = pd.read_csv(P / "panel.csv")
avg = pd.read_csv(P / "oecd_average.csv")
ch = pd.read_csv(P / "change_2014_2023.csv")
m = panel[panel.oecd_member & (panel.year >= 2010)].copy()
m = m[m.area.isin(m.dropna(subset=["premium_25_34"]).area.unique())]   # 임금 자료가 있는 36개국

# ---------------------------------------------------------------- 데이터 (짧은 열 이름으로 페이지에 내장)
def base_change(df, col, key="area"):
    """기준연도(2014, 없으면 2015) 대비 변화량"""
    out = pd.Series(np.nan, index=df.index)
    for k, g in df.groupby(key):
        b = g.loc[g.year == 2014, col].dropna()
        if b.empty: b = g.loc[g.year == 2015, col].dropna()
        if b.empty: continue
        out.loc[g.index] = g[col] - b.iloc[0]
    return out

R = pd.DataFrame({
    "area": m.area, "c": m.country, "year": m.year,
    "py": m.premium_25_34, "po": m.premium_55_64, "ay": m.attain_25_34, "ao": m.attain_55_64,
    "emp": m.emp_tert_25_34, "gdp": m.gdp_pcap / 1000, "un": m.youth_unemp,
    "fy": m.premium_flag_25_34.fillna(""), "fo": m.premium_flag_55_64.fillna(""),
})
R["dpy"] = base_change(R, "py"); R["dpo"] = base_change(R, "po")
A = avg[avg.year >= 2010].rename(columns={"premium_25_34": "py", "premium_55_64": "po", "attain_25_34": "ay",
                                         "attain_55_64": "ao", "emp_tert_25_34": "emp"}).copy()
A["area"] = "OECD"; A["c"] = "OECD 평균"
A["dpy"] = base_change(A, "py"); A["dpo"] = base_change(A, "po")
num = ["py", "po", "ay", "ao", "emp", "gdp", "un", "dpy", "dpo"]
R[num] = R[num].round(2); A[[c for c in num if c in A]] = A[[c for c in num if c in A]].round(2)
LINES = pd.concat([R[["area", "c", "year", "py", "po", "dpy", "dpo"]], A[["area", "c", "year", "py", "po", "dpy", "dpo"]]])

# ---------------------------------------------------------------- 신호 (값은 JS가 넣음; 여기서는 기본값)
sel = alt.param(name="sel", value="KOR"); cmp = alt.param(name="cmp", value="CAN")
selName = alt.param(name="selName", value="한국"); cmpName = alt.param(name="cmpName", value="캐나다")
year = alt.param(name="year", value=2023); age = alt.param(name="age", value="25_34")
ROLE = ("datum.area == sel ? 'sel' : datum.area == cmp ? 'cmp' : datum.area == 'OECD' ? 'oecd' : 'other'")
role_color = alt.Color("role:N", scale=alt.Scale(domain=["sel", "cmp", "oecd", "other"],
                                                 range=[SEL, CMP, INK2, OTHER]), legend=None)
def cfg(c):
    return (c.configure(font=FONT, background="transparent").configure_view(stroke=None)
             .configure_axis(labelFontSize=11.5, titleFontSize=11.5, titleFontWeight="normal", labelColor=INK2,
                             titleColor=INK2, gridColor="#ecebe6", domainColor="#c3c2b7", tickColor="#c3c2b7"))

# ---------------------------------------------------------------- 2. 기준연도 대비 변화 (선)
XS = alt.Scale(domain=[2014, 2024.9])
x2 = alt.X("year:Q", title=None, scale=XS, axis=alt.Axis(format="d", values=list(range(2014, 2025, 2))))
ln = (alt.Chart(LINES).transform_calculate(v="age == '25_34' ? datum.dpy : datum.dpo", lv="age == '25_34' ? datum.py : datum.po",
                                           role=ROLE)
      .transform_filter("datum.year >= 2014 && isValid(datum.v)"))
YS2 = alt.Scale(domain=[-45, 35], nice=False, zero=False)
y2 = alt.Y("v:Q", title="2014년 대비 프리미엄 변화 (포인트)", scale=YS2)
tipL = [alt.Tooltip("c:N", title="국가"), alt.Tooltip("year:O", title="연도"),
        alt.Tooltip("lv:Q", title="프리미엄", format=".1f"), alt.Tooltip("v:Q", title="2014년 대비", format="+.1f")]
zero = alt.Chart(pd.DataFrame({"z": [0]})).mark_rule(color="#a8a79f", strokeWidth=1).encode(y=alt.Y("z:Q", scale=YS2))
others = ln.transform_filter("datum.role == 'other'").mark_line(strokeWidth=1, color=OTHER_LINE, clip=True).encode(x=x2, y=y2, detail="area:N")
oecdl = ln.transform_filter("datum.role == 'oecd'").mark_line(strokeWidth=2, color=INK2, strokeDash=[5, 4]).encode(x=x2, y=y2)
main = ln.transform_filter("datum.role == 'sel' || datum.role == 'cmp'")
main_l = main.mark_line(strokeWidth=3, clip=True).encode(x=x2, y=y2, color=role_color, detail="area:N")
main_p = main.mark_circle(size=55, opacity=1).encode(x=x2, y=y2, color=role_color, tooltip=tipL)
endlab = (ln.transform_filter("datum.role == 'sel' || datum.role == 'cmp'")
          .transform_joinaggregate(last="max(year)", groupby=["area"]).transform_filter("datum.year == datum.last")
          .mark_text(align="left", dx=7, fontSize=12, fontWeight="bold").encode(x=x2, y=y2, text="c:N", color=role_color))
yr = (alt.Chart(pd.DataFrame({"k": [0]})).transform_calculate(yr="year", t="year + '년'"))
yrule = yr.mark_rule(color=MUTED, strokeWidth=1, strokeDash=[2, 3]).encode(x=alt.X("yr:Q", scale=XS))
ylab = yr.mark_text(align="left", baseline="top", dx=4, fontSize=11, color=MUTED).encode(x=alt.X("yr:Q", scale=XS), y=alt.value(2), text="t:N")
chart_lines = alt.layer(zero, others, oecdl, yrule, ylab, main_l, main_p, endlab).add_params(sel, cmp, year, age).properties(width=470, height=280)

# ---------------------------------------------------------------- 3. 산점도: 대졸자 비율 × 프리미엄
sc = (alt.Chart(R).transform_filter("datum.year == year")
      .transform_calculate(x="age == '25_34' ? datum.ay : datum.ao", y="age == '25_34' ? datum.py : datum.po", role=ROLE)
      .transform_filter("isValid(datum.x) && isValid(datum.y)"))
XS3 = alt.Scale(domain=[0, 80], nice=False); YS3 = alt.Scale(zero=False, nice=True)   # 세로축은 선택 연도·연령의 값 범위에 맞춤
x3 = alt.X("x:Q", title="대졸자 비율 (선택 연령대, %)", scale=XS3); y3 = alt.Y("y:Q", title="대졸 임금 프리미엄 (고졸 = 100)", scale=YS3)
tip3 = [alt.Tooltip("c:N", title="국가"), alt.Tooltip("y:Q", title="프리미엄", format=".1f"), alt.Tooltip("x:Q", title="대졸자 비율 %", format=".1f"),
        alt.Tooltip("emp:Q", title="25–34세 대졸 고용률 %", format=".1f"), alt.Tooltip("gdp:Q", title="1인당 GDP (천$)", format=".1f")]
reg = sc.transform_regression("x", "y").mark_line(color="#7d8f86", strokeWidth=2).encode(x=x3, y=y3)
av = (alt.Chart(A).transform_filter("datum.year == year")
      .transform_calculate(x="age == '25_34' ? datum.ay : datum.ao", y="age == '25_34' ? datum.py : datum.po"))
av_h = av.mark_rule(color=INK2, strokeDash=[5, 4], strokeWidth=1).encode(y=alt.Y("y:Q", scale=YS3))
av_v = av.mark_rule(color=INK2, strokeDash=[5, 4], strokeWidth=1, opacity=0.5).encode(x=alt.X("x:Q", scale=XS3))
av_t = av.mark_text(align="left", baseline="bottom", dy=-3, fontSize=11, color=INK2).encode(y=alt.Y("y:Q", scale=YS3), x=alt.value(4), text=alt.value("OECD 평균"))
dots = sc.transform_filter("datum.role == 'other'").mark_circle(size=70, opacity=1, color=OTHER, stroke="#fcfcfb", strokeWidth=1.2, cursor="pointer").encode(x=x3, y=y3, tooltip=tip3)
hi = sc.transform_filter("datum.role != 'other'")
hi_d = hi.mark_circle(size=170, opacity=1, stroke="#fcfcfb", strokeWidth=2, cursor="pointer").encode(x=x3, y=y3, color=role_color, tooltip=tip3)
hi_t = alt.layer(   # 선택 국가 라벨은 점 위, 비교 국가 라벨은 점 아래 → 두 점이 가까워도 겹치지 않게
    hi.transform_filter("datum.role == 'sel'").mark_text(align="left", dx=11, dy=-11, fontSize=13, fontWeight="bold").encode(x=x3, y=y3, text="c:N", color=role_color),
    hi.transform_filter("datum.role == 'cmp'").mark_text(align="left", dx=11, dy=14, fontSize=13, fontWeight="bold").encode(x=x3, y=y3, text="c:N", color=role_color))
r2 = (sc.transform_regression("x", "y", params=True).transform_calculate(t="'추세선 R² = ' + format(datum.rSquared, '.2f')")
      .mark_text(align="right", baseline="top", fontSize=11.5, color="#5f7168").encode(x=alt.value(466), y=alt.value(4), text="t:N"))
chart_scatter = alt.layer(av_v, av_h, av_t, reg, dots, hi_d, hi_t, r2).add_params(sel, cmp, year, age).properties(width=470, height=380)

# ---------------------------------------------------------------- 4. 덤벨: 세대 비교
db = (alt.Chart(R).transform_filter("datum.year == year && isValid(datum.py) && isValid(datum.po)")
      .transform_calculate(role=ROLE, sortval="age == '25_34' ? datum.py : datum.po"))
yb = alt.Y("c:N", title=None, sort=alt.EncodingSortField(field="sortval", op="max", order="descending"),
           axis=alt.Axis(ticks=False, domain=False, labelPadding=6, labelFontSize=11.5,
                         labelColor=alt.ExprRef(f"datum.value == selName ? '{SEL}' : datum.value == cmpName ? '{CMP}' : '{INK2}'"),
                         labelFontWeight=alt.ExprRef("datum.value == selName || datum.value == cmpName ? 'bold' : 'normal'")))
XB = alt.Scale(zero=False, nice=True)
tipB = [alt.Tooltip("c:N", title="국가"), alt.Tooltip("py:Q", title="25–34세", format=".1f"),
        alt.Tooltip("po:Q", title="55–64세", format=".1f")]
rule = db.mark_rule(strokeWidth=2.5).encode(y=yb, x=alt.X("py:Q", scale=XB, title="대졸 임금 프리미엄 (고졸 = 100)"), x2="po:Q",
                                            color=alt.condition("datum.role == 'other'", alt.value(OTHER_LINE), alt.value(INK2)),
                                            opacity=alt.condition("datum.role == 'other'", alt.value(1), alt.value(0.45)))
young = db.mark_circle(size=62, opacity=1, cursor="pointer").encode(y=yb, x=alt.X("py:Q", scale=XB), color=role_color, tooltip=tipB)
old = db.mark_point(size=62, filled=False, strokeWidth=2, opacity=1, cursor="pointer").encode(y=yb, x=alt.X("po:Q", scale=XB), color=role_color, tooltip=tipB)
chart_db = (alt.layer(rule, young, old).add_params(sel, cmp, selName, cmpName, year, age)
            .properties(width=330, height=alt.Step(13.5)))

specs = {k: cfg(c).to_dict() for k, c in {"lines": chart_lines, "scatter": chart_scatter, "db": chart_db}.items()}

# ---------------------------------------------------------------- 페이지에 넘길 데이터
facts = json.loads((P / "story_facts.json").read_text(encoding="utf-8"))
DATA = {
    "rows": R.astype(object).where(pd.notna(R), None).to_dict(orient="records"),
    "avg": A[["year", "py", "po", "ay", "ao", "emp", "dpy", "dpo"]].astype(object).where(pd.notna(A[["year", "py", "po", "ay", "ao", "emp", "dpy", "dpo"]]), None).to_dict(orient="records"),
    "names": R.drop_duplicates("area").sort_values("c").set_index("area").c.to_dict(),
    "change": {"r": facts["r_ch"], "n": facts["n_ch"], "down": facts["n_down"], "up": facts["n_up"]},
}
tpl = (ROOT / "templates" / "dashboard_template.html").read_text(encoding="utf-8")
body = (tpl.replace("/*__SPECS__*/null", json.dumps(specs, ensure_ascii=False))
           .replace("/*__DATA__*/null", json.dumps(DATA, ensure_ascii=False)))
full = ('<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '</head>\n<body>\n' + body + '\n</body>\n</html>\n')
(SITE / "index.html").write_text(full, encoding="utf-8")
(ROOT / "site" / "artifact_dashboard.html").write_text(body, encoding="utf-8")
(SITE / "dashboard_spec.json").unlink(missing_ok=True)
print("wrote", SITE / "index.html", f"{len(full)/1024:.0f} KB; countries", R.area.nunique())
