# /biomni-report

Run this command to set up and execute a new biomni analysis report pipeline.

## What this command does

1. Reads the user's analysis purpose and data files (결과 파일 + 분석 목적)
2. Builds optimal context — generates stage-specific prompts (analysis → literature → report)
3. Creates `analyses/<name>.py` with the generated config
4. Runs the full pipeline: statistical analysis → multi-reference literature search with
   result-vs-literature direction & mechanism consistency check → researcher-perspective
   report (가설→증거→기전→설명→결론 + 용어 설명) → self-review & optimization → markdown + PDF

## Steps

### Step 1: Get analysis name and inputs

Ask the user for:
- **Analysis name** (from `$ARGUMENTS`, or ask if empty): short identifier, e.g. `gwas_prs`, `proteomics_ad`
- **Purpose file**: path to a `.md` or `.txt` describing what the analysis is, what data was used, and what questions it answers
- **Data file**: path to the primary result file (CSV, TSV, etc.)

Read both files using the Read tool.

### Step 2: Understand the analysis

Read the purpose file and the first 50 rows of the data file. Identify:
- What biological question is being asked
- What statistical method was used
- What the key columns/metrics are
- What the expected output should look like
- What literature context is needed (species, disease, population, method)

### Step 3: Generate the three prompts

Based on your understanding, write:

**ANALYSIS_PROMPT**: Instructions for biomni agent to perform the statistical analysis.
- Must cover Tasks 1–7 (overview → estimates → sensitivity → heterogeneity → filtering → visual → verdict)
- Task 7 MUST use this exact format:
  ```
  VERDICT: [STRONG / MODERATE / WEAK / INSUFFICIENT]
  RATIONALE (2-3 sentences): ...
  MAIN_CAVEAT: ...
  ```
- Reference the actual column names from the data file

**LITERATURE_SEARCH_PROMPT**: PubMed search instructions.
- 3–4 targeted searches using `query_pubmed()`
- Each search has a GATE filter: explicit inclusion criteria + explicit REJECT list for off-topic papers
- Reporting format must require DOI for every cited paper AND capture both the effect
  DIRECTION and the proposed biological MECHANISM (so the report can later judge agreement)
- Final instruction: "Do NOT fabricate citations."

**REPORT_INSTRUCTIONS**: Rules for the final report (Korean body text).
- LANGUAGE RULE: statistical terms/abbreviations in English; all explanatory sentences in Korean (한국어)
- Section headings: bilingual format — e.g. "1. 초록 (Abstract)"
- Title ≤8 단어 (with correct/incorrect examples)
- Citations: use only DOIs verified in the literature results
- Numerical values must match analysis output exactly (±0.001)
- Required sections: 초록 → 서론 → 방법 요약 → 결과 → 고찰 → 결론 → 참고문헌
- Researcher-perspective reasoning chain and 용어 설명 (Glossary) are appended automatically by
  the engine (`DEFAULT_RESEARCHER_FRAMING`); set `report_structure`/`glossary=False` only to override.
  No need to restate them here.

> The engine runs **Stage 4 (self-review & optimization)** automatically: it re-checks every
> number against the analysis, validates citations, verifies each mechanism/direction verdict,
> and rewrites the draft into the final `04_report.md`. Disable with `review=False` if not wanted.

### Step 4: Create the analysis file

Create `analyses/<name>.py` using this template:

```python
"""
<Analysis title>
Usage: python analyses/<name>.py <path/to/data.csv>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from biomni_report_pipeline import AnalysisConfig, run_pipeline

LLM_MODEL = "claude-opus-4-5"

ANALYSIS_PROMPT = """<generated analysis prompt>"""

LITERATURE_SEARCH_PROMPT = """<generated literature prompt>"""

REPORT_INSTRUCTIONS = """<generated report instructions>"""


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyses/<name>.py <data_file>")
        sys.exit(1)

    data_path = Path(sys.argv[1])
    if not data_path.exists():
        print(f"Error: file not found: {data_path}")
        sys.exit(1)

    config = AnalysisConfig(
        name="<name>",
        data_path=str(data_path.parent),
        output_base=Path("result") / "<DISPLAY_NAME>",  # e.g. "GWAS_PRS", "Proteomics_AD"
        purpose="<one-line purpose>",
        pdf_title="<PDF title>",
        llm_model=LLM_MODEL,
        analysis_prompt=ANALYSIS_PROMPT,
        literature_prompt=LITERATURE_SEARCH_PROMPT,
        report_instructions=REPORT_INSTRUCTIONS,
        csv_path=data_path,
    )

    run_pipeline(config)


if __name__ == "__main__":
    main()
```

### Step 5: Run the pipeline

Execute: `python analyses/<name>.py <data_file_path>`

Monitor output for:
- `[CACHE HIT]` lines (normal on re-runs)
- `[Stage N]` progress lines
- `[PDF] Saved:` confirmation
- Final `[Pipeline] Done in Xs` line

Report the output directory and PDF path to the user.

## Notes

- **Causeway MR** already has pre-written prompts in `analyses/causeway_mr.py` — run it directly without this command
- **New analyses**: this command generates prompts tailored to the specific data structure
- If weasyprint is not installed, a `.html` file is saved instead — tell the user to run `pip install weasyprint` for PDF output
- The `result/.cache/` directory persists across runs — identical inputs reuse cached stage outputs at zero API cost
