import streamlit as st
import fitz  # PyMuPDF
import requests
import json
import tempfile
import os
import re
from collections import defaultdict
from datetime import datetime, timedelta
import pytesseract
from PIL import Image
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="GavelAI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CUSTOM CSS — judicial dark-gold aesthetic
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Source+Sans+3:wght@300;400;500;600&display=swap');


:root {
    --gold:     #10B981;
    --gold-lt:  #6EE7B7;
    --gold-dk:  #047857;
    --ink:      #0D0D0D;
    --ink2:     #1A1A1A;
    --ink3:     #242424;
    --surface:  #181818;
    --card:     #1F1F1F;
    --border:   #2E2E2E;
    --muted:    #6B6B6B;
    --text:     #E8E2D4;
    --text2:    #A89E87;
    --green:    #4CAF82;
    --red:      #CF6679;
    --amber:    #E8A838;
    --blue:     #5B9BD5;
}

html, body, [class*="css"] {
    font-family: 'Source Sans 3', sans-serif;
    background-color: var(--ink) !important;
    color: var(--text) !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem !important; }

/* ── Masthead ── */
.masthead {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1.2rem 2rem;
    background: linear-gradient(135deg, #1A1509 0%, #0D0D0D 60%);
    border-bottom: 1px solid var(--gold-dk);
    margin-bottom: 1.5rem;
    border-radius: 0 0 12px 12px;
}
.masthead-icon { font-size: 2.2rem; line-height: 1; }
.masthead-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.9rem;
    font-weight: 700;
    color: var(--gold-lt);
    letter-spacing: 0.02em;
    line-height: 1;
}
.masthead-sub {
    font-size: 0.78rem;
    color: var(--text2);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 0.2rem;
}
.masthead-badge {
    margin-left: auto;
    background: var(--gold-dk);
    color: var(--gold-lt);
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    border: 1px solid var(--gold);
}

/* ── Cards ── */
.gavel-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1.2rem;
}
.gavel-card-header {
    font-family: 'Playfair Display', serif;
    font-size: 1.15rem;
    color: var(--gold);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* ── Extracted field grid ── */
.field-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; }
.field-block {
    background: var(--ink2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.8rem 1rem;
}
.field-label {
    font-size: 0.68rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.3rem;
}
.field-value {
    font-size: 1rem;
    color: var(--text);
    line-height: 1.4;
}

/* ── Action plan ── */
.action-row {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    background: var(--ink2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
}
.priority-badge {
    padding: 0.2rem 0.7rem;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    white-space: nowrap;
}
.priority-HIGH   { background: #3D1520; color: var(--red);   border: 1px solid var(--red); }
.priority-MEDIUM { background: #2E2200; color: var(--amber); border: 1px solid var(--amber); }
.priority-LOW    { background: #0E2218; color: var(--green); border: 1px solid var(--green); }

/* ── Confidence bar ── */
.conf-wrap { margin-top: 0.5rem; }
.conf-label { font-size: 1rem; color: var(--muted); margin-bottom: 0.3rem; }
.conf-bar-bg {
    height: 5px; background: var(--border); border-radius: 4px; overflow: hidden;
}
.conf-bar-fill { height: 100%; border-radius: 4px; transition: width 0.6s ease; }

/* ── Stat chips ── */
.stats-row { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.4rem; }
.stat-chip {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.8rem 1.4rem;
    text-align: center;
    min-width: 120px;
}
.stat-num {
    font-family: 'Playfair Display', serif;
    font-size: 1.8rem;
    color: var(--gold);
    line-height: 1;
}
.stat-label { font-size: 0.72rem; color: var(--muted); margin-top: 0.3rem; text-transform: uppercase; letter-spacing: 0.08em; }

/* ── Source highlight box ── */
.source-box {
    background: #1C1800;
    border-left: 3px solid var(--gold);
    border-radius: 0 8px 8px 0;
    padding: 0.9rem 1.2rem;
    font-size: 0.86rem;
    color: var(--text2);
    font-style: italic;
    line-height: 1.6;
    margin: 0.8rem 0;
}

/* ── Verdict chip ── */
.verdict-chip {
    display: inline-block;
    padding: 0.25rem 0.9rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.verdict-APPROVED { background: #0E2218; color: var(--green); border: 1px solid var(--green); }
.verdict-EDITED   { background: #2E2200; color: var(--amber); border: 1px solid var(--amber); }
.verdict-REJECTED { background: #3D1520; color: var(--red);   border: 1px solid var(--red); }
.verdict-PENDING  { background: #1A1A2E; color: var(--blue);  border: 1px solid var(--blue); }

/* ── Divider ── */
.gavel-divider { border: none; border-top: 1px solid var(--border); margin: 1.4rem 0; }

/* ── Streamlit overrides ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--ink2) !important;
    border-radius: 10px;
    padding: 4px;
    gap: 2px;
    border: 1px solid var(--border);
    margin-bottom: 1.4rem;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text2) !important;
    border-radius: 7px;
    padding: 0.5rem 1.2rem;
    font-family: 'Source Sans 3', sans-serif;
    font-size: 1rem;
}
.stTabs [aria-selected="true"] {
    background: var(--gold-dk) !important;
    color: var(--gold-lt) !important;
}
.stTabs [data-baseweb="tab-panel"] { padding: 0 !important; }

div[data-testid="stFileUploader"] {
    background: var(--card) !important;
    border: 1.5px dashed var(--gold-dk) !important;
    border-radius: 10px !important;
    padding: 1rem !important;
}

.stButton > button {
    background: linear-gradient(135deg, var(--gold-dk), var(--gold)) !important;
    color: var(--ink) !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Source Sans 3', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    padding: 0.5rem 1.4rem !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

.stTextArea textarea {
    background: var(--ink2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: 'Source Sans 3', sans-serif !important;
    font-size: 1rem !important;
}

.stRadio [data-testid="stMarkdownContainer"] p { color: var(--text2) !important; font-size: 1rem; }
.stRadio label span { color: var(--text) !important; }

.stSelectbox div[data-baseweb="select"] {
    background: var(--ink2) !important;
    border-color: var(--border) !important;
}

div[data-testid="stExpander"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}
div[data-testid="stExpander"] summary { color: var(--gold) !important; font-size: 1rem; }

.stAlert { border-radius: 8px !important; }
.stProgress > div > div { background: var(--gold) !important; }

div[data-testid="metric-container"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    padding: 0.8rem 1rem !important;
}
[data-testid="stFileUploader"] div[data-testid="stFileUploaderDropzoneInstructions"] small {
    display: none !important;
}

[data-testid="stFileUploader"] div[data-testid="stFileUploaderDropzoneInstructions"] span {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MASTHEAD
# ─────────────────────────────────────────────
st.markdown("""
<div class="masthead">

  <div>
    <div class="masthead-title">GavelAi</div>
    <div class="masthead-sub">Court Judgment Intelligence System</div>
  </div>
  <div class="masthead-badge">CCMS Integration Ready</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# OLLAMA CONFIG (sidebar)
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='font-family: Playfair Display, serif; font-size: 1.1rem; color: #10B981; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid #2E2E2E;'>
    ⚙️ Configuration
    </div>
    """, unsafe_allow_html=True)

    ollama_host = st.text_input("Ollama Host", value="http://localhost:11434")
    ollama_model = st.selectbox("Model", ["llama3", "llama3.1", "mistral", "gemma2", "phi3"], index=0)
    
   
    st.markdown("<hr style='border-color: #2E2E2E; margin: 1rem 0;'>", unsafe_allow_html=True)

    # Connection test
    if st.button("Test Ollama Connection"):
        try:
            r = requests.get(f"{ollama_host}/api/tags", timeout=5)
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                st.success(f"Connected ✓  |  Models: {', '.join(models[:3])}")
            else:
                st.error(f"Responded with {r.status_code}")
        except Exception as e:
            st.error(f"Cannot reach Ollama: {e}")

    st.markdown("<hr style='border-color: #2E2E2E; margin: 1rem 0;'>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:0.75rem; color:#6B6B6B; line-height:1.6;'>
    <b style='color:#A89E87;'>GavelAI v1.0</b><br>
    AI-assisted judgment analysis with human verification loop.<br><br>
    Built for CCMS integration · High Court compatible
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for k, v in [("cases", []), ("current_case", None), ("processing", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def call_ollama(prompt: str, host: str, model: str, timeout: int = 120) -> str:
    """Call Ollama and return raw response text."""
    try:
        res = requests.post(
            f"{host}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=timeout
        )
        res.raise_for_status()
        return res.json().get("response", "")
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to Ollama. Make sure it's running (`ollama serve`).")
        return ""
    except requests.exceptions.Timeout:
        st.error("⏱ Ollama timed out. Try a lighter model or reduce page count.")
        return ""
    except Exception as e:
        st.error(f"Ollama error: {e}")
        return ""


def safe_json(text: str) -> dict:
    """Extract JSON from model response robustly."""
    # Try direct parse
    try:
        return json.loads(text)
    except Exception:
        pass
    # Try extracting JSON block
    for pattern in [r"```json\s*(.*?)\s*```", r"```\s*(.*?)\s*```", r"\{.*\}"]:
        m = re.search(pattern, text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1) if "```" in pattern else m.group(0))
            except Exception:
                pass
    return {}


def extract_pdf_text(doc: fitz.Document, use_ocr: bool = False) -> str:
    """Extract text from PDF, with optional OCR fallback for scanned docs."""
    text = ""
    pages_to_read = len(doc)

    for i in range(pages_to_read):
        page = doc[i]
        page_text = page.get_text().strip()

        # If page is blank → likely scanned, try OCR
        if len(page_text) < 50 and use_ocr:
            try:
                pix = page.get_pixmap(dpi=200)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                page_text = pytesseract.image_to_string(img, lang="eng")
            except Exception:
                pass  # pytesseract not available or page truly blank

        text += f"\n--- Page {i+1} ---\n{page_text}"

    return text.strip()



def chunk_pdf_pages(doc, pages_per_chunk=4):
    chunks = []
    total_pages = len(doc)

    for i in range(0, total_pages, pages_per_chunk):
        chunk_text = ""
        for j in range(i, min(i + pages_per_chunk, total_pages)):
            chunk_text += doc[j].get_text()

        if len(chunk_text.strip()) > 100:  # skip useless chunks
            chunks.append(chunk_text)

    return chunks

def highlight_pdf(doc: fitz.Document, terms: list[str]) -> str | None:
    """Highlight multiple terms in PDF and return temp path."""
    try:
        for page in doc:
            for term in terms:
                if term and len(term) > 10:
                    for area in page.search_for(term[:100]):
                        ann = page.add_highlight_annot(area)
                        ann.update()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        doc.save(tmp.name)
        return tmp.name
    except Exception as e:
        st.warning(f"Could not generate highlighted PDF: {e}")
        return None


def infer_deadline(extracted: dict, action_type: str) -> str:
    """Infer deadline from extracted data or action type."""
    explicit = extracted.get("deadlines") or extracted.get("timeline") or ""
    if explicit and len(str(explicit)) > 4:
        return str(explicit)
    # Infer from action type
    today = datetime.today()
    if "appeal" in action_type.lower():
        return (today + timedelta(days=90)).strftime("%d %b %Y") + " (inferred — 90-day limitation)"
    elif "comply" in action_type.lower() or "compliance" in action_type.lower():
        return (today + timedelta(days=30)).strftime("%d %b %Y") + " (inferred — 30 days)"
    return "Review order for explicit deadline"


def confidence_color(score: int) -> str:
    if score >= 80: return "#4CAF82"
    if score >= 55: return "#E8A838"
    return "#CF6679"


# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2 = st.tabs(["  Process Judgment", "  Action Dashboard"])


# ══════════════════════════════════════════════
# TAB 1 — PROCESS
# ══════════════════════════════════════════════
with tab1:

    col_up, col_tip = st.columns([3, 1])
    with col_up:
        uploaded_file = st.file_uploader(
            "Upload Court Judgment PDF",
            type="pdf",
            help="Digital or scanned PDF. System will auto-detect and apply OCR if needed."
        )

        if uploaded_file is None:
            st.session_state.current_case = None
    with col_tip:
        st.markdown("""
        <div class='gavel-card' style='padding: 0.9rem 1rem; font-size: 0.8rem; color: #A89E87; line-height: 1.7;'>
        <b style='color:#10B981;'>Tips</b><br>
        • Digital PDFs give best results<br>
        • Scanned PDFs auto-OCR'd<br>
        • Review extraction before approving
        </div>
        """, unsafe_allow_html=True)

    if uploaded_file:
        file_bytes = uploaded_file.read()
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        total_pages = len(doc)

        st.markdown(f"""
        <div class='gavel-card' style='display:flex; gap:2rem; align-items:center;'>
          <div>
            <div class='field-label'>File</div>
            <div class='field-value' style='color:#10B981;'>{uploaded_file.name}</div>
          </div>
          <div>
            <div class='field-label'>Pages</div>
            <div class='field-value'>{total_pages}</div>
          </div>
          <div>
            <div class='field-label'>Processing</div>
<div class='field-value'>Full document</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Check if scanned
        sample_text = doc[0].get_text().strip()
        is_scanned = len(sample_text) < 80
        if is_scanned:
            st.info("📷 Scanned PDF detected — OCR will be applied (requires `pytesseract` + Tesseract).")

        if st.button(" Analyze Judgment", use_container_width=True):
            # ── Step 1: Text Extraction ──
            with st.spinner(" Extracting text from PDF…"):
                raw_text = extract_pdf_text(doc, use_ocr=is_scanned)

            if not raw_text or len(raw_text) < 100:
                st.error("Could not extract meaningful text. If scanned, ensure Tesseract is installed.")
                st.stop()

            def merge_extractions(results):
                final = {}

                for key in results[0].keys():
                    values = [r.get(key) for r in results if r.get(key)]

                    if not values:
                        final[key] = ""
                        continue

                    # 🔹 If list field (like key_directions)
                    if isinstance(values[0], list):
                        merged = []

                        for v in values:
                            for item in v:
                                # convert dict → string safely
                                if isinstance(item, dict):
                                    item = json.dumps(item, sort_keys=True)
                                merged.append(str(item))

                        # remove duplicates safely
                        final[key] = list(set(merged))

                    else:
                        # 🔹 For normal fields → pick most frequent
                        values_str = [str(v) for v in values]
                        final[key] = max(set(values_str), key=values_str.count)

                return final


            

            # ── Step 2: Structured Extraction ──
            chunks = chunk_pdf_pages(doc)
            def process_chunk(chunk):
                prompt = f"""
            Extract structured legal info.

            Return ONLY JSON:
            {{
            "case_number": "",
            "court_name": "",
            "date_of_order": "",
            "bench": "",
            "petitioner": "",
            "respondent": "",
            "case_type": "",
            "subject_matter": "",
            "outcome": "",
            "key_directions": [],
            "compliance_required": true,
            "appeal_mentioned": false,
            "deadlines": "",
            "relevant_laws": [],
            "summary": ""
            }}

            TEXT:
            {chunk}
            """
                res = call_ollama(prompt, ollama_host, ollama_model)
                return safe_json(res)


            all_extractions = []

            # with st.spinner(f"⚡ Processing {len(chunks)} chunks..."):

            #     with ThreadPoolExecutor(max_workers=4) as executor:
            #         futures = [executor.submit(process_chunk, c) for c in chunks]

            #         for i, future in enumerate(as_completed(futures)):
            #             result = future.result()
            #             if result:
            #                 all_extractions.append(result)

            #             st.write(f"Processed {i+1}/{len(chunks)} chunks")


            processing_placeholder = st.empty()

            processing_placeholder.markdown("""
            <div style="
                display:flex;
                align-items:center;
                gap:0.7rem;
                padding:0.9rem 1rem;
                background:#1F1F1F;
                border:1px solid #2E2E2E;
                border-radius:10px;
                color:#E8E2D4;
                font-size:0.9rem;
            ">
                <div class="loader"></div>
                <div>Processing judgment...</div>
            </div>

            <style>
            .loader {
                width:16px;
                height:16px;
                border:2px solid #3A3A3A;
                border-top:2px solid #10B981;
                border-radius:50%;
                animation: spin 0.8s linear infinite;
            }

            @keyframes spin {
                100% { transform: rotate(360deg); }
            }
            </style>
            """, unsafe_allow_html=True)

            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(process_chunk, c) for c in chunks]

                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        all_extractions.append(result)

            processing_placeholder.empty()
            if not all_extractions:
                st.error("No data extracted from PDF.")
                st.stop()

            extracted = merge_extractions(all_extractions)
            extracted_raw = json.dumps(extracted)

            # Show extraction
            # st.markdown("<div class='gavel-card'>", unsafe_allow_html=True)
            st.markdown("<div class='gavel-card-header'>Extracted Case Details</div>", unsafe_allow_html=True)

            top_fields = [
                ("Case Number",  extracted.get("case_number", "—")),
                ("Court",        extracted.get("court_name", "—")),
                ("Date of Order",extracted.get("date_of_order", "—")),
                ("Bench",        extracted.get("bench", "—")),
                ("Petitioner",    extracted.get("petitioner", "—")),
                ("Respondent",    extracted.get("respondent", "—")),    
                ("Case Type",    extracted.get("case_type", "—")),
                ("Outcome",      extracted.get("outcome", "—")),
                ("Subject",      extracted.get("subject_matter", "—")),
            ]
            html_fields = "<div class='field-grid'>"
            for label, val in top_fields:
                html_fields += f"<div class='field-block'><div class='field-label'>{label}</div><div class='field-value'>{val}</div></div>"
            html_fields += "</div>"
            st.markdown(html_fields, unsafe_allow_html=True)

            directions = extracted.get("key_directions", [])

            if directions:
                st.markdown(
                    "<div style='margin-top:1rem; margin-bottom:0.4rem; font-size:0.75rem; letter-spacing:0.1em; color:#6B6B6B; text-transform:uppercase;'>Key Directions</div>",
                    unsafe_allow_html=True
                )

                for d in directions[:5]:
                    if isinstance(d, dict):
                        text = d.get("description", "")
                    else:
                        text = str(d)

                    st.markdown(
                        f"<div class='source-box'>› {text}</div>",
                        unsafe_allow_html=True
                    )

            

            if extracted.get("summary"):
                st.markdown(f"""
                <div style='background:#1A1A1A; border:1px solid #2E2E2E; border-radius:8px; padding:1rem; margin-top:0.8rem; font-size:1rem; color:#A89E87; line-height:1.7;'>
                <b style='color:#10B981; font-size:0.72rem; letter-spacing:0.1em; text-transform:uppercase;'>AI Summary</b><br><br>
                {extracted.get("summary")}
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # ── Highlighted PDF ──
            highlight_terms = []
            for d in directions[:3]:
                if isinstance(d, str) and len(d) > 15:
                    highlight_terms.append(d[:80])

            highlighted_path = highlight_pdf(doc, highlight_terms)
            if highlighted_path:
                with open(highlighted_path, "rb") as f:
                    pdf_data = f.read()
                st.download_button(
                    "📥 Download PDF with Highlighted Directions",
                    pdf_data,
                    file_name=f"highlighted_{uploaded_file.name}",
                    mime="application/pdf"
                )
                

            # ── Step 3: Action Plan ──
            with st.spinner(" Generating action plan…"):
                outcome  = extracted.get("outcome", "").lower()
                comp_req = extracted.get("compliance_required", True)
                appeal   = extracted.get("appeal_mentioned", False)
                subj     = extracted.get("subject_matter", "").lower()

                # Smarter department mapping
                dept_hint = "Legal"
                for kw, dept in [
                    ("employ", "HR / Labour"), ("service", "HR / Labour"), ("salary", "HR / Labour"),
                    ("land", "Revenue"), ("property", "Revenue"), ("acquisition", "Revenue"),
                    ("education", "Education"), ("school", "Education"), ("university", "Education"),
                    ("pension", "Finance"), ("pay", "Finance"), ("fund", "Finance"),
                    ("police", "Home"), ("crime", "Home"), ("custody", "Home"),
                    ("environment", "Environment"), ("pollution", "Environment"),
                    ("health", "Health"), ("hospital", "Health"),
                    ("infrastructure", "PWD"), ("road", "PWD"), ("construction", "PWD"),
                ]:
                    if kw in subj or kw in str(directions).lower():
                        dept_hint = dept
                        break

                action_prompt = f"""You are a senior government legal advisor. Based on the court judgment analysis below, produce a structured action plan for the government department.

Judgment Summary:
- Outcome: {extracted.get("outcome", "Unknown")}
- Key Directions: {json.dumps(directions)}
- Compliance Required: {comp_req}
- Appeal Mentioned: {appeal}
- Subject Matter: {extracted.get("subject_matter", "")}
- Deadlines in Order: {extracted.get("deadlines", "Not specified")}
- Suggested Department: {dept_hint}

Rules for action classification:
1. If "dismissed" and government wins → action: "No compliance required. File for records."
2. If "allowed" or directions issued against government → action: detailed compliance steps
3. If adverse order with right of appeal → include appeal recommendation
4. Infer realistic deadlines if not explicit (appeal: 90 days, compliance: 30-60 days)
5. Priority: HIGH if fundamental rights violation or contempt risk, MEDIUM if directions with deadline, LOW if informational

Return ONLY a valid JSON object:
{{
  "action_required": "Detailed description of what must be done",
  "action_type": "Compliance / Appeal / File for Records / Seek Clarification",
  "department": "{dept_hint}",
  "responsible_officer": "Designation of the officer who should act",
  "deadline": "Specific date or period",
  "priority": "HIGH / MEDIUM / LOW",
  "steps": ["step 1", "step 2", "step 3"],
  "appeal_recommended": true or false,
  "appeal_grounds": "Grounds for appeal if applicable",
  "confidence_score": 0-100,
  "confidence_rationale": "Why this confidence level"
}}"""

                action_raw = call_ollama(action_prompt, ollama_host, ollama_model)

            if not action_raw:
                st.stop()

            action_data = safe_json(action_raw)

            # Fix deadline if empty
            if not action_data.get("deadline"):
                action_data["deadline"] = infer_deadline(extracted, action_data.get("action_type", ""))

            # Display action plan
            #st.markdown("<div class='gavel-card'>", unsafe_allow_html=True)
            st.markdown("<div class='gavel-card-header'>Generated Action Plan</div>", unsafe_allow_html=True)

            priority = action_data.get("priority", "MEDIUM").upper()
            conf = int(action_data.get("confidence_score", 70))
            conf_col = confidence_color(conf)

            st.markdown(f"""
            <div style='display:flex; gap:1rem; align-items:center; margin-bottom:1rem; flex-wrap:wrap;'>
              <span class='priority-badge priority-{priority}'>{priority} PRIORITY</span>
              <span style='font-size:0.8rem; color:#A89E87;'>{action_data.get("action_type","—")}</span>
              <span style='font-size:0.8rem; color:#6B6B6B;'>Dept: <b style='color:#E8E2D4;'>{action_data.get("department","—")}</b></span>
              <span style='font-size:0.8rem; color:#6B6B6B;'>Officer: <b style='color:#E8E2D4;'>{action_data.get("responsible_officer","—")}</b></span>
            </div>

            <div class='source-box' style='font-style:normal; margin-bottom:1rem;'>
              {action_data.get("action_required", "—")}
            </div>
            """, unsafe_allow_html=True)

            steps = action_data.get("steps", [])
            if steps:
                st.markdown("<div style='font-size:0.75rem; color:#6B6B6B; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:0.5rem;'>Action Steps</div>", unsafe_allow_html=True)
                for i, step in enumerate(steps, 1):
                    st.markdown(f"<div style='padding:0.4rem 0; font-size:1rem; color:#A89E87; border-bottom:1px solid #2E2E2E;'><b style='color:#10B981;'>{i}.</b> {step}</div>", unsafe_allow_html=True)

            st.markdown(f"""
            <div style='display:flex; gap:2rem; margin-top:1rem; flex-wrap:wrap;'>
              <div>
                <div class='field-label'> Deadline</div>
                <div class='field-value' style='color:#E8A838;'>{action_data.get("deadline","—")}</div>
              </div>
              <div>
                <div class='field-label'>Appeal Recommended</div>
                <div class='field-value'>{" Yes" if action_data.get("appeal_recommended") else " No"}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            if action_data.get("appeal_grounds"):
                st.markdown(f"<div style='margin-top:0.8rem; font-size:0.82rem; color:#6B6B6B;'>Appeal Grounds: <span style='color:#A89E87;'>{action_data['appeal_grounds']}</span></div>", unsafe_allow_html=True)

            # Confidence bar
            st.markdown(f"""
            <div class='conf-wrap' style='margin-top:1rem;'>
              <div class='conf-label'>AI Confidence: {conf}% — {action_data.get("confidence_rationale","")}</div>
              <div class='conf-bar-bg'>
                <div class='conf-bar-fill' style='width:{conf}%; background:{conf_col};'></div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # ── Save to session ──
            st.session_state.current_case = {
                "file_name": uploaded_file.name,
                "total_pages": total_pages,
                "extracted": extracted,
                "extracted_raw": extracted_raw,
                "action_data": action_data,
                "action_raw": action_raw,
                "raw_text_preview": raw_text[:2000],
                "status": "Pending",
                "timestamp": datetime.now().strftime("%d %b %Y, %H:%M"),
            }
            st.success(" Analysis complete! Scroll down to review.")

    # ── Verification inline ──
    if st.session_state.current_case and st.session_state.current_case.get("status") == "Pending":
        case = st.session_state.current_case
        st.markdown("<hr class='gavel-divider'>", unsafe_allow_html=True)
        #st.markdown("<div class='gavel-card'>", unsafe_allow_html=True)
        st.markdown("<div class='gavel-card-header'> Human Verification</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:0.85rem; color:#A89E87; margin-bottom:1rem;'>Review the AI analysis for <b style='color:#10B981;'>{case['file_name']}</b> before it enters the dashboard.</div>", unsafe_allow_html=True)



        decision = st.radio("Your Decision", ["Approve", "Edit & Approve", "Reject"], horizontal=True)

        edited_action = case["action_data"].get("action_required", "")
        edited_dept   = case["action_data"].get("department", "")
        edited_dl     = case["action_data"].get("deadline", "")

        if decision == "Edit & Approve":
            st.markdown("<div style='font-size:0.8rem; color:#A89E87; margin:0.5rem 0;'>Edit the fields below then submit:</div>", unsafe_allow_html=True)
            edited_action = st.text_area("Action Required", edited_action, height=100)
            c1, c2 = st.columns(2)
            with c1: edited_dept = st.text_input("Department", edited_dept)
            with c2: edited_dl   = st.text_input("Deadline", edited_dl)

        if st.button(" Submit Decision", use_container_width=False):
            new_case = case.copy()
            if decision == "Approve":
                new_case["status"] = "Approved"
            elif decision == "Edit & Approve":
                new_case["status"] = "Edited"
                new_case["action_data"] = {**case["action_data"],
                    "action_required": edited_action,
                    "department": edited_dept,
                    "deadline": edited_dl
                }
            else:
                new_case["status"] = "Rejected"
                new_case["reject_timestamp"] = datetime.now().strftime("%d %b %Y, %H:%M")

            new_case["verified_at"] = datetime.now().strftime("%d %b %Y, %H:%M")
            st.session_state.cases.append(new_case)
            st.session_state.current_case = None
            st.success(f"Case {new_case['status'].lower()}. Visit the **Action Dashboard** tab.")
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)



# ══════════════════════════════════════════════
# TAB 2 — DASHBOARD
# ══════════════════════════════════════════════
with tab2:
    all_cases = st.session_state.cases
    approved  = [c for c in all_cases if c["status"] in ("Approved", "Edited")]
    rejected  = [c for c in all_cases if c["status"] == "Rejected"]
    pending_d = [c for c in all_cases if c["status"] == "Pending"]

    # Stats
    st.markdown(f"""
    <div class='stats-row'>
      <div class='stat-chip'><div class='stat-num'>{len(all_cases)}</div><div class='stat-label'>Total Cases</div></div>
      <div class='stat-chip'><div class='stat-num' style='color:#4CAF82;'>{len(approved)}</div><div class='stat-label'>Approved</div></div>
      <div class='stat-chip'><div class='stat-num' style='color:#E8A838;'>{len(pending_d)}</div><div class='stat-label'>Pending</div></div>
      <div class='stat-chip'><div class='stat-num' style='color:#CF6679;'>{len(rejected)}</div><div class='stat-label'>Rejected</div></div>
    </div>
    """, unsafe_allow_html=True)

    if not approved:
        st.info("No approved cases yet. Process and approve judgments to populate the dashboard.")
    else:
        # Filter controls
        col_f1, col_f2, col_f3 = st.columns(3)
        depts = sorted(set(c.get("action_data", {}).get("department", "Other") for c in approved))
        with col_f1:
            sel_dept = st.selectbox("Filter by Department", ["All"] + depts)
        with col_f2:
            sel_prio = st.selectbox("Filter by Priority", ["All", "HIGH", "MEDIUM", "LOW"])
        with col_f3:
            sel_type = st.selectbox("Filter by Action Type", ["All", "Compliance", "Appeal", "File for Records", "Seek Clarification"])

        filtered = approved
        if sel_dept != "All":
            filtered = [c for c in filtered if c.get("action_data", {}).get("department") == sel_dept]
        if sel_prio != "All":
            filtered = [c for c in filtered if c.get("action_data", {}).get("priority", "").upper() == sel_prio]
        if sel_type != "All":
            filtered = [c for c in filtered if sel_type.lower() in c.get("action_data", {}).get("action_type", "").lower()]

        st.markdown(f"<div style='font-size:0.8rem; color:#6B6B6B; margin-bottom:1rem;'>Showing {len(filtered)} of {len(approved)} approved cases</div>", unsafe_allow_html=True)

        # Group by department
        dept_map = defaultdict(list)
        for case in filtered:
            dept = case.get("action_data", {}).get("department", "Other")
            dept_map[dept].append(case)

        for dept, cases in dept_map.items():
            st.markdown(f"""
            <div style='font-family: Playfair Display, serif; font-size: 1.1rem; color: #10B981;
                        border-bottom: 1px solid #2E2E2E; padding-bottom: 0.5rem; margin: 1.5rem 0 1rem 0;'>
            🏢 {dept} <span style='font-size:0.75rem; color:#6B6B6B; font-family: Source Sans 3, sans-serif; font-weight:400;'>({len(cases)} action{'s' if len(cases)>1 else ''})</span>
            </div>
            """, unsafe_allow_html=True)

            for case in cases:
                ad = case.get("action_data", {})
                ext = case.get("extracted", {})
                priority = ad.get("priority", "MEDIUM").upper()
                conf = int(ad.get("confidence_score", 70))
                conf_col = confidence_color(conf)
                status_chip = f"<span class='verdict-chip verdict-{case['status'].upper()}'>{case['status']}</span>"

                with st.expander(f"📁 {case['file_name']}  ·  {ad.get('action_type','—')}"):
                    st.markdown(f"""
                    <div style='display:flex; gap:0.8rem; align-items:center; flex-wrap:wrap; margin-bottom:1rem;'>
                      <span class='priority-badge priority-{priority}'>{priority}</span>
                      {status_chip}
                      <span style='font-size:0.78rem; color:#6B6B6B;'>Verified: {case.get('verified_at','—')}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown(f"""
                        <div class='field-block' style='margin-bottom:0.8rem;'>
                          <div class='field-label'>Action Required</div>
                          <div class='field-value'>{ad.get("action_required","—")}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        if ad.get("steps"):
                            st.markdown("<div style='font-size:0.75rem; color:#6B6B6B; margin:0.5rem 0 0.3rem; letter-spacing:0.08em; text-transform:uppercase;'>Steps</div>", unsafe_allow_html=True)
                            for i, s in enumerate(ad["steps"], 1):
                                st.markdown(f"<div style='font-size:0.84rem; color:#A89E87; padding:0.25rem 0; border-bottom:1px solid #2E2E2E;'><b style='color:#C8A84B;'>{i}.</b> {s}</div>", unsafe_allow_html=True)

                    with c2:
                        st.markdown(f"""
                        <div class='field-grid' style='grid-template-columns:1fr; gap:0.6rem;'>
                          <div class='field-block'>
                            <div class='field-label'>⏰ Deadline</div>
                            <div class='field-value' style='color:#E8A838;'>{ad.get("deadline","—")}</div>
                          </div>
                          <div class='field-block'>
                            <div class='field-label'>Responsible Officer</div>
                            <div class='field-value'>{ad.get("responsible_officer","—")}</div>
                          </div>
                          <div class='field-block'>
                            <div class='field-label'>Appeal</div>
                            <div class='field-value'>{"✅ Recommended" if ad.get("appeal_recommended") else "❌ Not Required"}</div>
                          </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Confidence bar
                        st.markdown(f"""
                        <div class='conf-wrap' style='margin-top:0.8rem;'>
                          <div class='conf-label'>AI Confidence: {conf}%</div>
                          <div class='conf-bar-bg'>
                            <div class='conf-bar-fill' style='width:{conf}%; background:{conf_col};'></div>
                          </div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("<hr class='gavel-divider'>", unsafe_allow_html=True)
                    with st.expander("📄 Original Extracted Data"):
                        st.markdown(f"""
                        <div class='field-grid' style='gap:0.6rem;'>
                          <div class='field-block'><div class='field-label'>Case Number</div><div class='field-value'>{ext.get("case_number","—")}</div></div>
                          <div class='field-block'><div class='field-label'>Date of Order</div><div class='field-value'>{ext.get("date_of_order","—")}</div></div>
                          <div class='field-block'><div class='field-label'>Outcome</div><div class='field-value'>{ext.get("outcome","—")}</div></div>
                        </div>
                        <div style='margin-top:0.8rem; font-size:0.85rem; color:#A89E87;'>{ext.get("summary","")}</div>
                        """, unsafe_allow_html=True)

        # Export
        st.markdown("<hr class='gavel-divider'>", unsafe_allow_html=True)
        if st.button("📤 Export Approved Cases (JSON)"):
            export = []
            for c in approved:
                export.append({
                    "file": c["file_name"],
                    "status": c["status"],
                    "verified_at": c.get("verified_at"),
                    "extracted": c.get("extracted", {}),
                    "action_plan": c.get("action_data", {}),
                })
            st.download_button(
                "⬇️ Download JSON",
                json.dumps(export, indent=2, ensure_ascii=False),
                file_name=f"gavelai_export_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )