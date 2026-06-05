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
- Gate criterion satisfied: [quote the specific criterion met]
Do NOT alter numbers. If CI not in abstract, state "CI not reported."
"""

REPORT_INSTRUCTIONS = """
Write a structured scientific report summarizing the Causeway MR analysis results.

Required sections:
1. Abstract (≤250 words)
2. Introduction (background on lipid-CAD MR, East Asian context)
3. Methods Summary (MR methods used, sensitivity analyses)
4. Results
   - Primary IVW estimates table (all exposures)
   - Sensitivity analysis summary
   - Literature context: cite only papers from the verified literature results
5. Discussion
   - Interpretation of findings
   - Comparison with European MR studies (use [R1]–[R6] for European refs)
   - Limitations
6. Conclusion
7. References
   - [R1]–[R6]: Standard European lipid-CAD MR references (do NOT alter DOI/author/year)
   - [A1]–[An]: Only papers from the verified East Asian literature search above

TITLE RULE: ≤8 words. Correct: "LDL-C Causes CAD in East Asians". Wrong: "Mendelian Randomization Study Investigating the Causal Role of Lipids in Coronary Artery Disease Among East Asian Populations"
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
        output_base=Path("result"),
        purpose="BioBank Japan Mendelian randomization: lipid traits → coronary artery disease",
        pdf_title="Causeway MR Report: Lipid → CAD (BioBank Japan)",
        llm_model=LLM_MODEL,
        analysis_prompt=ANALYSIS_PROMPT,
        literature_prompt=LITERATURE_SEARCH_PROMPT,
        report_instructions=REPORT_INSTRUCTIONS,
        csv_path=csv_path,
    )

    run_pipeline(config)


if __name__ == "__main__":
    main()
