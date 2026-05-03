import fitz  # PyMuPDF
import requests
import json

# Open PDF
doc = fitz.open("sample.pdf")

# Combine all pages
raw_text = ""
for i, page in enumerate(doc):
    if i < 3:  # limit pages (important)
        raw_text += page.get_text()

raw_text = raw_text[:8000]

# ------------------------
# STEP 3: Extract Data
# ------------------------
def extract_data(text):
    prompt = f"""
You are a legal assistant.

Extract the following from the judgment:

- Case title
- Date of order
- Parties involved
- Key directions/orders
- Timeline (if any)

Return ONLY valid JSON.
Do NOT add any explanation.

Format:
{{
  "case_title": "",
  "date_of_order": "",
  "parties": [],
  "key_directions": "",
  "timeline": ""
}}

TEXT:
\"\"\"{text}\"\"\"
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    return response.json()["response"]

# ------------------------
# STEP 4: Action Plan
# ------------------------
def generate_action_plan(extracted_json):
    prompt = f"""
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
{extracted_json}
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    return response.json()["response"]

# ------------------------
# RUN FLOW
# ------------------------

# Step 3
result = extract_data(raw_text)
print("\n--- Extracted JSON ---\n")
print(result)

# Convert to dict safely
try:
    data = json.loads(result)
except:
    print("⚠️ JSON parsing failed, using raw text")
    data = result

# Step 4
action_plan = generate_action_plan(data)
print("\n--- Action Plan ---\n")
print(action_plan)