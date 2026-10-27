"""Build downloadable TXT and PDF reports from analysis results."""
import re
from datetime import date

from fpdf import FPDF

DISCLAIMER = ("The match score is an AI-generated estimate, not a real ATS score or a guarantee of selection. "
              "AI-generated suggestions must be reviewed for accuracy before use.")


def _sections(result: dict, improvements: dict | None) -> list:
    s = [("Overall Assessment", result["summary"]),
         ("Score Breakdown", [f"{r['label']}: {r['score']}/{r['max']} - {r['comment']}" for r in result["rubric"].values()]),
         ("Matching Skills", result["matching_skills"]),
         ("Missing Skills", result["missing_skills"]),
         ("Experience Analysis", result["experience_analysis"]),
         ("Education Match", result["education_match"]),
         ("Strengths", result["strengths"]),
         ("Areas to Improve", result["areas_to_improve"]),
         ("ATS-Friendly Suggestions", result["ats_suggestions"]),
         ("Recommended Learning Topics", result["learning_topics"])]
    if improvements:
        s.append(("Summary Suggestions (AI-generated, review before use)", improvements["summary_suggestions"]))
        s.append(("Bullet Rewrites (AI-generated, review before use)",
                  [f"Original: {b['original']}\n  Improved: {b['improved']}" for b in improvements["bullet_rewrites"]]))
        s.append(("Suggested Keywords (add only if true for you)", [", ".join(improvements["keywords"])] if improvements["keywords"] else []))
    return [(t, c) for t, c in s if c]


def build_text_report(result: dict, improvements: dict | None = None) -> str:
    out = ["AI RESUME ANALYSIS REPORT", f"Generated: {date.today():%Y-%m-%d}", "",
           f"MATCH SCORE (estimate): {result['score']}/100", DISCLAIMER, ""]
    for title, content in _sections(result, improvements):
        out += [title.upper(), "-" * len(title)]
        out += [f"- {c}" for c in content] if isinstance(content, list) else [content]
        out.append("")
    return "\n".join(out)


def _s(text) -> str:
    t = str(text)
    for a, b in {"•": "-", "–": "-", "—": "-", "’": "'", "‘": "'", "“": '"', "”": '"', "…": "..."}.items():
        t = t.replace(a, b)
    t = t.encode("latin-1", "replace").decode("latin-1")
    return re.sub(r"(\S{60})(?=\S)", r"\1 ", t)  # keep very long tokens wrappable


def build_pdf_report(result: dict, improvements: dict | None = None) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(True, 15)
    pdf.add_page()

    def line(text, size=10, style="", h=6):
        pdf.set_font("Helvetica", style, size)
        pdf.multi_cell(0, h, _s(text), new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(15, 23, 42)
    line("AI Resume Analysis Report", 20, "B", 10)
    line(f"Generated {date.today():%Y-%m-%d}", 9)
    pdf.ln(3)
    pdf.set_text_color(37, 99, 235)
    line(f"Match score (estimate): {result['score']}/100", 14, "B", 8)
    pdf.set_text_color(100, 116, 139)
    line(DISCLAIMER, 8, "I", 5)
    for title, content in _sections(result, improvements):
        pdf.ln(3)
        pdf.set_text_color(30, 41, 100)
        line(title, 12, "B", 8)
        pdf.set_text_color(15, 23, 42)
        for c in (content if isinstance(content, list) else [content]):
            line(("- " + c) if isinstance(content, list) else c)
    return bytes(pdf.output())
