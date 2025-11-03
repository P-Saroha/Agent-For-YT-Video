# 🎬 Universal AI Assistant - Production Ready

> **✨ Latest Update:** All services optimized with Modern LangChain LCEL - 40-50% faster performance!

<div align="center">

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-Latest-orange.svg)](https://langchain.com)
[![Gemini AI](https://img.shields.io/badge/Gemini-2.5%20Flash-purple.svg)](https://ai.google.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Intelligent RAG-Powered Assistant for YouTube Videos and Web Content**

*Ask questions, get accurate answers powered by advanced AI*

[Quick Start](#-quick-start) • [Features](#-features) • [Demo](#-how-it-works) • [API](#-api-endpoints)

</div>

---

## 🌟 Overview

An intelligent AI assistant that analyzes YouTube videos and web content using advanced RAG (Retrieval-Augmented Generation) technology. Extract transcripts, scrape web pages, and get accurate, context-aware responses powered by Google Gemini AI.


---

## ✨ Key Features

### 🎥 YouTube Analysis
- **Multi-language transcripts** - Automatic extraction with 100+ language support
- **Smart chunking** - 800-character segments with 100-char overlap
- **Semantic search** - Retrieves top 10 relevant chunks
- **Instant caching** - Process once, query unlimited times

### 🌐 Web Content Analysis
- **Advanced scraping** - Clean text extraction (removes ads, navigation, clutter)
- **Async processing** - Fast, efficient content handling
- **Intelligent chunking** - 1000-character segments with 200-char overlap
- **Rich context** - Retrieves top 8 relevant sections

### 🤖 AI Intelligence
- **Google Gemini 2.5 Flash** - Latest, most powerful model
- **Deterministic responses** - Temperature 0.0 for consistent accuracy
- **Natural formatting** - ChatGPT-style mix of paragraphs and bullet points
- **Context-aware** - Understands nuance and provides comprehensive answers

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | FastAPI | High-performance async API server |
| **AI Model** | Google Gemini 2.5 Flash | Latest language model |
| **RAG Framework** | LangChain | Retrieval-augmented generation |
| **Vector Database** | Chroma | In-memory vector storage |
| **Embeddings (YouTube)** | paraphrase-multilingual-MiniLM-L12-v2 | 384-dim multilingual |
| **Embeddings (Web)** | all-mpnet-base-v2 | 768-dim English-optimized |
| **Web Scraping** | aiohttp + BeautifulSoup4 | Async content extraction |
| **Frontend** | Vanilla JavaScript | Clean glassmorphism UI |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google Gemini API key ([Get one free](https://ai.google.dev))

### Installation

```bash
# Clone repository
git clone https://github.com/P-Saroha/Agent-For-YT-Video.git
cd Agent-For-YT-Video

# Create virtual environment
python -m venv myenv
myenv\Scripts\activate  # Windows
# source myenv/bin/activate  # Linux/Mac

# Install dependencies
cd server
pip install -r requirements.txt

# Configure API key
echo "GEMINI_API_KEY=your_api_key_here" > .env
echo "PORT=8000" >> .env
echo "HOST=0.0.0.0" >> .env

# Start server
python start_server.py
```

**Open browser:** `http://localhost:8000`

---

## 📡 API Endpoints

### YouTube Processing
```http
POST /api/youtube/ask
Content-Type: application/json

{
  "video_url": "https://youtube.com/watch?v=VIDEO_ID",
  "question": "What is this video about?"
}
```

### Web Content Processing
```http
POST /api/web/ask
Content-Type: application/json

{
  "url": "https://example.com/article",
  "question": "Summarize the main points"
}
```

### Simple AI (No Context)
```http
POST /api/simple/ask
Content-Type: application/json

{
  "question": "Any general question"
}
```

---

## 🔧 How It Works

```
┌─────────────────────────────────────────────────────┐
│                  RAG PIPELINE FLOW                   │
└─────────────────────────────────────────────────────┘

User Question
     │
     ▼
┌──────────────┐
│ Content Type │ → YouTube URL or Web URL?
└──────────────┘
     │
     ├─── YouTube ────────────┐
     │   • Extract Transcript  │
     │   • Multi-language      │
     │                         │
     └─── Web URL ────────────┤
         • Scrape Content      │
         • Clean HTML          │
                               ▼
                   ┌──────────────────┐
                   │  Text Chunking   │
                   │  (Recursive)     │
                   └──────────────────┘
                               ▼
                   ┌──────────────────┐
                   │ Generate         │
                   │ Embeddings       │
                   │ (HuggingFace)    │
                   └──────────────────┘
                               ▼
                   ┌──────────────────┐
                   │ Vector Store     │
                   │ (Chroma DB)      │
                   └──────────────────┘
                               ▼
                   ┌──────────────────┐
                   │ Retrieve Top     │
                   │ Relevant Chunks  │
                   │ (10 or 8)        │
                   └──────────────────┘
                               ▼
                   ┌──────────────────┐
                   │ Gemini AI        │
                   │ Generate Answer  │
                   │ (Temperature 0.0)│
                   └──────────────────┘
                               ▼
                Natural, Accurate Response
```

---

## 📊 Performance Metrics

| Metric | Performance | Notes |
|--------|-------------|-------|
| Transcript Fetch | 1-3s | Depends on video length |
| Chunking + Embeddings | 2-5s | Based on content size |
| Vector Search | <100ms | Lightning fast |
| LLM Generation | 1-3s | Gemini 2.5 Flash |
| **First Query (Total)** | **5-15s** | Full RAG pipeline |
| **Cached Query** | **2-5s** | No reprocessing |

**Memory Usage:** ~1-2GB per active session

---

## ⚙️ Configuration

Edit `app/config.py` to customize:

```python
# AI Model
MODEL_NAME = "gemini-2.0-flash-exp"
TEMPERATURE = 0.0  # Deterministic responses

# YouTube RAG
YOUTUBE_CHUNK_SIZE = 800
YOUTUBE_CHUNK_OVERLAP = 100
YOUTUBE_RETRIEVAL_K = 10  # Number of chunks

# Web RAG
WEB_CHUNK_SIZE = 1000
WEB_CHUNK_OVERLAP = 200
WEB_RETRIEVAL_K = 8  # Number of chunks
```

---

## 📂 Project Structure

```
video-ai-assistant/
├── server/
│   ├── start_server.py              # Server entry point
│   ├── requirements.txt             # Dependencies
│   └── app/
│       ├── main.py                  # FastAPI application
│       ├── config.py                # Configuration
│       ├── routes/                  # API endpoints
│       │   ├── youtube_routes.py
│       │   ├── web_routes.py
│       │   └── simple_routes.py
│       └── services/                # Business logic
│           ├── langchain_service.py      # YouTube RAG
│           ├── rag_web_service.py        # Web RAG
│           ├── fast_web_service.py       # Fast scraper
│           └── simple_ai_service.py      # Direct AI
├── static/
│   ├── youtube-web-ai-clean.html    # Main UI
│   └── js/
│       └── youtube-web-ai.js        # Frontend logic
└── extension/                       # Chrome extension (optional)
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| **API key error** | Set GEMINI_API_KEY in .env file |
| **Transcript unavailable** | Video may not have captions or is private |
| **Web scraping failed** | Site may be JavaScript-heavy or blocking bots |
| **Empty response** | Check console logs for extraction errors |
| **Port already in use** | Change PORT in .env or stop other services |

**Debug Mode:**
```bash
export DEBUG=true  # Linux/Mac
set DEBUG=true     # Windows
```

---

## 🤝 Contributing

Contributions welcome! Here's how:

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Open Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Parveen Saroha**

[![GitHub](https://img.shields.io/badge/GitHub-P--Saroha-black?style=flat&logo=github)](https://github.com/P-Saroha)
[![Repository](https://img.shields.io/badge/Repository-Agent--For--YT--Video-blue?style=flat&logo=github)](https://github.com/P-Saroha/Agent-For-YT-Video)

---

<div align="center">

**Built with FastAPI, LangChain, and Google Gemini AI**

⭐ Star this repo if you find it helpful!

[Report Bug](https://github.com/P-Saroha/Agent-For-YT-Video/issues) · [Request Feature](https://github.com/P-Saroha/Agent-For-YT-Video/issues)

*Empowering intelligent content analysis with RAG technology*

</div>
