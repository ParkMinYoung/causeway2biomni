# 계획: Causeway 리포트 파이프라인 v2 설계

## Context

`biomni_causeway_report.py`는 Causeway MR 결과를 3단계(분석 → 문헌 검색 → 리포트)로 처리하지만 세 가지 핵심 문제가 있다:

1. **캐싱 없음**: 42K 토큰 시스템 프롬프트가 스텝마다 전송됨 (3단계 × ~10스텝 = 약 $3-4/회)
2. **덮어쓰기**: 출력 파일명이 고정(`report.md`, `BBJ_CAD_report.pdf`) → 이전 결과 소실
3. **창작 발생**: Stage 1 출력이 저장 안 됨 / Literature 검색이 무관한 논문 반환 → 모델이 [A1],[A2] 위조 인용 생성

목적: 비용·품질 동시 최적화를 위한 `biomni_causeway_report_v2.py` 신규 작성 (원본 유지).

---

## 출력 디렉토리 구조

```
result/
├── .cache/                        # 스테이지별 디스크 캐시 (run 간 공유)
│   ├── analysis_<hash12>.md
│   ├── literature_<hash12>.md
│   └── report_<hash12>.md
├── 20260605_143022/               # 타임스탬프 run 디렉토리 (덮어쓰기 없음)
│   ├── 00_metadata.json           # hash, model, elapsed, token_estimate
│   ├── 01_analysis.md             # Stage 1 저장 (현재 미저장)
│   ├── 02_literature.md           # Stage 2 저장
│   ├── 03_report.md               # Stage 3 저장
│   └── BBJ_CAD_report.pdf
├── report.md  -> [latest]/03_report.md          # 하위 호환 심볼릭 링크
└── BBJ_CAD_report.pdf -> [latest]/BBJ_CAD_report.pdf
```

---

## 구현 계획

### 1. 신규 파일 생성
`/home/adminrig/src/Biomni/biomni_causeway_report_v2.py`  
원본 `biomni_causeway_report.py` 유지 (실행 불가하게 변경하지 말 것)

### 2. 핵심 신규 컴포넌트

#### `RunContext` 클래스
```python
class RunContext:
    def __init__(self, output_base: Path, csv_path: Path):
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = output_base / self.run_id
        self.cache_dir = output_base / ".cache"
        self.run_dir.mkdir(parents=True)
        self.cache_dir.mkdir(exist_ok=True)
        self.csv_bytes = csv_path.read_bytes()
        self.metadata = {"run_id": self.run_id}

    def compute_hash(self, inputs: list) -> str:
        h = hashlib.sha256()
        for x in inputs:
            h.update(x if isinstance(x, bytes) else x.encode())
        return h.hexdigest()[:12]

    def load_cached(self, stage: str, key: str) -> str | None:
        f = self.cache_dir / f"{stage}_{key}.md"
        return f.read_text(encoding="utf-8") if f.exists() else None

    def save_cached(self, stage: str, key: str, content: str):
        (self.cache_dir / f"{stage}_{key}.md").write_text(content, encoding="utf-8")

    def save_stage(self, filename: str, content: str) -> Path:
        p = self.run_dir / filename
        p.write_text(content, encoding="utf-8")
        return p
```

#### `create_cached_agent()` — API 캐시 주입
```python
def create_cached_agent(data_path: str, llm_model: str):
    from biomni.agent import A1
    # use_tool_retriever=False: update_system_prompt_with_selected_resources()가
    # system_prompt를 덮어쓰지 못하게 차단 (cache_control 블록 보존)
    agent = A1(path=data_path, llm=llm_model, use_tool_retriever=False)
    # 42K 토큰 시스템 프롬프트를 ephemeral 캐시 블록으로 래핑
    agent.system_prompt = [{
        "type": "text",
        "text": agent.system_prompt,
        "cache_control": {"type": "ephemeral"},
    }]
    return agent
```
**근거**: langchain_anthropic v1.4.4는 `SystemMessage(content=[...])` 리스트를 그대로 API에 전달함. `generate()` 클로저가 매 스텝 `self.system_prompt`를 동적으로 읽으므로 패치가 모든 호출에 적용됨. 절감 효과: ~1.1M 토큰/회 ≈ $3.3 절감.

#### `stream_and_capture()` — Stage 1 출력 보존 (현재 `stream_with_progress` 대체)
```python
def stream_and_capture(agent, prompt: str, label: str) -> str:
    seen: set[str] = set()
    all_chunks: list[str] = []
    step = 0
    for chunk in agent.go_stream(prompt):
        raw = chunk["output"]
        all_chunks.append(raw)
        new = [ln for ln in raw.splitlines() if ln not in seen]
        seen.update(raw.splitlines())
        if new:
            step += 1
            print(f"\n--- [{label}] Step {step} ---")
            print("\n".join(new), flush=True)
    return extract_solution("\n".join(all_chunks))
```
현재 `stream_with_progress()`는 `last_output`만 반환하여 분석 내용이 소실됨. 수정 버전은 전체 스트림을 축적한 후 `<solution>` 추출.

### 3. 단계별 함수

```python
def run_stage_1(agent, ctx: RunContext) -> str:
    key = ctx.compute_hash([ctx.csv_bytes, ANALYSIS_PROMPT.encode()])
    if cached := ctx.load_cached("analysis", key):
        ctx.save_stage("01_analysis.md", cached)
        return cached
    result = stream_and_capture(agent, ANALYSIS_PROMPT, "ANALYSIS")
    ctx.save_cached("analysis", key, result)
    ctx.save_stage("01_analysis.md", result)
    return result

def run_stage_2(agent, ctx: RunContext) -> str:
    key = ctx.compute_hash([LITERATURE_SEARCH_PROMPT.encode(), LLM_MODEL.encode()])
    if cached := ctx.load_cached("literature", key):
        ctx.save_stage("02_literature.md", cached)
        return cached
    _, raw = agent.go(LITERATURE_SEARCH_PROMPT)
    result = extract_solution(raw)
    ctx.save_cached("literature", key, result)
    ctx.save_stage("02_literature.md", result)
    return result

def run_stage_3(agent, ctx: RunContext, lit_text: str) -> str:
    key = ctx.compute_hash([ctx.csv_bytes, lit_text.encode(), LLM_MODEL.encode()])
    if cached := ctx.load_cached("report", key):
        ctx.save_stage("03_report.md", cached)
        return cached
    prompt = build_report_prompt(lit_text)
    _, raw = agent.go(prompt)
    result = extract_solution(raw)
    ctx.save_cached("report", key, result)
    ctx.save_stage("03_report.md", result)
    return result
```

**캐시 키 설계**: Stage 2(문헌)는 CSV에 독립적 (LLM_MODEL 포함 → 모델 업그레이드 시 무효화). Stage 3은 `lit_text`를 키에 포함 → 문헌 결과가 바뀌면 리포트도 재생성.

---

## 프롬프트 최적화

### ANALYSIS_PROMPT — Task 7 구조화
변경 최소화. Task 7의 자유형 서술을 고정 템플릿으로 교체:
```
7. Expert verdict (REQUIRED FORMAT):
   VERDICT: [STRONG / MODERATE / WEAK / INSUFFICIENT]
   RATIONALE (2-3 sentences): ...
   MAIN_CAVEAT: ...
   IS_CANDIDATE_FALSE_REASON: [Conservative criteria / Pleiotropy / Insufficient power]
```
나머지 Task 1-6은 현행 유지 (이미 적절함).

### LITERATURE_SEARCH_PROMPT — 4개 타겟 검색 + GATE 필터 (핵심 개선)

현재 문제: 3개 광범위 검색 → ALS·통풍·담낭염 논문 반환 → [A1][A2] 위조 인용 발생

```python
LITERATURE_SEARCH_PROMPT = """
You are a systematic literature reviewer. Search PubMed using query_pubmed() for each search.
Before reporting a paper, verify it passes ALL GATE criteria for that search.
If no papers pass the gate, state: "검색 결과 없음 (해당 카테고리)"
Do NOT report papers that fail the gate. Do NOT fabricate citations.

═══ SEARCH 1: East Asian MR + lipid + CAD (2015-2025) ═══
Query: ("Mendelian randomization" OR "Mendelian randomisation") AND
       ("LDL" OR "HDL" OR "triglyceride" OR "non-HDL") AND
       ("coronary artery disease" OR "myocardial infarction") AND
       ("East Asian" OR "Japanese" OR "Korean" OR "Chinese" OR "BioBank Japan")
GATE: Must use MR AND report OR/beta specifically for CAD/MI as primary outcome.
      REJECT papers about: ALS, gout, gallstones, endometriosis, liver disease.

═══ SEARCH 2: GSMR method + lipid + CAD ═══
Query: "GSMR" AND ("LDL" OR "HDL" OR "lipid") AND ("coronary" OR "CAD")
GATE: Must apply GSMR (not merely cite it) AND report GSMR OR/beta for CAD.

═══ SEARCH 3: Cross-ancestry lipid-CAD MR ═══
Query: ("cross-ancestry" OR "trans-ethnic" OR "multi-ancestry") AND
       "Mendelian randomization" AND ("LDL" OR "HDL" OR "lipid") AND
       ("coronary artery disease" OR "CAD")
GATE: Must include East Asian/BBJ samples AND compare effect sizes across ancestries.

═══ SEARCH 4: BioBank Japan as MR outcome ═══
Query: "BioBank Japan" AND "Mendelian randomization" AND
       ("coronary artery disease" OR "myocardial infarction" OR "CAD")
GATE: BBJ must be the OUTCOME population (not just exposure GWAS source).

═══ REPORTING FORMAT ═══
For each paper passing its gate:
- Citation: Author(s) et al. Title. Journal. Year;Vol:Pages. doi:XXX
- Ancestry and N (exposure and outcome separately)
- Key OR/beta (95% CI) for CAD
- Direction vs European populations (same / opposite / not compared)
- Gate criterion satisfied: [quote the specific criterion met]
Do NOT alter numbers. If CI not in abstract, state "CI not reported."
"""
```

### REPORT_PROMPT — 3가지 추가 규칙

`build_report_prompt()` 함수 내 지시문에 다음 추가:

```python
# 검증된 [A*] 인용 수 자동 계산 → 프롬프트에 주입
import re
verified_dois = re.findall(r'doi:\S+', lit_text, re.IGNORECASE)
n_asian = len(verified_dois)
asian_citation_rule = (
    f"[A*] 인용: 검증된 {n_asian}개 문헌만 사용 가능 ([A1]~[A{n_asian}])."
    if n_asian > 0
    else "[A*] 형식 인용 금지 — 검증된 동아시아 특이적 문헌 없음. '동아시아 집단 특이적 대규모 MR 연구 미발견'으로 대체."
)
```

지시문에 추가할 3개 규칙:
1. **제목**: ≤8 어절 (준수 예시/위반 예시 함께 제시)
2. **인용**: `{asian_citation_rule}` 동적 삽입; [R1]-[R6] 저자·연도·DOI 변경 금지
3. **수치**: 표 수치와 ±0.001 이상 차이 있으면 오류

---

## 심볼릭 링크 (하위 호환성)

```python
def update_symlinks(output_base: Path, run_dir: Path):
    for name, src in [("report.md", "03_report.md"),
                      ("BBJ_CAD_report.pdf", "BBJ_CAD_report.pdf")]:
        link = output_base / name
        if link.is_symlink() or link.exists():
            link.unlink()
        link.symlink_to(run_dir / src)
```

---

## 수정 대상 파일

| 파일 | 액션 |
|------|------|
| `/home/adminrig/src/Biomni/biomni_causeway_report_v2.py` | 신규 생성 |
| `/home/adminrig/src/Biomni/biomni_causeway_report.py` | 변경 없음 (유지) |

---

## 비용 절감 추정

| 항목 | 현행 | v2 |
|------|------|-----|
| API 캐시 (시스템 프롬프트 42K × 30스텝) | ~1.26M 토큰 | ~42K 토큰 (97% 절감) |
| 디스크 캐시 히트 (동일 CSV 재실행) | 전체 재실행 | 0 API 호출 |
| 오염 문헌 → 위조 인용 수정 재실행 비용 | 반복 발생 | GATE 필터로 예방 |
| 예상 비용/회 | ~$4-5 | ~$0.5 (첫 실행) / $0 (캐시 히트) |

---

## 검증 방법

1. 첫 실행: `python biomni_causeway_report_v2.py` → `result/20260605_XXXXXX/` 디렉토리 생성 확인
2. 두 번째 실행(동일 CSV): 모든 단계 `[CACHE HIT]` 출력 확인, 새 타임스탬프 디렉토리 생성 확인
3. 문헌 결과 확인: `02_literature.md`에서 ALS·통풍·담낭염 관련 논문 없음 확인
4. 인용 검증: `03_report.md`에서 [A*] 인용이 `02_literature.md`에 실제 존재하는 DOI만 사용하는지 확인
5. 제목 길이: 리포트 1행 제목의 어절 수 ≤8 확인
6. 심볼릭 링크: `result/report.md`가 최신 run으로 연결되는지 확인
7. 덮어쓰기 방지: 이전 run 디렉토리 파일 내용 변경 없음 확인
