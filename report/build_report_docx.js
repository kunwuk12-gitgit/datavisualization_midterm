// 보고서(.docx) 생성 — node report/build_report_docx.js
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, ImageRun, ExternalHyperlink, LevelFormat, Footer, PageNumber,
  TableLayoutType, LineRuleType,
} = require("docx");

const ROOT = path.join(__dirname, "..");
const FONT = "맑은 고딕";
const CODE = "맑은 고딕";
const W = 9026; // A4 본문 폭 (DXA, 여백 2.54cm)

// ---------- 인라인: **굵게**, *기울임*, `코드`, [글](url)
function inline(s, base = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\)|\*[^*]+\*)/g;
  let last = 0, m;
  const push = (t, o = {}) => t && out.push(new TextRun({ text: t, ...base, ...o }));
  while ((m = re.exec(s))) {
    push(s.slice(last, m.index));
    const t = m[0];
    if (t.startsWith("**")) push(t.slice(2, -2), { bold: true });
    else if (t.startsWith("`")) push(t.slice(1, -1), { font: { ascii: CODE, hAnsi: CODE, eastAsia: FONT, cs: FONT } });
    else if (t.startsWith("[")) {
      const mm = t.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
      out.push(new ExternalHyperlink({ link: mm[2], children: [new TextRun({ text: mm[1], style: "Hyperlink", ...base })] }));
    } else push(t.slice(1, -1), { italics: true });
    last = m.index + t.length;
  }
  push(s.slice(last));
  return out;
}

const P = (s, o = {}) => new Paragraph({ children: inline(s, o.run), ...o.para });
const H2 = (s) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(s)] });
const H3 = (s) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(s)] });

let olCount = 0;
const bullets = (items) => items.map((s) => new Paragraph({ numbering: { reference: "bul", level: 0 }, children: inline(s), spacing: { after: 60 } }));
const ordered = (items) => {
  const ref = "ol" + (++olCount);
  return items.map((s) => new Paragraph({ numbering: { reference: ref, level: 0 }, children: inline(s), spacing: { after: 60 } }));
};

const border = { style: BorderStyle.SINGLE, size: 4, color: "808080" };
const borders = { top: border, bottom: border, left: border, right: border };
function table(rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths, layout: TableLayoutType.FIXED,
    rows: rows.map((r, i) => new TableRow({
      tableHeader: i === 0,
      children: r.map((c, j) => new TableCell({
        borders, width: { size: widths[j], type: WidthType.DXA },
        shading: i === 0 ? { fill: "F2F2F2", type: ShadingType.CLEAR, color: "auto" } : undefined,
        margins: { top: 60, bottom: 60, left: 100, right: 100 },
        children: [new Paragraph({ spacing: { after: 0, line: 260 }, alignment: i === 0 ? AlignmentType.CENTER : AlignmentType.LEFT,
          children: inline(c, { size: 18, bold: i === 0 ? true : undefined }) })],
      })),
    })),
  });
}
const gap = () => new Paragraph({ spacing: { after: 0 }, children: [] });

function img(file, widthPx) {
  const buf = fs.readFileSync(path.join(ROOT, "figures", file));
  const w0 = buf.readUInt32BE(16), h0 = buf.readUInt32BE(20);
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60, line: 240, lineRule: LineRuleType.AUTO }, keepNext: true,
    children: [new ImageRun({ type: "png", data: buf, transformation: { width: widthPx, height: Math.round(widthPx * h0 / w0) },
      altText: { title: file, description: file, name: file } })] });
}
const caption = (s) => new Paragraph({ style: "Caption", alignment: AlignmentType.CENTER, children: inline(s) });

// ---------------------------------------------------------------- 본문
const body = [];
body.push(new Paragraph({ style: "Title", alignment: AlignmentType.CENTER, children: [new TextRun("데이터 시각화 중간고사 보고서")] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 }, children: [new TextRun({ text: "대학 졸업장의 값", size: 28, bold: true, color: "000000" })] }));
body.push(new Paragraph({ alignment: AlignmentType.RIGHT, spacing: { after: 240 }, children: [new TextRun({ text: "22400498 이건욱", size: 21 })] }));

body.push(P("OECD 회원국의 대졸 임금 프리미엄을 탐색하는 대시보드(Part A)와, \"대졸자가 더 많이 늘어난 나라에서 졸업장 값이 더 떨어지지는 않았다\"는 메시지를 전달하는 설명 시각화(Part B)를 만들었습니다. 데이터는 OECD Education at a Glance의 데이터셋 3개와 Gapminder의 데이터셋 3개를 결합해 사용했습니다."));

body.push(H3("제출물"));
body.push(table([
  ["구분", "먼저 열 것", "내용"],
  ["Part A 탐색 대시보드", "온라인 URL (아래 기입) 또는 `site/dashboard/index.html`", "국가·비교 국가·연도·연령대 선택, 바뀌는 결론 문장·KPI·변화표, 차트 3개, 클릭 선택"],
  ["Part B 설명 시각화", "온라인 URL (아래 기입) 또는 `site/story/index.html`", "핵심 메시지 1개 + 고정 차트 3개, 한계"],
  ["데이터", "`data/raw/`, `data/processed/`", "원자료 원문, 결합된 패널(`panel.csv`), 전처리 로그"],
  ["코드", "`prepare_data.py`, `validate_collection.py`, `build_dashboard.py`, `build_story.py`", "원자료 → 결과물까지 재현"],
  ["안내", "`README.md`", "여는 순서, 필요한 프로그램, 재현 방법"],
], [1900, 3500, 3626]));
body.push(gap());
body.push(...bullets(["Part A 온라인 URL: (게시 후 기입)", "Part B 온라인 URL: (게시 후 기입)"]));
body.push(P("**가산점 신청**: ① Part A 온라인 게시, ② Part B 온라인 게시, ③ 여러 출처 데이터의 수집·결합·정제를 신청합니다(근거는 3장과 7장)."));

// 1
body.push(H2("1. 주제와 질문"));
body.push(P("이 분석은 \"대졸자가 흔해지면 대학 졸업장의 값은 떨어지는가?\"라는 질문에서 출발했습니다. 한국은 청년(25–34세) 대졸자 비율이 OECD 1위(2023년 69.7%)이면서, 고졸 대비 대졸 임금 프리미엄은 하위권(114)입니다. 그래서 \"다들 대학에 가서 졸업장 값이 떨어졌다\"는 말이 널리 퍼져 있습니다. 대학생인 저와 같은 세대에게 직접 해당하는 문제이고, 대학 정원 같은 정책 논의와도 연결되어 있어 주제로 골랐습니다."));
body.push(...bullets([
  "**핵심 지표**: 대졸 임금 프리미엄 = 같은 나라·같은 연령대 고졸(ISCED 3) 전일제 근로자 평균 임금을 100으로 두었을 때, 고등교육(ISCED 5–8) 이수 전일제 근로자의 평균 임금",
  "**비교 축**: 나라(OECD 36개국), 연도(2010–2024), 세대(25–34세 vs 55–64세)",
  "**같이 보는 변수**: 대졸자 비율(공급), 1인당 GDP(소득 수준), 25–34세 대졸 고용률(일자리 측면), 15–24세 실업률(청년 노동시장)",
]));
body.push(P("처음에는 한 해 단면에서 대졸자가 많은 나라의 프리미엄이 낮은 패턴을 확인했습니다. 그런데 변화량으로 다시 보니 그 관계가 사라졌고, 이 차이가 Part B의 메시지가 되었습니다."));

// 2
body.push(H2("2. 데이터 출처와 범위"));
body.push(P("지정 출처 중 OECD와 Gapminder에서 데이터셋 6개를 받았습니다. 접근일은 모두 2026년 10월 24일입니다."));
body.push(table([
  ["출처 · 데이터셋", "지표", "단위", "범위", "수집한 값"],
  ["OECD EAG `DF_LSO_EARN_REL_UPPER`", "고등교육 이수자 상대임금, 전일제(FT), 성별 전체", "고졸 임금 = 100", "44개 지역, 2005·2010–2024, 25–34·55–64세", "1,003개"],
  ["OECD EAG `DF_LSO_NEAC_DISTR_EA`", "고등교육 이수자 비율", "해당 연령 인구 대비 %", "51개 지역, 같은 연도·연령", "1,426개"],
  ["OECD EAG `DF_LSO_NEAC_EMP`", "고등교육 이수자 고용률", "같은 집단 대비 %", "50개 지역, 25–34세", "713개"],
  ["Gapminder `gdp_pcap` (fasttrack v32)", "1인당 GDP", "PPP, 2021년 불변 국제달러", "전 세계, 1800–2100", "패널에 맞춰 결합"],
  ["Gapminder `aged_15_24_unemployment_rate_percent` (systema_globalis, ILOSTAT 기반)", "15–24세 실업률", "%", "전 세계, ~2025", "패널에 맞춰 결합"],
  ["Gapminder `ddf--entities--geo--country`", "지역(world_4region), World Bank 소득그룹, ISO3 코드", "—", "270여 개 지역", "국가 기준표"],
], [2500, 2000, 1500, 1800, 1226]));
body.push(gap());
body.push(...bullets([
  "원문 URL: OECD SDMX API `https://sdmx.oecd.org/public/rest/data/OECD.EDU.IMEP,DSD_EAG_LSO_EA@<데이터셋>,/<키>` ([OECD Data Explorer](https://www.oecd.org/en/data.html)), Gapminder [open-numbers DDF 저장소](https://github.com/open-numbers) ([gapminder.org/data](https://www.gapminder.org/data)). 질의 키는 `data/raw/` 각 파일의 첫 줄에 적어 두었습니다.",
  "**분석 범위**: OECD 회원국 38개국 중 임금 자료가 있는 36개국(일본·아이슬란드 제외), 2010–2024년입니다. 파트너국(브라질·남아공 등)은 패널에는 남겨 두었지만 분석과 시각화에서는 제외했습니다.",
  "**연령대 선택 이유**: 25–34세는 최근 졸업한 청년 세대, 55–64세는 부모 세대입니다. 같은 해에 두 세대의 졸업장 값을 비교할 수 있어 이 두 연령대를 골랐습니다.",
  "청년 노동시장 지표는 ILO 원자료를 가공한 Gapminder의 청년 실업률을, 소득 구분은 Gapminder가 제공하는 World Bank 소득그룹 분류를 사용했습니다.",
]));

// 3
body.push(H2("3. 수집·전처리·결합"));
body.push(P("원자료 3,142개 관측값을 모아 국가×연도 패널 685행(48개국 × 16개 연도)으로 결합했습니다. 모든 단계는 `prepare_data.py`가 수행하고, 처리 내용은 `data/processed/prep_log.md`에 자동으로 기록되도록 만들었습니다."));
body.push(...ordered([
  "**수집**: OECD SDMX API에서 연도별로 나눠 받았습니다(임금 16회, 학력 분포 16회, 고용률 6회). 한 번에 받으면 응답이 잘렸기 때문입니다. 파일마다 질의 키와 접근일을 남겼습니다.",
  "**수집 검증**: 연도별로 받은 값과 별도로 국가별 전체 시계열을 다시 받아 1:1로 대조했습니다(7개국, 276개 값). 불일치는 없었습니다(`validate_collection.py`).",
  "**중복 점검**: (연도, 국가, 연령) 키에 중복이 없는 것을 확인했습니다.",
  "**정제**: 아래 표의 문제들을 처리했습니다.",
  "**형태 변환**: 연령별 long 형식을 국가×연도 wide 형식으로 바꾸고, 자료 상태 플래그도 값 옆 열로 옮겼습니다.",
  "**결합**: OECD 패널에 Gapminder의 GDP·실업률·지역을 국가 코드와 연도 기준으로 left join했습니다.",
  "**파생 변수**: 세대 격차(55–64세 − 25–34세 프리미엄), 기간별 변화량, 강건성 점검표를 만들었습니다.",
]));
body.push(gap());
body.push(table([
  ["문제", "발견 방법", "처리"],
  ["슬로바키아 2013년 프리미엄 2.97 / 3.94", "다른 국가·연도는 100–340 범위, 인접 연도 144.4 / 141.4", "단위·코딩 오류로 판단해 결측 처리"],
  ["남아공 2023년 값 294.1", "OECD가 OBS_STATUS = U(낮은 신뢰도)로 표시", "제외"],
  ["남아공 2024년 고용률 35.5% (전년 66.0%)", "급락 점검", "결측 처리(분석 범위 밖)"],
  ["2014년 이전 값 다수에 시계열 단절(B)", "학력 분포는 220건, 임금은 94건. OECD의 ISCED 2011 분류 전환 시점", "값은 보존하고 플래그 열로 표시, 변화량 분석은 2014년 이후로 한정, 대시보드 툴팁에 노출"],
  ["일본 학력 값에 W 플래그(다른 범주 포함)", "플래그 점검", "일본은 임금 자료가 없어 프리미엄 분석에서 제외됨"],
  ["국가 코드 표기 불일치", "OECD는 `KOR`, Gapminder는 `kor`, 열 이름도 `country`·`geo`로 다름", "대문자 ISO3 `area`로 통일, 메타는 `iso3166_1_alpha3`로 매칭. 미매칭 0건"],
  ["OECD·EU25·G20 집계값이 국가 행에 섞임", "코드 목록 점검", "분리해 `oecd_average.csv`로 저장, OECD 평균은 기준선으로만 사용"],
  ["임금 정의가 두 가지(전일제 / 전체 근로자)", "데이터셋 차원 확인", "시간제 비중 차이가 섞이지 않도록 전일제(FT)로 통일"],
  ["한국 고졸 고용률은 2022년부터만 존재", "국가별 시계열 확인", "고용 지표는 대졸 고용률만 사용"],
  ["단일 연도 비교 시 결측으로 표본 손실", "2014→2023 단일 연도는 26개국만 가능", "2014–15년 평균 → 2022–23년 평균으로 변경해 34개국 확보"],
], [2700, 3100, 3226]));
body.push(gap());
body.push(P("**결합으로 가능해진 분석**: OECD 자료만 있었다면 \"대졸자가 많은 나라의 프리미엄이 낮다\"는 단면 상관(r = −0.37)을 그대로 받아들일 수밖에 없었습니다. Gapminder 1인당 GDP(로그값)를 붙여 보니 소득과 프리미엄의 상관(r = −0.55)이 더 강했고, 소득은 대졸자 비율과도 연결되어 있었습니다(r = 0.60). 이 때문에 변화량 분석으로 한 번 더 검증하게 되었고, 그 결과가 Part B 메시지의 바탕이 되었습니다."));

// 4
body.push(H2("4. Part A 탐색 대시보드: 대졸 프리미엄 탐색기"));
body.push(P("사용자가 고른 나라의 졸업장 값을 OECD 평균, 비교 국가와 나란히 놓고 질문 1–5를 차례대로 따라가도록 **안내형 탐색 대시보드**로 구성했습니다. 위쪽 컨트롤 4칸을 바꾸면 결론 문장, KPI, 변화표, 차트 3개, 차트별 해석 문장, 요점이 모두 다시 계산됩니다. 차트는 수업에서 배운 Altair(Vega-Lite)로 그렸고, 문장·표·순위는 페이지에 넣어 둔 데이터로 JavaScript가 계산하도록 했습니다."));
body.push(img("dashboard_default.png", 560));
body.push(caption("그림 1. Part A 기본 화면 — 한국(선택) vs 캐나다(비교), 2023년, 25–34세."));
body.push(...bullets([
  "**사용자**: 진로와 학위의 가치를 고민하는 대학생·청년, 교육·노동 정책에 관심 있는 독자",
  "**데이터 범위**: OECD 36개국, 2010–2024년, 25–34세·55–64세",
  "**탐색 질문**: \"선택한 나라의 졸업장 값은 OECD 평균과 비교해 어디쯤이고, 2014년 이후 어떻게 변했으며, 대졸자가 많다는 것으로 얼마나 설명되는가?\" 예: 한국의 프리미엄은 얼마나 낮은가 · 캐나다는 대졸자가 늘었는데 왜 프리미엄이 올랐나 · 부모 세대와의 격차가 가장 큰 나라는 어디인가",
]));
body.push(H3("구성"));
body.push(table([
  ["순서", "질문", "표현"],
  ["컨트롤", "① 국가 ② 비교 국가 ③ 연도 ④ 연령대", "노란색 입력칸, 처음 상태로 버튼"],
  ["결론 문장", "지금 선택의 핵심은?", "예: \"한국: 2023년 25–34세 대졸 프리미엄 114.3 — OECD 평균(137.0)보다 22.7 낮다. 2014년 이후 −5.9 (OECD 평균 −3.0)\" + 색 범례"],
  ["1", "어디에 서 있나?", "KPI 카드 4개(프리미엄·대졸자 비율·대졸 고용률·세대 격차): 큰 숫자, 비교국, OECD 평균, OECD 내 순위"],
  ["2", "2014년 이후 얼마나 변했나?", "2014년 = 0으로 지수화한 선 그래프 + 변화표(5개 지표, OECD 평균 대비)"],
  ["3", "대졸자가 많으면 졸업장 값이 낮을까?", "산점도 + 추세선 + \"추세선 예상값보다 몇 낮다/높다\""],
  ["4", "부모 세대와 비교하면?", "덤벨 차트(● 25–34세, ○ 55–64세) + 격차 순위"],
  ["5", "그래서?", "숫자가 들어간 세 가지 요점(단면 · 선택 국가 · 변화)"],
], [1300, 2900, 4826]));
body.push(H3("상호작용"));
body.push(...bullets([
  "**컨트롤 4칸**: 국가·비교 국가(드롭다운, \"비교 안 함\" 포함), 연도(슬라이더), 연령대(두 칸 버튼)입니다. 무엇을 바꾸든 숫자·차트·문장이 함께 바뀝니다.",
  "**차트에서 바로 선택**: 산점도·덤벨·선 그래프의 점을 클릭하면 ① 국가로, Shift+클릭하면 ② 비교 국가로 설정됩니다.",
  "**툴팁**: 점에 마우스를 올리면 국가, 프리미엄, 대졸자 비율, 고용률, GDP가 나옵니다.",
  "**현재 상태 표시**: 지금 무엇을 골랐는지는 컨트롤 4칸과 결론 문장에 항상 드러나고, 값이 바뀔 때 문장·KPI·표가 잠깐 깜박입니다. \"처음 상태로\" 버튼을 누르면 기본값(한국 vs 캐나다, 2023년, 25–34세)으로 돌아갑니다.",
  "**표 보기**: 현재 연도의 모든 나라 값을 표로 펼쳐 볼 수 있고, 값이 없는 경우는 0 대신 \"자료 없음\"으로 표시했습니다.",
]));
body.push(H3("설계 근거"));
body.push(...bullets([
  "**의미가 고정된 색 3개**: 파랑은 선택 국가, 주황은 비교 국가, 회색은 OECD 평균과 다른 나라입니다. 모든 차트·KPI·문장에서 같은 의미로 쓰고, 맨 위에 색 범례를 두었습니다. 나머지 나라를 균일한 회색으로 두어 두 나라가 바로 눈에 띄도록 했습니다(Preattentive processing의 pop-out, 대상과 배경의 유사도는 낮게). 두 색이 색각이상에서도 구분되는지 시뮬레이션으로 확인했습니다(ΔE 24.7).",
  "**Feature hierarchy**: 가장 강한 채널인 색은 핵심 정보(어느 나라인가)에 쓰고, 보조 정보인 연령대는 색이 아닌 채운 원(●)과 빈 원(○)으로 구분했습니다.",
  "**Graphical Perception**: 프리미엄은 모두 공통 축 위의 위치로 표현했습니다(정확도 1순위). 세대 비교는 누적 막대 대신 덤벨을 썼고, 변화는 두 시점 값을 눈으로 빼지 않도록 2014년을 0으로 두고 그렸습니다(Curvature 함정 피하기).",
  "**Cognitive effort 줄이기**: 제목에 번호가 붙은 질문을 쓰고, 차트마다 \"읽는 법\"과 \"이 차트가 보여주는 것\"을 달았습니다. 해석 문장이 현재 선택의 숫자를 그대로 보여주기 때문에 차트에서 값을 읽어낼 부담이 줄어듭니다. 문장 속 숫자는 화면에 보이는 반올림 값끼리 계산해서 표와 문장의 숫자가 어긋나지 않게 했습니다.",
  "**Change blindness**: 값이 바뀌면 깜박임으로 알려주고, 선 그래프의 세로선이 선택한 연도를 따라 움직이도록 했습니다.",
  "**기준선 구분**: 점선은 OECD 평균(연도·연령에 따라 바뀜), 초록 실선은 현재 표시된 나라들의 추세선, 세로 점선은 선택한 연도로 의미를 나눴습니다.",
  "**연결된 뷰(Altair Part 2의 parameter)**: 국가·비교 국가·연도·연령대를 alt.param 네 개로 만들고 차트 3개가 같은 파라미터를 공유하도록 했습니다. 그래서 한 곳에서 나라를 바꾸면 선 그래프·산점도·덤벨 차트의 강조가 동시에 바뀝니다. 연도와 연령대에 따라 보여줄 값은 transform_filter와 transform_calculate가 파라미터 값을 읽어 다시 계산하고, 산점도의 추세선과 R²는 transform_regression으로 현재 화면의 나라들만 가지고 매번 새로 구합니다.",
  "**Overview → 선택 → 세부 정보**: 처음에는 모든 나라를 회색으로 보여 전체 분포를 먼저 보게 하고, 관심 있는 나라를 고르면 색으로 강조되며, 자세한 값은 툴팁과 표 보기에서 확인하는 순서로 구성했습니다.",
]));

// 5
body.push(H2("5. Part B 설명 시각화: 졸업장 값의 오해"));
body.push(P("**핵심 메시지**: 대졸자가 더 많이 늘어난 나라에서 졸업장 값이 더 떨어지지는 않았다. 한국 청년의 낮은 대졸 프리미엄은 '대졸자가 너무 많아서'만으로는 설명되지 않는다."));
body.push(...bullets([
  "**대상 독자**: 대학 진학·전공·취업을 고민하는 한국의 대학생과 청년, 대학 정원과 고등교육 정책을 논의하는 사람",
  "**왜 중요한가**: 졸업장 값이 떨어진 것을 '대졸자가 너무 많아서'로만 보면 대학 정원 축소 같은 처방에만 관심이 쏠립니다. 다른 요인도 봐야 한다는 근거를 데이터로 보여주고 싶었습니다.",
]));
body.push(H3("읽는 순서와 차트별 근거"));
body.push(...ordered([
  "**① 통념의 근거 (2023년 단면, 28개국)**: 대졸자가 많은 나라일수록 프리미엄이 낮아 보입니다(r = −0.37). 한국은 대졸자 비율 1위(69.7%), 프리미엄 하위 3위(114)로 그 끝에 있습니다. 차트에 \"로그 1인당 GDP와의 상관이 더 강하다(r = −0.55)\"는 주석을 달아 단면 비교의 한계를 먼저 보여주었습니다. 통념이 왜 맞아 보이는지도 숨기지 않고 보여주어 cherry-picking을 피하려 했습니다.",
  "**② 변화로 검증 (34개국, 2014–15 → 2022–23)**: 통념이 맞다면 대졸자가 많이 늘어난 나라일수록 프리미엄이 많이 떨어져야 합니다. 실제 상관은 r = 0.05였고, 프리미엄이 내린 나라는 18개국, 오른 나라는 16개국이었습니다. 34개국 평균으로 보면 대졸자 비율은 6.2%p 늘었지만 프리미엄 변화는 평균 −0.3에 그쳤습니다. 비교 연도를 다섯 가지로 바꿔도 r은 −0.19 ~ 0.05 사이였습니다. 캐나다·스페인(대졸자↑ 프리미엄↑)과 튀르키예·노르웨이(대졸자↑ 프리미엄↓)에는 라벨을 달았습니다.",
  "**③ 한국 사례 (2010–2024)**: 2014년 이후 대졸자 비율은 67.7%에서 70.6%로 거의 그대로인데, 프리미엄은 120에서 114로 계속 내려갔습니다. 2014년 이전에는 두 값이 함께 움직였다는 점도 그대로 보여주었습니다.",
]));
body.push(img("story_c1.png", 540));
body.push(caption("그림 2. ① 통념의 근거 — 2023년 28개국, 한국 강조."));
body.push(img("story_c2.png", 540));
body.push(caption("그림 3. ② 변화로 검증 — 34개국, r = 0.05. 초록 = 프리미엄 상승, 주황 = 하락, 파란 고리 = 한국."));
body.push(img("story_c3.png", 560));
body.push(caption("그림 4. ③ 한국 사례 — 같은 연도 축을 공유하는 두 패널."));
body.push(H3("설계 근거"));
body.push(...bullets([
  "**메시지를 제목으로**: 페이지 제목과 차트 제목을 질문이 아닌 결론 문장으로 썼습니다(Altair의 explanatory chart 원칙). 진한 색 머리띠에 메시지를 두고, 그 아래 큰 숫자 3개(69.7%, 114.3, r = 0.05)로 근거를 먼저 보여주었습니다.",
  "**색의 역할 고정**: 파랑은 한국(모든 차트에서 같은 의미), 초록은 프리미엄 상승, 주황은 하락, 회색은 OECD 평균과 다른 나라입니다. 페이지 위에 색 범례를 두었고, 세 색이 색각이상에서도 구분되는지 확인했습니다.",
  "**②에서는 색으로 결론 보여주기 (Preattentive processing)**: 프리미엄이 오른 나라는 초록, 내린 나라는 주황으로 칠했습니다. 통념이 맞다면 오른쪽에는 주황만 남아야 하는데, 두 색이 가로축 전체에 섞여 있는 것이 한눈에 보입니다. 한국은 색 대신 파란 고리로 표시해 색의 의미가 겹치지 않게 했습니다(Feature hierarchy).",
  "**이중 축 쓰지 않기**: ③에서는 단위가 다른 대졸자 비율(%)과 프리미엄(지수)을 한 축에 겹치지 않고, 같은 연도 축을 쓰는 두 패널로 나눴습니다. 이중 축은 두 축의 비율에 따라 없는 상관도 있는 것처럼 보이게 만들 수 있기 때문입니다.",
  "**차이를 직접 그리기**: ②는 두 시점의 값을 따로 그리지 않고 변화량 자체를 위치로 그렸습니다. 두 값이나 두 선 사이의 차이를 눈으로 빼서 읽는 것은 정확도가 낮다는 Graphical Perception 내용을 반영했습니다.",
  "**Cleveland & McGill 순위로 인코딩 고르기**: 메시지에 가장 중요한 두 값(대졸자 비율, 프리미엄)은 정확도 1순위인 '공통 축 위의 위치'에 두었습니다. 색은 크기 비교가 아니라 '올랐나, 내렸나' 같은 범주 구분에만 썼고, 정확도가 낮은 면적과 각도는 쓰지 않았습니다. 1인당 GDP를 점 크기로 넣는 방법도 생각했지만, 면적은 실제 차이보다 작게 지각되기 쉬워(Stevens의 power law) 상관계수를 주석으로 적는 쪽을 택했습니다.",
  "**한국을 바로 찾게 하기 (pop-out vs conjunction search)**: ①에서는 나머지 나라를 모두 같은 회색으로 두어 파란 점 하나만 튀어나오게 했습니다. ②에서는 색이 이미 상승·하락에 쓰였기 때문에 한국까지 색으로 표시하면 '이 색이면서 이 위치' 같은 조합을 확인해야 해서 찾는 데 시간이 걸립니다(conjunction search). 그래서 한국에만 있는 큰 고리와 굵은 라벨이라는 별도의 특징으로 표시했습니다.",
  "**범례 대신 직접 라벨**: 나라 이름은 점 바로 옆에, ②의 색 의미는 음영 영역 안에 '프리미엄 상승 / 하락'으로 적었습니다. 범례와 차트를 오가며 색을 대조하는 수고(cognitive effort)를 줄이기 위해서입니다.",
  "**Altair 문법으로 구현**: 모든 차트는 하나의 데이터에 여러 마크를 겹친 layer 구조입니다. 예를 들어 ②는 음영(mark_rect), 0선(mark_rule), 추세선(transform_regression + mark_line), 점(mark_circle), 한국 고리(mark_point), 라벨(mark_text)을 겹쳐 만들었습니다. 강조 색은 alt.condition으로 조건에 따라 바꾸고, 라벨을 붙일 나라는 transform_filter로 골랐습니다. ③은 두 차트를 vconcat으로 위아래로 붙이고 같은 연도 스케일을 써서 시점이 정확히 맞도록 했습니다. 변수 타입도 Q(양적)와 N(명목)으로 구분해 지정했습니다.",
  "**기준선과 주석**: ①에는 OECD 평균선, ②에는 변화 없음(0)선과 상승·하락 영역 음영, ③에는 2014–2024 음영과 시작·끝 값을 넣었습니다. 주석의 숫자는 직접 입력하지 않고 코드가 데이터에서 계산해 넣도록 했습니다.",
  "**축 설정**: 프리미엄은 '고졸 = 100' 지수라서 축을 0이 아닌 구간에서 시작했고, 대신 막대가 아닌 점·선으로만 표현해 길이로 오해하지 않게 했습니다. ③에는 시작·끝 값을 숫자로 함께 적어 변화의 크기가 과장되지 않도록 했습니다.",
  "**고정 화면과 요점**: 필터를 조작하지 않고 스크롤만 해도 메시지 → 01 → 02 → 03 → 세 가지 요점 → 한계 순서로 읽힙니다. 툴팁은 보조로만 썼습니다.",
]));

// 6
body.push(H2("6. 한계"));
body.push(P("이 분석은 \"대졸자가 늘면 프리미엄이 낮아진다\"는 단순한 관계가 데이터에서 보이지 않는다는 것까지만 보여줍니다. 해석할 때 다음 점들을 주의해야 합니다."));
body.push(...bullets([
  "**인과관계가 아닙니다**: 상관이 0에 가깝다고 해서 대졸자 수가 전혀 영향을 주지 않는다는 뜻은 아닙니다. 산업 구조나 경기 같은 다른 요인이 그 효과를 상쇄했을 수도 있습니다.",
  "**상대 임금입니다**: 고졸 임금이 오르면(예: 최저임금 인상) 대졸 임금이 그대로여도 프리미엄은 낮아집니다. 이 자료만으로는 두 경우를 구분할 수 없습니다.",
  "**전일제 근로자의 평균입니다**: 미취업자나 시간제 근로자, 전공·대학·성별에 따른 차이는 반영되지 않습니다. 평균값이라 분포가 어떻게 변했는지도 알 수 없습니다.",
  "**표본 범위**: OECD 36개국 중에서도 두 시점 자료가 모두 있는 34개국만 변화 분석에 들어갔습니다. 일본과 아이슬란드는 임금 자료가 없습니다. 따라서 결론을 OECD 밖의 나라로 넓힐 수는 없습니다.",
  "**기간**: 9년 정도의 변화만 봤습니다. 2014년 OECD 학력 분류 변경(ISCED 2011) 이전 값은 변화 분석에 쓰지 않았기 때문에, 더 긴 기간으로 보면 결과가 달라질 수 있습니다.",
  "**기준 연도 차이**: OECD 임금 자료는 나라마다 조사 기준 연도가 1년 정도 다를 수 있습니다.",
]));

// 7
body.push(H2("7. 가산점 내역과 재현 방법"));
body.push(table([
  ["가산점 항목", "근거"],
  ["① Part A 온라인 게시", "웹 URL에서 컨트롤 4칸, 차트 클릭 선택, 초기화가 모두 작동하고 결론 문장·KPI·표가 함께 바뀝니다. 데이터가 들어 있는 HTML 파일 하나로 동작합니다."],
  ["② Part B 온라인 게시", "웹 URL에서 필터 조작 없이 메시지와 차트 3개가 정해진 순서로 보입니다."],
  ["③ 데이터 수집·결합·정제", "2개 지정 출처의 6개 데이터셋 결합, 수집값 276개 교차 검증, 10가지 문제 처리(3장 표), 기간 정의 5가지 강건성 점검, 소득 교란 점검"],
], [2600, 6426]));
body.push(gap());
body.push(P("**재현 방법** (Python 3.10 이상, `pip install pandas altair vl-convert-python`)"));
body.push(...ordered([
  "`python prepare_data.py` — 원자료 → `data/processed/` (패널, 변화량, 강건성 표, 전처리 로그)",
  "`python validate_collection.py` — 수집값 교차 검증",
  "`python build_dashboard.py` — `site/dashboard/index.html`",
  "`python build_story.py` — `site/story/index.html`, `figures/story_*.png`",
]));
body.push(P("결과 HTML은 브라우저로 바로 열리지만 차트를 그리는 프로그램을 인터넷에서 불러오기 때문에 인터넷이 연결되어 있어야 합니다."));

// 출처
body.push(H2("출처"));
body.push(...bullets([
  "OECD (2026), Education at a Glance — Educational attainment and labour-force outcomes: [OECD Data Explorer](https://www.oecd.org/en/data.html), [Education at a Glance 2024: What are the earnings advantages to education?](https://www.oecd.org/en/publications/education-at-a-glance-2024_c00cad36-en/full-report/what-are-the-earnings-advantages-to-education_90d02e8d.html)",
  "Gapminder, GDP per capita (v32) · Aged 15–24 unemployment rate (ILOSTAT) · country entities: [gapminder.org/data](https://www.gapminder.org/data), [open-numbers](https://github.com/open-numbers)",
  "수업 자료: Graphical Perception, Preattentive Processing, Altair Part 1·2 (최혜봉 교수님)",
  "Cleveland, W. S., & McGill, R. (1984). Graphical perception. *JASA*, 79(387), 531–554.",
]));

// ---------------------------------------------------------------- 문서
const olConfigs = Array.from({ length: olCount }, (_, i) => ({
  reference: "ol" + (i + 1),
  levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 400, hanging: 300 } } } }],
}));
const doc = new Document({
  creator: "이건욱", title: "데이터 시각화 중간고사 보고서", lastModifiedBy: "이건욱",
  styles: {
    default: { document: { run: { font: { ascii: FONT, hAnsi: FONT, eastAsia: FONT, cs: FONT }, size: 20 },
      paragraph: { spacing: { after: 120, line: 300, lineRule: LineRuleType.AUTO } } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", next: "Normal", run: { size: 36, bold: true, color: "000000", font: { ascii: FONT, hAnsi: FONT, eastAsia: FONT, cs: FONT } }, paragraph: { spacing: { before: 0, after: 60 } } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, color: "000000", font: { ascii: FONT, hAnsi: FONT, eastAsia: FONT, cs: FONT } }, paragraph: { spacing: { before: 360, after: 120 }, outlineLevel: 0, keepNext: true,
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "000000", space: 2 } } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 23, bold: true, color: "000000", font: { ascii: FONT, hAnsi: FONT, eastAsia: FONT, cs: FONT } }, paragraph: { spacing: { before: 240, after: 80 }, outlineLevel: 1, keepNext: true } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 21, bold: true, color: "000000", font: { ascii: FONT, hAnsi: FONT, eastAsia: FONT, cs: FONT } }, paragraph: { spacing: { before: 200, after: 60 }, outlineLevel: 2, keepNext: true } },
      { id: "Heading4", name: "Heading 4", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 21, bold: true, color: "000000", font: { ascii: FONT, hAnsi: FONT, eastAsia: FONT, cs: FONT } }, paragraph: { spacing: { before: 200, after: 60 }, outlineLevel: 3, keepNext: true } },
      { id: "Heading5", name: "Heading 5", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 21, bold: true, color: "000000", font: { ascii: FONT, hAnsi: FONT, eastAsia: FONT, cs: FONT } }, paragraph: { spacing: { before: 200, after: 60 }, outlineLevel: 4, keepNext: true } },
      { id: "Heading6", name: "Heading 6", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 21, bold: true, color: "000000", font: { ascii: FONT, hAnsi: FONT, eastAsia: FONT, cs: FONT } }, paragraph: { spacing: { before: 200, after: 60 }, outlineLevel: 5, keepNext: true } },
      { id: "Caption", name: "Caption", basedOn: "Normal", next: "Normal", run: { size: 17, color: "000000", font: { ascii: FONT, hAnsi: FONT, eastAsia: FONT, cs: FONT } }, paragraph: { spacing: { after: 200 } } },
    ],
  },
  numbering: { config: [
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 400, hanging: 260 } } } }] },
    ...olConfigs,
  ] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], size: 18 })] })] }) },
    children: body,
  }],
});
const out = path.join(ROOT, "report", "22400498_이건욱_데이터시각화_중간고사_보고서.docx");
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(out, b); console.log("wrote", out, b.length); });
