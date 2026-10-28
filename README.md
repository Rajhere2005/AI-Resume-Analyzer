# 📄 AI Resume Analyzer
🔗 **Live demo:** https://ai-resume-analyzer-gmueg52ew3zzwv8ye95lmk.streamlit.app/

A Streamlit web app that compares a resume (PDF/DOCX) with a job description and returns an AI-powered match analysis: score, matching/missing skills, experience and education fit, ATS tips, learning topics, truthful rewrite suggestions, and a downloadable PDF/TXT report.

## Features
- PDF/DOCX upload with validation (type, magic bytes, 5 MB limit, page limit, password-protected/corrupted/scanned detection) and text preview
- Match score from an explicit rubric: skills 40, experience 25, education 10, keywords/ATS 15, impact 10. **The total is computed in code**, not trusted from the model
- Dashboard: score card, rubric progress bars, skill chips, expandable feedback
- Improvement assistant: summary options, bullet rewrites (placeholders instead of invented metrics), keywords
- Provider-agnostic LLM layer (Gemini, Groq, OpenAI, or local Ollama)
- Graceful handling of missing keys, bad keys, rate limits, timeouts, and malformed AI output

## Quick start
```bash
git clone <your-repo-url> && cd ai-resume-analyzer
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                # then add your API key
streamlit run app.py
```

## Choosing an AI provider
| `LLM_PROVIDER` | Cost | Get a key |
|---|---|---|
| `gemini` (default) | Free tier | https://aistudio.google.com/apikey |
| `groq` | Free tier | https://console.groq.com/keys |
| `openai` | Paid | https://platform.openai.com/api-keys |
| `ollama` | Free, runs locally, **resume never leaves your machine** | https://ollama.com (no key needed) |

Model names change often. If you get a model error, set `LLM_MODEL` in `.env` to a current one.

## Project structure
```
app.py                 Streamlit UI
styles.css             Custom theme (navy/blue/purple SaaS look)
src/resume_parser.py   PDF/DOCX extraction + validation
src/analyzer.py        LLM calls, prompts, JSON parsing/validation
src/report.py          TXT and PDF report generation
.streamlit/config.toml Theme and upload limit
```

## Security & privacy design
- API keys live only in `.env` (git-ignored); the browser never sees them
- Uploaded files are processed in memory, never executed or written to disk
- Resume/JD text is treated as untrusted: wrapped in delimiter tags, tag-breakout stripped, and the model is told to ignore embedded instructions (prompt-injection mitigation)
- AI output is parsed as JSON, type-checked, length-limited, clamped, and **HTML-escaped before display**
- Users must consent before text is sent to an external provider (not required for Ollama)
- The score is labelled an estimate, not a real ATS score

## Limitations / ideas
- No OCR for scanned resumes (could add Tesseract)
- LLM scoring is not perfectly deterministic
- Ideas: multiple job comparison, cover-letter generator, keyword-gap chart, unit tests with mocked LLM responses

## License
MIT
