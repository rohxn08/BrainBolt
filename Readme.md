# BrainBolt ⚡

BrainBolt is a multimodal learning assistant that transforms various content types (Images, YouTube Videos, PDFs) into interactive quizzes and summaries.

## 🚀 Features (In Progress)

- **Multimodal Ingestion**: 
  - 📷 **Images**: Intelligent hybrid processing using Local OCR (PaddleOCR) for dense text and Gemini Vision for diagrams/charts.
  - 📺 **YouTube**: Transcript extraction and analysis.
  - 📄 **Files**: PDF and text document processing.
  - 🔍 **Web Search**: Dynamic content retrieval (DuckDuckGo).

- **Core Capabilities**:
  - 🧠 **Quiz Generation**: Automatically creates multiple-choice questions from ingested content using LLMs.
  - 📝 **Summarization** (Next): Concise explanations and summaries of complex topics.

## 🛠️ Architecture

- **Backend**: FastAPI (Upcoming)
- **Frontend**: Streamlit
- **AI/ML**: 
  - Google Gemini 1.5/2.0 Flash
  - PaddleOCR (Isolated Environment)
  - LangChain Orchestration

## 📦 Installation & Setup

1. **Environment Setup**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Isolated OCR Tool Setup** (Crucial for Local OCR):
   ```bash
   # Create a separate environment to avoid LangChain conflicts
   python -m venv .venv_ocr
   .venv_ocr\Scripts\python.exe -m pip install paddleocr paddlepaddle
   ```

3. **Running**:
   *(Instructions coming soon after main.py is implemented)*

## 📝 Roadmap

- [x] Image Ingestion (Hybrid OCR/Vision)
- [x] YouTube Ingestion
- [ ] Summarization Processor
- [ ] FastAPI Backend
- [ ] Streamlit UI
