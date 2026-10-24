# 대학 졸업장의 값 — 데이터 시각화 중간고사 (Take-home)

OECD 회원국의 **대졸 임금 프리미엄**(같은 나라·같은 연령대 고졸 전일제 근로자 평균 임금 = 100)을
대졸자 비율, 1인당 GDP, 대졸 고용률과 결합해 탐색(Part A)하고, 하나의 메시지로 설명(Part B)합니다.

> 핵심 메시지: 대졸자가 더 많이 늘어난 나라에서 졸업장 값이 더 떨어지지는 않았다.
> 한국 청년의 낮은 대졸 프리미엄은 '대졸자가 너무 많아서'만으로는 설명되지 않는다.

## 먼저 열어주셔야 할것!

| 순서 | 무엇 | 어디 |
|---|---|---|
| 1 | 보고서 | `report/22400498_이건욱_데이터시각화_중간고사_보고서.docx` |
| 2 | Part A 탐색 대시보드 | https://kunwuk12-gitgit.github.io/datavisualization_midterm/site/dashboard/ (또는 `site/dashboard/index.html`) |
| 3 | Part B 설명 시각화 | https://kunwuk12-gitgit.github.io/datavisualization_midterm/site/story/ (또는 `site/story/index.html`) |

- HTML 파일은 더블클릭하면 브라우저(Chrome·Safari·Edge)에서 열립니다.
"시각화 해주는걸 인터넷 사용이 가능해야 하는걸로 만들어서 인터넷 연결이 필요합니다!"


## Part A 사용법

- 위쪽 노란 4칸에서 **① 국가 · ② 비교 국가 · ③ 연도 · ④ 연령대(25–34세 / 55–64세)**를 고르면
  결론 문장, KPI 카드, 변화표, 차트 3개, 차트별 해석 문장, 세 가지 요점이 모두 함께 바뀝니다.
- 차트의 점을 **클릭**하면 ① 국가, **Shift+클릭**하면 ② 비교 국가가 됩니다.
- **처음 상태로** 버튼 = 기본값(한국 vs 캐나다, 2023년, 25–34세)으로 초기화.
- 색: 파랑 = 선택 국가, 주황 = 비교 국가, 회색 = OECD 평균·다른 나라.

## 폴더 구조

```
data/raw/            OECD 원자료(SDMX 질의 결과, 질의 키·접근일 포함), Gapminder 원본 CSV, 교차검증용 자료
data/processed/      panel.csv(국가×연도 결합 패널), oecd_average.csv, change_2014_2023.csv,
                     robustness_windows.csv, story_facts.json, prep_log.md(전처리 로그)
site/                온라인 게시용 (index.html → dashboard/, story/)
figures/             Part B 차트 PNG, 대시보드 화면 캡처
templates/           HTML 템플릿
prepare_data.py      원자료 → 결합·정제 → data/processed/
validate_collection.py  연도별 수집값과 국가별 수집값 교차 검증 (276개, 불일치 0)
build_dashboard.py   Part A 생성 (Altair → Vega-Lite → HTML)
build_story.py       Part B 생성 (+ PNG)
```

## 재현

```bash
pip install pandas altair vl-convert-python
python prepare_data.py
python validate_collection.py
python build_dashboard.py
python build_story.py
```

## 데이터 출처 (접근일 2026-10-24)

- OECD Education at a Glance — `DF_LSO_EARN_REL_UPPER`(상대임금, 전일제), `DF_LSO_NEAC_DISTR_EA`(학력 분포),
  `DF_LSO_NEAC_EMP`(학력별 고용률). https://www.oecd.org/en/data.html
- Gapminder — GDP per capita (PPP, 2021 int.$, v32), Aged 15–24 unemployment rate (ILOSTAT),
  country entities(지역·World Bank 소득그룹). https://www.gapminder.org/data

## 가산점 관련 자료

1. Part A 온라인 게시  2. Part B 온라인 게시  3. 여러 출처 데이터의 수집·결합·정제 (보고서 3장·7장)
