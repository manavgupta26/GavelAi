import streamlit as st
import fitz  # PyMuPDF
import requests
import json

st.set_page_config(page_title="GavelAI", layout="wide")

st.title("⚖️ GavelAI - Court Judgment Analyzer")

# -----------------------------
# SESSION STATE INIT
# -----------------------------
if "cases" not in st.session_state:
    st.session_state.cases = []

if "current_case" not in st.session_state:
    st.session_state.current_case = None

# -----------------------------
# TABS
# -----------------------------
tab1, tab2 = st.tabs(["🔍 Process Judgment", "📊 Dashboard"])

# =============================
# TAB 1 → PROCESS
# =============================
with tab1:

    uploaded_file = st.file_uploader("Upload Court Judgment PDF", type="pdf")

    if uploaded_file:

        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")

        raw_text = ""
        for i, page in enumerate(doc):
            if i < 3:  # limit pages
                raw_text += page.get_text()

        raw_text = raw_text[:8000]

        if st.button("🚀 Process Judgment"):

            # ------------------------
            # STEP 1: EXTRACTION
            # ------------------------
            extract_prompt = f"""
You are a legal assistant.

Extract:
- Case title
- Date of order
- Parties involved
- Key directions/orders
- Timeline (if any)

Return ONLY valid JSON. No explanation.

Format:
{{
  "case_title": "",
  "date_of_order": "",
  "parties": [],
  "key_directions": "",
  "timeline": ""
}}

TEXT:
\"\"\"{raw_text}\"\"\"
"""

            res = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3",
                    "prompt": extract_prompt,
                    "stream": False
                }
            )

            extracted = res.json()["response"]

            st.subheader("📄 Extracted Data")
            st.code(extracted)

            # Try parsing JSON
            try:
                data = json.loads(extracted)
            except:
                st.warning("⚠️ JSON parsing failed, using raw output")
                data = extracted

            # ------------------------
            # STEP 2: ACTION PLAN
            # ------------------------
            action_prompt = f"""
You are assisting a government legal department.

Based on the extracted case data below, generate an action plan.

Decide:
- Action required (compliance / appeal / no action)
- Responsible department
- Deadline
- Priority (High/Medium/Low)

Return ONLY JSON:

{{
  "action": "",
  "department": "",
  "deadline": "",
  "priority": ""
}}

DATA:
{data}
"""

            res2 = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3",
                    "prompt": action_prompt,
                    "stream": False
                }
            )

            action = res2.json()["response"]

            st.subheader("⚡ Action Plan")
            st.code(action)

            # Save current case temporarily
            st.session_state.current_case = {
                "file_name": uploaded_file.name,
                "extracted": extracted,
                "action": action,
                "status": "Pending"
            }

    # ------------------------
    # VERIFICATION SECTION
    # ------------------------
    if st.session_state.current_case:

        st.subheader("👨‍⚖️ Human Verification")

        decision = st.radio(
            "Choose Decision",
            ["Approve", "Edit", "Reject"],
            key="decision_radio"
        )

        edited_action = st.session_state.current_case["action"]

        if decision == "Edit":
            edited_action = st.text_area(
                "Edit Action Plan",
                st.session_state.current_case["action"]
            )

        if st.button("✅ Submit Decision"):

            case = st.session_state.current_case.copy()

            if decision == "Approve":
                case["status"] = "Approved"

            elif decision == "Edit":
                case["status"] = "Edited"
                case["action"] = edited_action

            else:
                case["status"] = "Rejected"

            st.session_state.cases.append(case)

            st.success("✅ Saved! Check Dashboard tab 👉")

            # Clear current case after saving
            st.session_state.current_case = None


# =============================
# TAB 2 → DASHBOARD
# =============================
with tab2:

    st.subheader("📊 Processed Cases Dashboard")

    if len(st.session_state.cases) == 0:
        st.info("No cases processed yet.")
    else:
        for i, case in enumerate(st.session_state.cases):

            st.markdown(f"### 📁 Case {i+1}: {case['file_name']}")
            st.write(f"**Status:** {case['status']}")

            st.write("**⚡ Action Plan:**")
            st.code(case["action"])

            with st.expander("📄 View Extracted Data"):
                st.code(case["extracted"])

            st.divider()