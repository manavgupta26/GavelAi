# GavelAI

GavelAI is an AI-powered legal document analysis platform that helps users quickly analyze court judgements and legal PDFs. The system extracts important information from uploaded documents and generates structured AI insights for faster understanding and decision making.

---

## Features

- Upload and analyze judgement PDFs
- AI-generated legal summary
- Key directions extraction
- Action steps generation
- Risk analysis
- Approval recommendation
- Simple and clean UI
- Local AI processing using Ollama

---

## Tech Stack

- Python
- Streamlit
- Ollama
- Llama 3
- PDF Processing Libraries
- HTML/CSS

---

## How to Run

### 1. Clone or Download the Project

Download the project files or clone the repository.

### 2. Open the Project Folder

Open the folder in VS Code or terminal.

### 3. Install Required Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Ollama

Install Ollama on your system.

### 5. Download the Required Model

```bash
ollama pull llama3
```

### 6. Start the Application

```bash
streamlit run app.py
```

### 7. Open in Browser

Open the localhost link shown in the terminal.

---

## Workflow

1. User uploads a judgement PDF.
2. Text is extracted from the document.
3. The extracted content is processed using Llama 3 through Ollama.
4. AI generates:
   - Summary
   - Key directions
   - Action steps
   - Risk analysis
   - Recommendation
5. Results are displayed in a structured format.

---

## Future Improvements

- Multi-language support
- Faster PDF processing
- OCR support for scanned documents
- Cloud deployment
- Advanced legal search
- Real-time legal assistant

---

## Use Cases

- Legal document analysis
- Court judgement review
- Compliance verification
- Legal research assistance
- Faster case understanding

---

## Author
Shobhit Garg
Manav Gupta
