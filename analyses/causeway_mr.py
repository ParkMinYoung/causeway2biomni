"""
Causeway MR: Lipid → CAD causal inference (BioBank Japan)
Usage: python analyses/causeway_mr.py <path/to/causeway_results.csv>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from biomni_report_pipeline import AnalysisConfig, run_pipeline

LLM_MODEL = "claude-sonnet-4-5"

ANALYSIS_PROMPT = """
You are a Mendelian randomization expert. Analyze the Causeway MR results in the loaded data file.

Perform ALL of the following tasks:

Task 1: Data overview
- List all exposure-outcome pairs present
- Report total number of instruments per exposure
- Identify any missing or anomalous values

Task 2: Primary MR estimates (IVW)
- Extract IVW OR (95% CI) and p-value for each exposure → CAD pair
- Flag pairs meeting genome-wide significance (p < 5e-8 for instruments)

Task 3: Sensitivity analyses
- Report MR-Egger intercept and p-value (pleiotropy test)
- Report weighted median OR and p-value
- Report MR-PRESSO results if available (global test p, outlier-corrected estimates)

Task 4: Heterogeneity assessment
- Cochran Q statistic and p-value per exposure
- I² statistic interpretation

Task 5: Steiger filtering
- Report instruments removed by Steiger filtering
- Confirm causal direction (exposure → outcome)

Task 6: Funnel plot asymmetry
- Note any visual asymmetry from leave-one-out analysis

Task 7: Expert verdict (REQUIRED FORMAT — do not deviate):
VERDICT: [STRONG / MODERATE / WEAK / INSUFFICIENT]
RATIONALE (2-3 sentences): Summarize the overall causal evidence quality.
MAIN_CAVEAT: State the single most important limitation.
IS_CANDIDATE_FALSE_REASON: [Conservative criteria / Pleiotropy / Insufficient power / N/A]

Output all results in structured markdown with tables where appropriate.
"""

LITERATURE_SEARCH_PROMPT = """
You are a systematic literature reviewer. Search PubMed using query_pubmed() for each search below.
Before reporting a paper, verify it passes ALL GATE criteria for that search.
If no papers pass the gate, state: "검색 결과 없음 (해당 카테고리)"
Do NOT report papers that fail the gate. Do NOT fabricate citations.

═══ SEARCH 1: East Asian MR + lipid + CAD (2015–2025) ═══
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
GATE: BBJ must be the OUTCOME population (not just the exposure GWAS source).

═══ REPORTING FORMAT ═══
For each paper passing its gate:
- Citation: Author(s) et al. Title. Journal. Year;Vol:Pages. doi:XXX
- Ancestry and N (exposure and outcome separately)
- Key OR/beta (95% CI) for CAD
- Direction vs European populations (same / opposite / not compared)
- Proposed MECHANISM linking the lipid trait to CAD (1 line, as stated by the paper)
- Gate criterion satisfied: [quote the specific criterion met]
Do NOT alter numbers. If CI not in abstract, state "CI not reported."
"""

REPORT_INSTRUCTIONS = """
Causeway MR 분석 결과를 정리한 과학 리포트를 작성하시오.

LANGUAGE RULE:
- Statistical terms, method names, and abbreviations: keep in English (e.g. IVW, MR-Egger, OR, 95% CI, GSMR, HEIDI, SNP, GWAS)
- All explanatory sentences, interpretations, and conclusions: write in Korean (한국어)
- Section headings: bilingual — e.g. "1. 초록 (Abstract)"

필수 섹션:
1. 초록 (Abstract, ≤250 단어)
2. 서론 (Introduction) — 배경: 지질-CAD MR, 동아시아 맥락
3. 방법 요약 (Methods Summary) — 사용된 MR 기법, 민감도 분석
4. 결과 (Results)
   - Primary IVW estimates 표 (전체 노출 변수)
   - 민감도 분석 요약 표
   - 문헌 맥락: 검증된 문헌만 인용
5. 고찰 (Discussion)
   - 결과 해석
   - 유럽 MR 연구와 비교 ([R1]–[R6] 사용)
   - 한계점
6. 결론 (Conclusion)
7. 참고문헌 (References)
   - [R1]–[R6]: 유럽 지질-CAD MR 표준 참고문헌 (DOI/저자/연도 변경 금지)
   - [A1]–[An]: 검증된 동아시아 문헌 검색 결과 논문만 인용

TITLE RULE: ≤8 단어. 올바른 예) "LDL-C Causes CAD in East Asians". 잘못된 예) "BioBank Japan 데이터를 활용한 동아시아인 지질 형질과 관상동맥질환 간의 멘델 무작위화 연구"
"""


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyses/causeway_mr.py <causeway_results.csv>")
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        print(f"Error: file not found: {csv_path}")
        sys.exit(1)

    config = AnalysisConfig(
        name="causeway_mr",
        data_path="/home/adminrig/src/Biomni/data",
        output_base=Path("result") / "Causeway_MR",
        purpose="BioBank Japan Mendelian randomization: lipid traits → coronary artery disease",
        pdf_title="Causeway MR Report: Lipid → CAD (BioBank Japan)",
        llm_model=LLM_MODEL,
        analysis_prompt=ANALYSIS_PROMPT,
        literature_prompt=LITERATURE_SEARCH_PROMPT,
        report_instructions=REPORT_INSTRUCTIONS,
        csv_path=csv_path,
        no_citation_fallback="동아시아 집단 특이적 대규모 MR 연구 미발견 (No large-scale East-Asian-specific MR study identified).",
    )

    run_pipeline(config)


if __name__ == "__main__":
    main()
