"""
Generic Biomni Report Pipeline
Stages: 0=prompt generation, 1=analysis, 2=literature, 3=report+pdf
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


def extract_solution(text: str) -> str:
    match = re.search(r"<solution>(.*?)</solution>", text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()


@dataclass
class AnalysisConfig:
    name: str
    data_path: str
    output_base: Path
    purpose: str
    pdf_title: str
    llm_model: str = "claude-sonnet-4-5"
    analysis_prompt: str | None = None
    literature_prompt: str | None = None
    report_instructions: str | None = None
    csv_path: Path | None = None


class RunContext:
    def __init__(self, output_base: Path, csv_path: Path | None = None):
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = output_base / self.run_id
        self.cache_dir = output_base / ".cache"
        self.run_dir.mkdir(parents=True)
        self.cache_dir.mkdir(exist_ok=True)
        self.csv_bytes = csv_path.read_bytes() if csv_path and csv_path.exists() else b""

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

    def save_metadata(self, data: dict):
        (self.run_dir / "00_metadata.json").write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )


def create_cached_agent(config: AnalysisConfig):
    from biomni.agent import A1

    agent = A1(path=config.data_path, llm=config.llm_model, use_tool_retriever=False)
    if isinstance(agent.system_prompt, str):
        agent.system_prompt = [
            {
                "type": "text",
                "text": agent.system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ]
    return agent


def stream_and_capture(agent, prompt: str, label: str) -> str:
    seen: set[str] = set()
    all_chunks: list[str] = []
    step = 0
    for chunk in agent.go_stream(prompt):
        raw = chunk.get("output", "")
        all_chunks.append(raw)
        new = [ln for ln in raw.splitlines() if ln not in seen]
        seen.update(raw.splitlines())
        if new:
            step += 1
            print(f"\n--- [{label}] Step {step} ---")
            print("\n".join(new), flush=True)
    return extract_solution("\n".join(all_chunks))


def generate_stage_prompts(config: AnalysisConfig, sample_data: str) -> None:
    """Stage 0: call Claude to generate prompts when none are pre-provided."""
    import anthropic

    client = anthropic.Anthropic()

    system = (
        "You are an expert bioinformatics analyst. "
        "Given an analysis purpose and sample data, generate three prompts for a biomni agent pipeline. "
        "Return ONLY valid JSON with keys: analysis_prompt, literature_prompt, report_instructions."
    )

    user_content = f"""Analysis purpose:
{config.purpose}

Sample data (first rows):
{sample_data[:3000]}

Generate:
1. analysis_prompt: Detailed prompt instructing biomni to perform statistical analysis of the data.
   Must include Tasks 1-7 with Task 7 using this REQUIRED FORMAT:
   VERDICT: [STRONG/MODERATE/WEAK/INSUFFICIENT]
   RATIONALE (2-3 sentences): ...
   MAIN_CAVEAT: ...

2. literature_prompt: PubMed search prompt with 3-4 targeted searches.
   Each search must include a GATE filter: specific inclusion criteria and explicit rejection list.
   Format: query_pubmed() calls + GATE criteria + reporting format with DOI required.

3. report_instructions: Rules for the final report.
   Must include: title ≤8 words, citations only from verified DOIs in literature results,
   numerical values must match analysis output exactly.

Return JSON only, no markdown fences."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    )

    raw = message.content[0].text.strip()
    # strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

    prompts = json.loads(raw)
    config.analysis_prompt = prompts["analysis_prompt"]
    config.literature_prompt = prompts["literature_prompt"]
    config.report_instructions = prompts["report_instructions"]
    print("[Stage 0] Prompts generated via Claude.", flush=True)


def run_stage_1(agent, ctx: RunContext, config: AnalysisConfig) -> str:
    key = ctx.compute_hash([ctx.csv_bytes, (config.analysis_prompt or "").encode()])
    if cached := ctx.load_cached("analysis", key):
        print("[CACHE HIT] Stage 1: analysis", flush=True)
        ctx.save_stage("01_analysis.md", cached)
        return cached
    print("[Stage 1] Running analysis...", flush=True)
    result = stream_and_capture(agent, config.analysis_prompt, "ANALYSIS")
    ctx.save_cached("analysis", key, result)
    ctx.save_stage("01_analysis.md", result)
    return result


def run_stage_2(agent, ctx: RunContext, config: AnalysisConfig) -> str:
    key = ctx.compute_hash([(config.literature_prompt or "").encode(), config.llm_model.encode()])
    if cached := ctx.load_cached("literature", key):
        print("[CACHE HIT] Stage 2: literature", flush=True)
        ctx.save_stage("02_literature.md", cached)
        return cached
    print("[Stage 2] Searching literature...", flush=True)
    _, raw = agent.go(config.literature_prompt)
    result = extract_solution(raw)
    ctx.save_cached("literature", key, result)
    ctx.save_stage("02_literature.md", result)
    return result


def _build_report_prompt(config: AnalysisConfig, lit_text: str) -> str:
    import re
    verified_dois = re.findall(r"doi:\S+", lit_text, re.IGNORECASE)
    n = len(verified_dois)
    citation_rule = (
        f"[A*] citations: use ONLY the {n} verified references ([A1]–[A{n}])."
        if n > 0
        else "[A*] citation format is FORBIDDEN — no verified East-Asian-specific MR papers found. "
             "Replace with: 'No large-scale East-Asian-specific MR study identified.'"
    )

    return f"""{config.report_instructions or ''}

LITERATURE RESULTS (use these references only):
{lit_text}

ADDITIONAL RULES:
1. Title: ≤8 words.
2. {citation_rule}
3. All numerical values must match the analysis output exactly (±0.001 tolerance).
4. Structure: Abstract → Methods Summary → Results → Discussion → References
"""


def run_stage_3(agent, ctx: RunContext, config: AnalysisConfig, lit_text: str) -> str:
    key = ctx.compute_hash([ctx.csv_bytes, lit_text.encode(), config.llm_model.encode()])
    if cached := ctx.load_cached("report", key):
        print("[CACHE HIT] Stage 3: report", flush=True)
        ctx.save_stage("03_report.md", cached)
        return cached
    print("[Stage 3] Writing report...", flush=True)
    prompt = _build_report_prompt(config, lit_text)
    _, raw = agent.go(prompt)
    result = extract_solution(raw)
    ctx.save_cached("report", key, result)
    ctx.save_stage("03_report.md", result)
    return result


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>{{ title }}</title>
<style>
  body { font-family: "Noto Serif", Georgia, serif; max-width: 860px; margin: 40px auto; padding: 0 24px; line-height: 1.7; color: #1a1a1a; }
  h1 { font-size: 1.8em; border-bottom: 2px solid #333; padding-bottom: 8px; }
  h2 { font-size: 1.3em; border-bottom: 1px solid #ccc; margin-top: 2em; }
  h3 { font-size: 1.1em; }
  table { border-collapse: collapse; width: 100%; margin: 1em 0; }
  th, td { border: 1px solid #bbb; padding: 6px 10px; text-align: left; }
  th { background: #f4f4f4; }
  code { background: #f4f4f4; padding: 2px 4px; border-radius: 3px; font-size: 0.9em; }
  blockquote { border-left: 3px solid #ccc; margin-left: 0; padding-left: 16px; color: #555; }
  @page { margin: 2cm; }
</style>
</head>
<body>
{{ body }}
</body>
</html>"""


def render_pdf(report_md_path: Path, output_path: Path, title: str):
    try:
        import markdown as md_lib
        from jinja2 import Template
    except ImportError:
        print("[render_pdf] 'markdown' package missing. Run: pip install markdown", file=sys.stderr)
        return

    md_text = report_md_path.read_text(encoding="utf-8")
    body_html = md_lib.markdown(
        md_text,
        extensions=["tables", "fenced_code", "toc"],
    )
    html = Template(_HTML_TEMPLATE).render(title=title, body=body_html)

    html_path = output_path.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")

    try:
        import weasyprint
        weasyprint.HTML(string=html, base_url=str(output_path.parent)).write_pdf(str(output_path))
        print(f"[PDF] Saved: {output_path}", flush=True)
    except ImportError:
        print(
            f"[render_pdf] weasyprint not installed — HTML saved to {html_path}\n"
            "  Install: pip install weasyprint",
            file=sys.stderr,
        )
    except Exception as e:
        print(f"[render_pdf] WeasyPrint error ({e}) — HTML saved to {html_path}", file=sys.stderr)


def update_symlinks(output_base: Path, run_dir: Path, name: str):
    pairs = [
        ("report.md", run_dir / "03_report.md"),
        (f"{name}_report.pdf", run_dir / f"{name}_report.pdf"),
        (f"{name}_report.html", run_dir / f"{name}_report.html"),
    ]
    for link_name, target in pairs:
        if not target.exists():
            continue
        link = output_base / link_name
        if link.is_symlink() or link.exists():
            link.unlink()
        link.symlink_to(target.resolve())


def run_pipeline(config: AnalysisConfig):
    t0 = datetime.now()
    config.output_base.mkdir(parents=True, exist_ok=True)

    ctx = RunContext(config.output_base, config.csv_path)
    print(f"[Pipeline] Run ID: {ctx.run_id} | Output: {ctx.run_dir}", flush=True)

    # Stage 0: generate prompts if not pre-provided
    if config.analysis_prompt is None:
        sample = ""
        if config.csv_path and config.csv_path.exists():
            lines = config.csv_path.read_text(encoding="utf-8", errors="replace").splitlines()
            sample = "\n".join(lines[:50])
        generate_stage_prompts(config, sample)

    agent = create_cached_agent(config)

    analysis_text = run_stage_1(agent, ctx, config)
    lit_text = run_stage_2(agent, ctx, config)
    run_stage_3(agent, ctx, config, lit_text)

    pdf_path = ctx.run_dir / f"{config.name}_report.pdf"
    render_pdf(ctx.run_dir / "03_report.md", pdf_path, config.pdf_title)

    elapsed = (datetime.now() - t0).total_seconds()
    ctx.save_metadata({
        "run_id": ctx.run_id,
        "analysis": config.name,
        "model": config.llm_model,
        "elapsed_sec": round(elapsed, 1),
        "stages_cached": [],
    })

    update_symlinks(config.output_base, ctx.run_dir, config.name)
    print(f"\n[Pipeline] Done in {elapsed:.0f}s → {ctx.run_dir}", flush=True)
