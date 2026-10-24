"""
build_story.py — Part B 설명용 시각화 (고정 화면, 메시지 1개 + 근거 차트 3개)

핵심 메시지
  "대졸자가 늘어난 나라에서 졸업장 값이 더 떨어진 것은 아니었다.
   한국 청년의 낮은 대졸 프리미엄은 '대졸자가 너무 많아서'만으로는 설명되지 않는다."
읽는 순서
  ① 통념의 근거: 2023년 한 해 단면 — 대졸자 많은 나라일수록 프리미엄이 낮아 '보인다'
  ② 변화로 검증: 2014–15 → 2022–23 변화량 — 대졸자 증가 폭과 프리미엄 변화는 무관
  ③ 한국 사례: 2014년 이후 대졸자 비율은 정체, 프리미엄은 계속 하락
출력: site/story/index.html, site/artifact_story.html
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import altair as alt

ROOT = Path(__file__).resolve().parent
P = ROOT / "data" / "processed"
SITE = ROOT / "site" / "story"; SITE.mkdir(parents=True, exist_ok=True)

BLUE, INK, INK2, MUTED = "#2a78d6", "#0b0b0b", "#52514e", "#898781"
UP, DOWN = "#1baf7a", "#eb6834"   # ②: 프리미엄 상승 / 하락 (검증 팔레트, 라벨 병기)
GRAY_PT, GRAY_LINE = "#c9c8c0", "#dedcd4"
FONT = "IBM Plex Sans KR, Apple SD Gothic Neo, Noto Sans KR, Noto Sans CJK KR, Malgun Gothic, sans-serif"

panel = pd.read_csv(P / "panel.csv")
avg = pd.read_csv(P / "oecd_average.csv")
ch = pd.read_csv(P / "change_2014_2023.csv")
rob = pd.read_csv(P / "robustness_windows.csv")
m = panel[panel.oecd_member]

# ---------------------------------------------------------------- 수치 (주석 문구는 데이터에서 계산)
Y = 2023
cs = m[m.year == Y].dropna(subset=["premium_25_34", "attain_25_34"]).copy()
r_cs = cs.attain_25_34.corr(cs.premium_25_34)
r_gdp = np.log(cs.gdp_pcap).corr(cs.premium_25_34)
kor = cs.set_index("area").loc["KOR"]
rank_att = int(cs.attain_25_34.rank(ascending=False)["KOR" == cs.area].iloc[0])
rank_prem_low = int(cs.premium_25_34.rank(ascending=True)["KOR" == cs.area].iloc[0])
r_ch = ch.d_attain.corr(ch.d_premium)
n_down, n_up = int((ch.d_premium < 0).sum()), int((ch.d_premium > 0).sum())
r_min, r_max = rob.pearson.min(), rob.pearson.max()
k = m[(m.area == "KOR") & (m.year >= 2010)].set_index("year")
kc = ch.set_index("area").loc["KOR"]
print(f"cross-section {Y}: n={len(cs)} r={r_cs:.2f} r_gdp={r_gdp:.2f} KOR attain rank {rank_att}, premium rank(low) {rank_prem_low}")
print(f"change: n={len(ch)} r={r_ch:.2f} down={n_down} up={n_up}; robustness r in [{r_min},{r_max}]")


def ann(df, xs, ys, align="left", size=12.5, color=INK, color_field=False, dx=0):
    """주석 텍스트: 굵기(w)별로 레이어를 나눠 그림 (fontWeight는 인코딩 채널이 아님)"""
    layers = []
    for w in ["bold", "normal"]:
        d = df[df.w == w]
        if d.empty: continue
        enc = dict(x=alt.X("x:Q", scale=xs), y=alt.Y("y:Q", scale=ys), text="t:N")
        if color_field: enc["color"] = alt.Color("c:N", scale=None)
        layers.append(alt.Chart(d).mark_text(align=align, fontSize=size, fontWeight=w, dx=dx,
                                            **({} if color_field else {"color": color})).encode(**enc))
    return alt.layer(*layers)

def base_cfg(c):
    return (c.configure(font=FONT, background="transparent")
             .configure_view(stroke=None)
             .configure_title(fontSize=15, subtitleFontSize=12, anchor="start", offset=12, subtitlePadding=6)
             .configure_axis(labelFontSize=12, titleFontSize=12, titleFontWeight="normal", gridColor="#e9e8e2",
                             domainColor="#c3c2b7", tickColor="#c3c2b7", labelColor=INK2, titleColor=INK2))

# ---------------------------------------------------------------- ① 2023년 단면
W1, H1 = 600, 350
XS1 = alt.Scale(domain=[25, 75]); YS1 = alt.Scale(domain=[95, 215], zero=False, nice=False)
cs["is_kor"] = cs.area == "KOR"
cs["label"] = np.where(cs.area.isin(["KOR", "NOR", "SWE", "USA", "COL", "CAN"]), cs.country, "")
x1 = alt.X("attain_25_34:Q", title="25–34세 대졸자 비율 (%)", scale=XS1, axis=alt.Axis(values=list(range(25, 80, 5))))
y1 = alt.Y("premium_25_34:Q", title="25–34세 대졸 임금 프리미엄 (고졸 = 100)", scale=YS1)
tip1 = [alt.Tooltip("country:N", title="국가"), alt.Tooltip("attain_25_34:Q", title="대졸자 비율(%)", format=".1f"),
        alt.Tooltip("premium_25_34:Q", title="프리미엄", format=".1f")]
c1_base = alt.Chart(cs)
p1 = c1_base.mark_circle(size=85, opacity=1, stroke="#fcfcfb", strokeWidth=1.5).encode(
    x=x1, y=y1, color=alt.condition("datum.is_kor", alt.value(BLUE), alt.value(GRAY_PT)),
    order=alt.Order("is_kor:O"), tooltip=tip1)
reg1 = c1_base.transform_regression("attain_25_34", "premium_25_34").mark_line(color=MUTED, strokeWidth=1.5).encode(x=x1, y=y1)
lab1 = c1_base.transform_filter("datum.label != '' && !datum.is_kor").mark_text(
    align="left", dx=8, dy=-1, fontSize=12, color=INK2).encode(x=x1, y=y1, text="label:N")
lab1k = c1_base.transform_filter("datum.is_kor").mark_text(
    align="right", dx=-10, dy=-10, fontSize=13, fontWeight="bold", color=BLUE).encode(x=x1, y=y1, text="label:N")
ann1 = pd.DataFrame([
    {"x": 74, "y": 207, "t": f"대졸자가 많은 나라일수록 프리미엄이 낮아 보인다 (상관 r = {r_cs:.2f}, {len(cs)}개국)", "w": "bold"},
    {"x": 74, "y": 199, "t": f"하지만 부유한 나라일수록 프리미엄이 낮은 경향이 더 강하다 (로그 1인당 GDP와 r = {r_gdp:.2f})", "w": "normal"},
    {"x": 74.5, "y": 101,
     "t": f"한국: 대졸자 비율 {rank_att}위({kor.attain_25_34:.1f}%) · 프리미엄 하위 {rank_prem_low}위({kor.premium_25_34:.0f})", "w": "normal"},
])
t1 = ann(ann1[ann1.index < 2], XS1, YS1, align="right")
t1k = alt.Chart(ann1[ann1.index == 2]).mark_text(align="right", fontSize=11.5, color=BLUE).encode(
    x=alt.X("x:Q", scale=XS1), y=alt.Y("y:Q", scale=YS1), text="t:N")
avg23 = float(avg.loc[avg.year == Y, "premium_25_34"].iloc[0])
oe1 = alt.Chart(pd.DataFrame({"y": [avg23], "t": [f"OECD 평균 {avg23:.0f}"]}))
oer = oe1.mark_rule(color=INK2, strokeWidth=1, opacity=0.6).encode(y=alt.Y("y:Q", scale=YS1))
oet = oe1.mark_text(align="left", x=4, dy=-7, fontSize=11, color=INK2).encode(y=alt.Y("y:Q", scale=YS1), text="t:N")
chart1 = alt.layer(oer, oet, reg1, p1, lab1, lab1k, t1, t1k).properties(
    width=W1, height=H1,
    title=alt.Title("① 한 해만 보면 ‘대졸자가 많을수록 졸업장 값이 낮다’처럼 보인다",
                    subtitle=f"OECD 회원국, {Y}년, 25–34세 · 점 = 국가 · 회색 선 = 선형 추세"))

# ---------------------------------------------------------------- ② 변화량
W2, H2 = 600, 380
XS2 = alt.Scale(domain=[-4, 21]); YS2 = alt.Scale(domain=[-32, 30], zero=False, nice=False)
ch["is_kor"] = ch.area == "KOR"
show = {"KOR", "CAN", "ESP", "TUR", "NOR", "PRT", "HUN", "IRL"}
ch["label"] = np.where(ch.area.isin(show), ch.country, "")
x2 = alt.X("d_attain:Q", title="25–34세 대졸자 비율 변화 (%p)", scale=XS2)
y2 = alt.Y("d_premium:Q", title="25–34세 대졸 프리미엄 변화 (포인트)", scale=YS2)
tip2 = [alt.Tooltip("country:N", title="국가"), alt.Tooltip("d_attain:Q", title="대졸자 비율 변화(%p)", format="+.1f"),
        alt.Tooltip("d_premium:Q", title="프리미엄 변화", format="+.1f"),
        alt.Tooltip("premium_start:Q", title="2014–15 프리미엄", format=".1f"),
        alt.Tooltip("premium_end:Q", title="2022–23 프리미엄", format=".1f")]
c2 = alt.Chart(ch)
zero = alt.Chart(pd.DataFrame({"v": [0]}))
zx = zero.mark_rule(color="#c3c2b7", strokeWidth=1).encode(x=alt.X("v:Q", scale=XS2))
zy = zero.mark_rule(color=INK2, strokeWidth=1).encode(y=alt.Y("v:Q", scale=YS2))
quad = pd.DataFrame([
    {"x": 20.5, "y": 28, "t": f"● 프리미엄 상승 ({n_up}개국)", "c": UP, "w": "bold"},
    {"x": 20.5, "y": -22, "t": f"● 프리미엄 하락 ({n_down}개국)", "c": DOWN, "w": "bold"},
])
qt = ann(quad, XS2, YS2, align="right", size=12.5, color_field=True)
shade = alt.Chart(pd.DataFrame([{"y0": 0, "y1": 30, "c": UP}, {"y0": -32, "y1": 0, "c": DOWN}])).mark_rect(opacity=0.06).encode(
    y=alt.Y("y0:Q", scale=YS2), y2="y1:Q", color=alt.Color("c:N", scale=None))
p2 = c2.mark_circle(size=90, opacity=0.95, stroke="#fcfcfb", strokeWidth=1.5).encode(
    x=x2, y=y2, color=alt.condition("datum.d_premium > 0", alt.value(UP), alt.value(DOWN)), tooltip=tip2)
ring2 = c2.transform_filter("datum.is_kor").mark_point(shape="circle", size=330, filled=False, strokeWidth=3, color=BLUE).encode(x=x2, y=y2)
reg2 = c2.transform_regression("d_attain", "d_premium").mark_line(color=MUTED, strokeWidth=1.5).encode(x=x2, y=y2)
lab2 = c2.transform_filter("datum.label != '' && !datum.is_kor").mark_text(
    align="left", dx=8, fontSize=12, color=INK2).encode(x=x2, y=y2, text="label:N")
lab2k = c2.transform_filter("datum.is_kor").mark_text(
    align="left", dx=13, dy=2, fontSize=13, fontWeight="bold", color=BLUE).encode(x=x2, y=y2, text="label:N")
ann2 = pd.DataFrame([
    {"x": -3.7, "y": 28, "t": f"상관 r = {r_ch:.2f} — 대졸자가 많이 늘어난 나라라고", "w": "bold"},
    {"x": -3.7, "y": 25.0, "t": "프리미엄이 더 떨어지지 않았다", "w": "bold"},
    {"x": -3.7, "y": 21.6, "t": f"프리미엄 하락 {n_down}개국 · 상승 {n_up}개국", "w": "normal"},
    {"x": -3.7, "y": 19.0, "t": f"비교 연도를 바꿔도 r = {r_min:.2f} ~ {r_max:.2f}", "w": "normal"},
])
t2 = ann(ann2, XS2, YS2)
chart2 = alt.layer(shade, zx, zy, qt, reg2, p2, ring2, lab2, lab2k, t2).properties(
    width=W2, height=H2,
    title=alt.Title("② 변화로 보면 그 관계가 사라진다",
                    subtitle=f"OECD {len(ch)}개국, 2014–15년 평균 → 2022–23년 평균, 25–34세 · 색 = 프리미엄이 오른 나라/내린 나라 · 파란 고리 = 한국"))

# ---------------------------------------------------------------- ③ 한국 사례 (같은 x축의 두 패널)
W3 = 590
kk = m[(m.area == "KOR") & (m.year >= 2010)][["year", "attain_25_34", "premium_25_34", "attain_flag_25_34"]].copy()
kk["pre"] = kk.year < 2014
oa = avg[avg.year >= 2010][["year", "premium_25_34", "attain_25_34"]]
XS3 = alt.Scale(domain=[2010, 2024.6])
x3 = alt.X("year:Q", title=None, scale=XS3, axis=alt.Axis(format="d", values=list(range(2010, 2025, 2))))
band = alt.Chart(pd.DataFrame({"a": [2014], "b": [2024]}))
def bandlayer(ys, ytop):
    return band.mark_rect(color="#2a78d6", opacity=0.07).encode(x=alt.X("a:Q", scale=XS3), x2="b:Q")
YA = alt.Scale(domain=[30, 75], zero=False, nice=False)
ka_line = alt.Chart(kk).mark_line(color=BLUE, strokeWidth=2.5).encode(x=x3, y=alt.Y("attain_25_34:Q", scale=YA, title="대졸자 비율 (%)"))
ka_pts = alt.Chart(kk).mark_circle(size=45, color=BLUE, opacity=1).encode(
    x=x3, y=alt.Y("attain_25_34:Q", scale=YA), tooltip=[alt.Tooltip("year:O", title="연도"), alt.Tooltip("attain_25_34:Q", title="한국 대졸자 비율(%)", format=".1f")])
oa_line = alt.Chart(oa.dropna(subset=["attain_25_34"])).mark_line(color="#8f8e88", strokeWidth=2, strokeDash=[5, 4]).encode(x=x3, y=alt.Y("attain_25_34:Q", scale=YA))
a0, a1 = float(k.loc[2014, "attain_25_34"]), float(k.loc[2024, "attain_25_34"])
pr0, pr1 = float(k.loc[2014, "premium_25_34"]), float(k.loc[2024, "premium_25_34"])
la = pd.DataFrame([
    {"x": 2024.4, "y": a1, "t": "한국", "c": BLUE, "w": "bold"},
    {"x": 2024.4, "y": float(oa.set_index("year").loc[2024, "attain_25_34"]), "t": "OECD 평균", "c": MUTED, "w": "normal"},
])
la = ann(la, XS3, YA, size=12, color_field=True, dx=4)
na = alt.Chart(pd.DataFrame([{"x": 2014.3, "y": 58, "t": f"2014년 이후 거의 그대로: {a0:.1f}% → {a1:.1f}% (+{a1-a0:.1f}%p)"}])).mark_text(
    align="left", fontSize=12.5, fontWeight="bold", color=INK).encode(x=alt.X("x:Q", scale=XS3), y=alt.Y("y:Q", scale=YA), text="t:N")
top = alt.layer(bandlayer(YA, 75), oa_line, ka_line, ka_pts, la, na).properties(
    width=W3, height=150, title=alt.Title("③ 한국: 대졸자 비율은 멈췄는데 졸업장 값은 계속 내려갔다",
                                          subtitle="25–34세 · 음영 = 2014–2024년 · 위: 대졸자 비율, 아래: 대졸 프리미엄 (같은 연도 축)"))
YP = alt.Scale(domain=[105, 145], zero=False, nice=False)
kp_line = alt.Chart(kk).mark_line(color=BLUE, strokeWidth=2.5).encode(x=x3, y=alt.Y("premium_25_34:Q", scale=YP, title="프리미엄 (고졸 = 100)"))
kp_pts = alt.Chart(kk).mark_circle(size=45, color=BLUE, opacity=1).encode(
    x=x3, y=alt.Y("premium_25_34:Q", scale=YP), tooltip=[alt.Tooltip("year:O", title="연도"), alt.Tooltip("premium_25_34:Q", title="한국 프리미엄", format=".1f")])
op_line = alt.Chart(oa.dropna(subset=["premium_25_34"])).mark_line(color="#8f8e88", strokeWidth=2, strokeDash=[5, 4]).encode(x=x3, y=alt.Y("premium_25_34:Q", scale=YP))
lp = pd.DataFrame([
    {"x": 2024.4, "y": pr1, "t": "한국", "c": BLUE, "w": "bold"},
    {"x": 2024.4, "y": float(oa.set_index("year").loc[2024, "premium_25_34"]), "t": "OECD 평균", "c": MUTED, "w": "normal"},
])
lp = ann(lp, XS3, YP, size=12, color_field=True, dx=4)
npn = alt.Chart(pd.DataFrame([{"x": 2014.3, "y": 109, "t": f"같은 기간 계속 하락: {pr0:.0f} → {pr1:.0f}"}])).mark_text(
    align="left", fontSize=12.5, fontWeight="bold", color=INK).encode(x=alt.X("x:Q", scale=XS3), y=alt.Y("y:Q", scale=YP), text="t:N")
bot = alt.layer(bandlayer(YP, 145), op_line, kp_line, kp_pts, lp, npn).properties(width=W3, height=170)
chart3 = alt.vconcat(top, bot, spacing=14)

charts = {"c1": chart1, "c2": chart2, "c3": chart3}
specs = {}
for key, c in charts.items():
    cc = base_cfg(c)
    specs[key] = cc.to_dict()

facts = dict(r_cs=round(r_cs, 2), r_gdp=round(r_gdp, 2), n_cs=len(cs), kor_att=round(float(kor.attain_25_34), 1),
             kor_prem=round(float(kor.premium_25_34), 1), rank_att=rank_att, rank_prem_low=rank_prem_low,
             r_ch=round(r_ch, 2), n_ch=len(ch), n_down=n_down, n_up=n_up, r_min=r_min, r_max=r_max,
             a0=a0, a1=a1, pr0=round(pr0, 1), pr1=round(pr1, 1),
             kor_d_att=round(float(kc.d_attain), 1), kor_d_prem=round(float(kc.d_premium), 1), a_diff=round(a1 - a0, 1),
             m_datt=f"+{ch.d_attain.mean():.1f}", m_dprem=f"{ch.d_premium.mean():+.1f}")
(P / "story_facts.json").write_text(json.dumps(facts, ensure_ascii=False, indent=1), encoding="utf-8")
tpl = (ROOT / "templates" / "story_template.html").read_text(encoding="utf-8")
body = tpl.replace("/*__SPECS__*/null", json.dumps(specs, ensure_ascii=False))
for k_, v_ in facts.items():
    body = body.replace("{{" + k_ + "}}", str(v_).replace("-", "−"))
full = ('<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '</head>\n<body>\n' + body + '\n</body>\n</html>\n')
(SITE / "index.html").write_text(full, encoding="utf-8")
(ROOT / "site" / "artifact_story.html").write_text(body, encoding="utf-8")
print("facts", facts)
