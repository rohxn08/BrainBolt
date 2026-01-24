
# BrainBolt: Multimodal RAG System

## Contents

1.  [Introduction](#1-introduction)
2.  [Demo](#2-demo)
3.  [Model Summary](#3-model-summary)
4.  [Features](#4-features)
5.  [Performance Metrics](#5-performance-metrics)
6.  [Tech Stack](#6-tech-stack)
7.  [Project Structure](#7-project-structure)
8.  [How to Run the App](#8-how-to-run-the-app)
9.  [Difficulties Faced](#9-difficulties-faced)
10. [Future Improvements](#10-future-improvements)

---

## 1. Introduction

BrainBolt is a **Multimodal RAG (Retrieval Augmented Generation) System** designed to revolutionize how users interact with complex information. Unlike traditional text-only assistants, BrainBolt seamlessly ingests, processes, and understands **documents (PDFs), images, web links, and YouTube videos**.

It leverages advanced **Multimodal Large Language Models (LLMs)** like Google Gemini 1.5 Pro to provide two core functionalities:
1.  **Summarizer Engine:** Transforming lengthy, complex multimodal content into concise, executive-level summaries or educational breakdowns.
2.  **Quiz Generator:** Instantly creating interactive, difficulty-graded quizzes from any uploaded material to test comprehension and active recall.

The application features a futuristic, "Neural Grid" styled interface built with custom HTML/CSS/JS, powered by a high-performance FastAPI backend.

---

## 2. Demo

*(Add your demo video or GIF here)*

---

## 3. Model Summary

BrainBolt utilizes a sophisticated pipeline that integrates retrieval systems with generative AI:

### A. Generative Engine: Google Gemini 1.5 Flash / Pro
The core reasoning and generation are handled by Gemini 1.5.

*   **Capabilities:** Multimodal understanding (native image and text processing), long-context window (up to 1M tokens), and high-speed inference.
*   **Role:** Synthesizes retrieved chunks into coherent summaries and generates context-aware quiz questions.
*   **Optimization:** Configured with `temperature=0.3` for factual consistency and `streaming=False` for robust JSON parsing.

### B. Retrieval System: FAISS + Embeddings
To handle large datasets without hallucination, we use a RAG architecture.

*   **Vector Store:** FAISS (Facebook AI Similarity Search) for millisecond-latency similarity search.
*   **Embedding Model:** `models/embedding-001` (Google) to convert text and image descriptions into high-dimensional vectors.
*   **Hybrid Retrieval:** Performs semantic search on text chunks and matches image captions to user queries, ensuring visual context is never lost.

---

## 4. Features

### Neural Grid Interface
*   **Universal Ingest:** One drop zone for PDFs, Images, Links, and Raw Text.
*   **Smart Type Detection:** Automatically routes files to the correct ingestor (OCR for images, parsing for PDFs, scraping for URLs).
*   **Dark Mode UI:** A premium, "Space Grotesk" typography-driven design with glassmorphism and neon accents.

### Intelligent Processors
*   **Summarizer Studio:**
    *   **Multiple Modes:** Concise, Detailed, Educational, Bullet Points, Executive, and Technical Deep Dive.
    *   **Multimodal Output:** The summary mentions text facts AND describes relevant images found in the source.
*   **Quiz Engine:**
    *   **Adaptive Difficulty:** Generates Easy, Medium, or Hard questions based on the depth of the content.
    *   **Interactive Feedback:** Instant validation of answers with explanations derived from the source material.

### 3. Pipeline Architecture
*   **OCR Integration:** Uses a fallback mechanism (Tesseract/PaddleOCR) to extract text from scanned documents or diagrams when standard extraction fails.
*   **YouTube Transcription:** Automatically fetches video captions to allow users to "chat" with video content without watching it.

---

## 5. Performance Metrics

### Measurement Methodology
To ensure scientific rigor, metrics were captured using the following instrumentation:
*   **TTFT (Time to First Token):** Measured from request dispatch → first token received from Gemini API.
*   **Latency:** Measured as end-to-end wall-clock time.
*   **Retrieval Time:** Measured independently (embedding + search) before LLM invocation.
*   **Throughput:** Computed as `total output tokens ÷ generation time`.

> **Note:** The evaluation scripts used to generate these metrics are intended for offline benchmarking and system analysis and are not part of the production request path.

### 5.1 Before Vector DB Integration
Below are the benchmarked performance metrics for the **Summarizer Engine** across various input types. All tests were conducted on a standard broadband connection.

| Input Type | Task | Total Latency (ms) | TTFT (ms) | Retrieval Time (ms) | Throughput (T/s) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PDF Document** | Summarize | 33,459 | 4,842 | 9,355 | 8.75 |
| **Raw Text** | Summarize | 24,769 | 3,687 | 16,151 | 11.61 |
| **Pure Image** | Summarize | 68,626 | 3,237 | 15,157 | 10.97 |
| **Text Heavy Image** | Summarize | 32,489 | 3,544 | 9,402 | 1,850.37* |
| **Live Web Search** | Summarize | 62,833 | 3,942 | 25,118 | 61.41 |
| **Web Link (Scrape)** | Summarize | 68,845 | 6,302 | 54,195 | 78.44 |
| **YouTube Video** | Summarize | 26,129 | 7,352 | 14,385 | 16.81 |

**Throughput Definition:** Throughput is measured as generated output tokens per second during the LLM generation phase only (excluding OCR and retrieval preprocessing). For OCR-heavy inputs, low generation length can result in unusually high throughput values.

**Key Observations:**
1.  **Retrieval Bottleneck:** For web links and search, the retrieval phase (scraping + embedding) dominates the total time (~54s for links).
2.  **High Throughput for OCR:** Text-heavy images showed an anomaly high throughput (1,850 T/s), explained by the definition above (efficient batch processing of OCR tokens vs short generation).
3.  **Video Efficiency:** YouTube summarization is surprisingly fast (~26s), comparable to raw text, as transcripts are lightweight compared to scraping heavy HTML pages.

| ![Latency Breakdown](docs/images/Retrieval%20vs%20generation.png) | ![BrainBolt Visualization](docs/images/brainbolt%20visualization.png) |
| :---: | :---: |

### 5.2 After Vector DB Integration
*(Benchmarks pending optimization and database integration)*

---

## 6. Tech Stack

### Frontend
*   **HTML5 / CSS3:** Custom-built "Neural Grid" design with CSS variables for theming.
*   **JavaScript (ES6+):** Vanilla JS for DOM manipulation, async API calls, and state management.
*   **Chart.js:** For visualizing metrics (optional debug mode).
*   **Lucide Icons:** For modern, lightweight SVG iconography.

### Backend & AI
*   **FastAPI:** High-performance async Python web framework.
*   **LangChain:** Framework for orchestrating RAG chains and LLM interactions.
*   **Google Gemini API:** Primary inference engine for embeddings and generation.
*   **FAISS:** Vector database for similarity search.
*   **BeautifulSoup4:** For web scraping and cleaning HTML content.
*   **YouTube Transcript API:** For extracting captions from videos.

### Infrastructure
*   **Uvicorn:** ASGI server for production-grade deployment.
*   **Pydantic:** Data validation and settings management.
*   **Python 3.10+:** Core runtime environment.

---

## 7. Project Structure

```bash
BrainBolt/
├── api.py                      # Main FastAPI Entry Point
├── start.bat                   # Windows Launcher Script
├── requirements.txt            # Project Dependencies
├── frontend/                   # UI Assets
│   ├── index.html              # Single Page Application
│   ├── style.css               # "Neural Grid" Styling
│   └── script.js               # Frontend Logic & API Client
├── src/
│   ├── pipeline.py             # Orchestrator
│   ├── processors/             # AI Logic Engines
│   │   ├── summarizer.py       # RAG Summarization Logic
│   │   ├── quiz_generator.py   # RAG Quiz Logic
│   │   └── multimodal_rag.py   # Core RAG Implementation
│   ├── ingestors/              # Data Loading Modules
│   │   ├── file.py             # PDF/Text Loader
│   │   ├── image.py            # OCR & Vision Loader
│   │   ├── youtube.py          # Video Transcript Loader
│   │   └── search.py           # Web Search Loader
│   └── utils/                  # Helpers (Startups, Logging)
└── data/                       # Local Storage for Ingested Files
```

---

## 8. How to Run the App

### Requirements
*   Python 3.10 or higher installed.
*   A valid **Google Gemini API Key**.

### Quick Start (Windows)
1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/your-repo/BrainBolt.git
    cd BrainBolt
    ```
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the Launcher**:
    Double-click `start.bat` (if available) or run:
    ```bash
    python api.py
    ```
4.  **Access the App**:
    Open your browser and navigate to `http://localhost:8000`.

---

## 9. Difficulties Faced

1.  **Multimodal RAG Complexity:**
    *   *Challenge:* Standard RAG only handles text. We needed to ingest images and keep them linked to their descriptive text.
    *   *Solution:* We implemented a dual-index strategy where images are captioned via Gemini-Vision, embedded as text, but the original base64 image is stored in a separate key-value store to be retrieved and displayed in the final answer.

2.  **API Rate Limiting (Resource Exhausted):**
    *   *Challenge:* The free tier of Gemini API often hits "429 Resource Exhausted" errors during parallel processing of large PDFs.
    *   *Solution:* Implemented exponential backoff in the API client and optimized chunk sizes (`chunk_size=1000`) to reduce the number of API calls per document.

3.  **Frontend-Backend Sync:**
    *   *Challenge:* Polling for generation status caused UI freezes.
    *   *Solution:* Switched to a robust Async/Await pattern in `script.js` with comprehensive error handling to keep the "Neural Grid" responsive even during 60-second generation tasks.

---

## 10. Future Improvements

*   **Streaming Responses:** Implement Server-Sent Events (SSE) to stream the summary token-by-token to the frontend for a "ChatGPT-like" typing effect.
*   **History Persistence:** Add a local database (SQLite) to save user summaries and quizzes so they persist after a page refresh.
*   **Deep Research Mode:** Allow the "Search" ingestor to recursively visit links found in the search results for a more comprehensive report.
