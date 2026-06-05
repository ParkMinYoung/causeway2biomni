# Biomin Report Pipeline

Biomni A1 에이전트 기반 생물정보학 분석 리포트 자동 생성 파이프라인.

## 특징

- **3단계 파이프라인**: 통계 분석 → 문헌 검색 → 리포트 생성 (Markdown + PDF)
- **디스크 캐시**: 동일 입력 재실행 시 API 호출 없이 캐시에서 즉시 반환
- **API 프롬프트 캐싱**: 42K 토큰 시스템 프롬프트를 `cache_control: ephemeral`로 캐시 (~$3.3/회 절감)
- **결과 보존**: 타임스탬프 디렉토리로 이전 실행 결과 덮어쓰기 없음
- **위조 인용 방지**: GATE 필터로 관련 없는 논문 차단, 검증된 DOI만 인용

## 요구사항

```bash
pip install weasyprint markdown jinja2  # PDF 생성용
# Biomni A1 에이전트: /home/adminrig/src/Biomni 설치 필요
```

## 사용법

### 1. Causeway MR 분석 (사전 구성됨)

BioBank Japan 지질→관상동맥질환 MR 분석:

```bash
cd /home/adminrig/claude/biomin
python analyses/causeway_mr.py <causeway_results.csv>
```

**출력:**
```
result/
├── .cache/                        # 스테이지별 캐시 (run 간 공유)
├── 20260605_164758/               # 타임스탬프 run 디렉토리
│   ├── 00_metadata.json
│   ├── 01_analysis.md             # Stage 1: MR 통계 분석
│   ├── 02_literature.md           # Stage 2: PubMed 문헌 검색
│   ├── 03_report.md               # Stage 3: 최종 리포트
│   └── causeway_mr_report.pdf
├── report.md -> [latest]/03_report.md
└── causeway_mr_report.pdf -> [latest]/...
```

**재실행 (캐시 히트):** 동일 CSV로 재실행하면 API 호출 없이 `[CACHE HIT]`로 처리됨.

### 2. 새 분석 추가 (`/biomni-report` 슬래시 커맨드)

Claude Code에서 새 분석 타입을 설정할 때:

```
/biomni-report <analysis_name>
```

Claude가 데이터 파일과 분석 목적을 물어보고 `analyses/<name>.py`를 자동 생성 후 파이프라인을 실행합니다.

### 3. 직접 스크립트 작성

`analyses/causeway_mr.py`를 참고해 새 분석 스크립트 작성:

```python
from biomni_report_pipeline import AnalysisConfig, run_pipeline

config = AnalysisConfig(
    name="my_analysis",
    data_path="/path/to/biomni/data",   # Biomni A1 데이터 디렉토리
    output_base=Path("result"),
    purpose="분석 목적 한 줄 설명",
    pdf_title="PDF 제목",
    llm_model="claude-sonnet-4-5",
    analysis_prompt=ANALYSIS_PROMPT,
    literature_prompt=LITERATURE_SEARCH_PROMPT,
    report_instructions=REPORT_INSTRUCTIONS,
    csv_path=Path("data/results.csv"),
)

run_pipeline(config)
```

## 파이프라인 구조

```
biomni_report_pipeline.py   # 공통 엔진
analyses/
├── causeway_mr.py          # Causeway MR 분석 (BioBank Japan)
└── <new_analysis>.py       # 추가 분석
result/                     # 실행 결과 (gitignore 제외)
docs/design.md              # 설계 문서
```

## 캐시 동작

| 상황 | 동작 |
|------|------|
| 첫 실행 | 전체 API 호출, 결과를 `.cache/`에 저장 |
| 동일 CSV 재실행 | 모든 스테이지 `[CACHE HIT]`, API 호출 없음 |
| CSV 변경 후 재실행 | Stage 1,3 재실행 (Stage 2 문헌 검색은 캐시 유지) |
| 프롬프트 수정 후 재실행 | 해당 스테이지 이후만 재실행 |

캐시 초기화: `rm -rf result/.cache/`

## 비용

| 항목 | 비용 |
|------|------|
| 첫 실행 (API 캐시 적용) | ~$0.5 |
| 재실행 (디스크 캐시 히트) | $0 |
| API 캐시 없을 경우 | ~$4–5 |
