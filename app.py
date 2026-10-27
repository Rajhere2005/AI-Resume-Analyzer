"""AI Resume Analyzer: Streamlit front end."""
import html
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src import analyzer, report  # noqa: E402
from src.resume_parser import ResumeParseError, extract_text  # noqa: E402

st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="wide")
st.markdown(f"<style>{(Path(__file__).parent / 'styles.css').read_text()}</style>", unsafe_allow_html=True)

ss = st.session_state
for k, v in {"uploader_key": 0, "resume_text": None, "parse_error": None, "sig": None,
             "result": None, "improvements": None, "jd": ""}.items():
    ss.setdefault(k, v)


# ---------- helpers (all AI/user text is HTML-escaped before rendering) ----------
def e(x) -> str:
    return html.escape(str(x))


def chips(items, kind) -> str:
    return "".join(f'<span class="chip {kind}">{e(i)}</span>' for i in items) or '<span class="muted">None identified</span>'


def ul(items) -> str:
    return ('<ul class="clean">' + "".join(f"<li>{e(i)}</li>" for i in items) + "</ul>") if items else '<span class="muted">Nothing to show.</span>'


def reset():
    ss.uploader_key += 1
    ss.jd = ""
    for k in ("resume_text", "parse_error", "sig", "result", "improvements"):
        ss[k] = None


def score_style(score):
    if score >= 75:
        return "#15803D", "#DCFCE7", "Strong match"
    if score >= 50:
        return "#B45309", "#FEF3C7", "Moderate match"
    return "#B91C1C", "#FEE2E2", "Needs work"


# ---------- sidebar ----------
try:
    cfg = analyzer.get_config()
    provider_ok, local = True, cfg["is_local"]
except analyzer.ConfigError as ex:
    cfg, provider_ok, local = None, False, False
    config_msg = str(ex)

with st.sidebar:
    st.markdown("### 🔒 Privacy")
    st.caption("Resumes are processed in memory and never saved to disk. Resume text is sent to your configured AI "
               "provider for analysis. For fully local processing, use the `ollama` provider.")
    if provider_ok:
        st.caption(f"Provider: **{cfg['provider']}** · Model: `{cfg['model']}`")
    st.button("🔄 Start new analysis", on_click=reset, use_container_width=True)

# ---------- header ----------
st.markdown('<div class="hero"><h1>📄 AI Resume Analyzer</h1>'
            '<p>Upload your resume, paste a job description, and get an AI-powered match analysis with '
            'actionable ways to improve.</p></div>', unsafe_allow_html=True)

with st.expander("How it works", expanded=ss.result is None):
    st.markdown("1. **Upload** a text-based PDF or DOCX resume (max 5 MB).\n"
                "2. **Paste** the full job description you're targeting.\n"
                "3. **Analyze** to see your match score, skill gaps and recommendations.\n"
                "4. **Improve** your wording with AI suggestions, then **download** the report.")

if not provider_ok:
    st.error(config_msg)

# ---------- inputs ----------
left, right = st.columns(2, gap="large")
with left:
    st.markdown("#### 1. Your resume")
    up = st.file_uploader("PDF or DOCX, max 5 MB", type=["pdf", "docx"], key=f"up_{ss.uploader_key}")
    if up is not None:
        sig = (up.name, up.size)
        if ss.sig != sig:
            try:
                ss.resume_text, ss.parse_error = extract_text(up.name, up.getvalue()), None
            except ResumeParseError as ex:
                ss.resume_text, ss.parse_error = None, str(ex)
            ss.sig, ss.result, ss.improvements = sig, None, None
    elif ss.sig is not None:
        ss.resume_text = ss.parse_error = ss.sig = None
    if ss.parse_error:
        st.error(ss.parse_error)
    elif ss.resume_text:
        st.success(f"Extracted {len(ss.resume_text):,} characters.")
        with st.expander("Preview extracted text"):
            st.text(ss.resume_text[:3000] + ("\n…" if len(ss.resume_text) > 3000 else ""))
with right:
    st.markdown("#### 2. Job description")
    jd = st.text_area("Paste the job posting", key="jd", height=260, max_chars=15000,
                      placeholder="Paste the full job description here…", label_visibility="collapsed")

consent = True
if provider_ok and not local:
    consent = st.checkbox(f"I understand my resume text will be sent to **{cfg['provider']}** for analysis.")

if st.button("🔍 Analyze my resume", type="primary", disabled=not provider_ok):
    if ss.parse_error:
        st.error("Please fix the resume problem above first.")
    elif not ss.resume_text:
        st.warning("Please upload your resume first.")
    elif len(jd.strip()) < 50:
        st.warning("Please paste a complete job description (at least a few sentences).")
    elif not consent:
        st.warning("Please confirm you're happy for your resume text to be sent to the AI provider.")
    else:
        try:
            with st.spinner("Analyzing your resume… this usually takes 10-30 seconds."):
                ss.result = analyzer.analyze(ss.resume_text, jd)
                ss.improvements = None
        except analyzer.AnalyzerError as ex:
            st.error(str(ex))
        except Exception:
            st.error("Something unexpected went wrong. Please try again.")

# ---------- results ----------
res = ss.result
if res:
    color, bg, label = score_style(res["score"])
    st.markdown('<div class="section-title">Your results</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2], gap="large")
    with c1:
        st.markdown(f'<div class="card score-card"><div class="score-num" style="color:{color}">{res["score"]}</div>'
                    f'<div class="score-sub">out of 100 (estimated)</div>'
                    f'<span class="score-label" style="background:{bg};color:{color}">{label}</span></div>',
                    unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="card"><h4>Score breakdown</h4><div class="muted">{e(res["summary"])}</div></div>',
                    unsafe_allow_html=True)
        for r in res["rubric"].values():
            st.progress(r["score"] / r["max"], text=f'{r["label"]}: {r["score"]}/{r["max"]}')
    st.markdown('<div class="note">ℹ️ This score is an AI-generated estimate based on the rubric above. It is not a real ATS '
                'score and does not guarantee selection.</div>', unsafe_allow_html=True)

    s1, s2 = st.columns(2, gap="large")
    s1.markdown(f'<div class="card"><h4>✅ Matching skills</h4>{chips(res["matching_skills"], "ok")}</div>', unsafe_allow_html=True)
    s2.markdown(f'<div class="card"><h4>⚠️ Missing skills</h4>{chips(res["missing_skills"], "miss")}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Detailed feedback</div>', unsafe_allow_html=True)
    for title, body, first in [
        ("💼 Experience analysis", f'<p>{e(res["experience_analysis"])}</p>', True),
        ("🎓 Education match", f'<p>{e(res["education_match"])}</p>', False),
        ("💪 Strengths", ul(res["strengths"]), False),
        ("🛠️ Areas to improve", ul(res["areas_to_improve"]), False),
        ("🤖 ATS-friendly suggestions", ul(res["ats_suggestions"]), False),
        ("📚 Recommended learning topics", ul(res["learning_topics"]), False),
    ]:
        with st.expander(title, expanded=first):
            st.markdown(body, unsafe_allow_html=True)

    # ---------- improvement assistant ----------
    st.markdown('<div class="section-title">✨ Resume improvement assistant</div>', unsafe_allow_html=True)
    if st.button("Generate improvement suggestions"):
        try:
            with st.spinner("Writing suggestions…"):
                ss.improvements = analyzer.improve(ss.resume_text, jd, res)
        except analyzer.AnalyzerError as ex:
            st.error(str(ex))
        except Exception:
            st.error("Something unexpected went wrong. Please try again.")
    imp = ss.improvements
    if imp:
        st.markdown('<div class="warn">⚠️ <b>AI-generated suggestions.</b> Review everything for accuracy before using it. '
                    'Replace any [placeholders] with your real numbers, and only add keywords you can honestly claim.</div>',
                    unsafe_allow_html=True)
        st.markdown("**Professional summary options**")
        for s in imp["summary_suggestions"]:
            st.markdown(f'<div class="rewrite">{e(s)}</div>', unsafe_allow_html=True)
        st.markdown("**Bullet point rewrites**")
        for b in imp["bullet_rewrites"]:
            st.markdown(f'<div class="rewrite"><div class="before">{e(b["original"])}</div>'
                        f'<div class="after">{e(b["improved"])}</div><div class="muted">{e(b["note"])}</div></div>',
                        unsafe_allow_html=True)
        st.markdown("**Relevant keywords (add only if true for you)**")
        st.markdown(chips(imp["keywords"], "kw"), unsafe_allow_html=True)

    # ---------- downloads ----------
    st.markdown('<div class="section-title">Download report</div>', unsafe_allow_html=True)
    d1, d2, _ = st.columns([1, 1, 2])
    d1.download_button("⬇️ Text report", report.build_text_report(res, imp), "resume_analysis.txt", "text/plain")
    try:
        d2.download_button("⬇️ PDF report", report.build_pdf_report(res, imp), "resume_analysis.pdf", "application/pdf")
    except Exception:
        d2.caption("PDF unavailable; use the text report.")
