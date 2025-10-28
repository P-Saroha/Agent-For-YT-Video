# 🎬 YouTube + Web AI Assistant# 🎬 YouTube AI Assistant - Optimized for Chrome Extension



**AI-powered content analysis for YouTube videos and web pages with advanced RAG (Retrieval Augmented Generation) system**## 🚀 **Optimized Storage & Performance System**



[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)### 📊 **Your Questions Answered**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)**Q: Do you store video transcripts when users provide video links?**

✅ **YES** - Smart caching system:

---- Transcripts are processed and stored in chunks

- Uses SQLite database for lightweight persistence

## 📋 Table of Contents- Implements LRU (Least Recently Used) cache management

- [Overview](#-overview)

- [Key Features](#-key-features)**Q: Are you using vector database to store transcripts?**  

- [How It Works](#-how-it-works)✅ **YES** - Optimized Chroma vector database:

- [Architecture](#-architecture)- HuggingFace embeddings for similarity search

- [Installation](#-installation)- Temporary vector stores per video

- [Usage](#-usage)- Smart cleanup to prevent storage bloat

- [API Documentation](#-api-documentation)

- [Troubleshooting](#-troubleshooting)**Q: Won't storing transcripts for every video be too large?**

✅ **SOLVED** - Multiple optimizations implemented:

---

## 🎯 **Extension Optimizations**

## 🎯 Overview

### 📏 **Size Limits**

This project provides an intelligent AI assistant that can:- **50KB max transcript** per video (truncated if larger)

- **Analyze YouTube videos** by processing transcripts- **800 characters max** per chunk (vs 1000 in original)

- **Scrape and analyze web content** from any URL- **20 chunks max** per video (vs unlimited)

- **Answer questions** using advanced RAG with vector similarity search- **5 videos max** in memory cache (LRU eviction)

- **Provide natural, ChatGPT-style responses** with mixed formatting

### 🗄️ **Smart Storage**

### What Makes This Special?- **SQLite database** for metadata (lightweight vs full embeddings)

- **Temporary vector stores** (cleaned up automatically)

✅ **Advanced RAG Pipeline** - Proper chunking, embeddings, and vector search  - **3-day auto cleanup** of old cache entries

✅ **Dual Content Support** - Both YouTube videos and web pages  - **LRU cache management** for memory efficiency

✅ **Clean Responses** - Natural mix of paragraphs and bullet points like ChatGPT  

✅ **High Performance** - Optimized chunk retrieval (10 chunks for YouTube, 8 for web)  ### ⚡ **Performance Optimizations**

✅ **Production Ready** - Clean code, no debug emojis, proper error handling  - **15-second timeout** for extension responsiveness

✅ **Modern UI** - Beautiful glassmorphism design with dark mode  - **Smaller embedding model** (`all-MiniLM-L6-v2` vs multilingual large)

- **3 similar chunks** for answers (vs 5)

---- **No source documents** returned to save memory

- **Async processing** with timeouts

## 🚀 Key Features

### 🧹 **Automatic Cleanup**

### 1. **YouTube Video Analysis**- Old videos auto-removed after 3 days

- Automatic transcript extraction (multiple language support)- Memory cache limited to 5 videos

- Intelligent chunking with 800-character segments- Temp directories cleaned up on exit

- 100-character overlap for context preservation- Database optimization built-in

- Vector embeddings using `paraphrase-multilingual-MiniLM-L12-v2`

- Retrieves top 10 most relevant chunks per query## 🛠️ **Three Implementation Levels**

- Caches processed videos for instant re-querying

| Feature | Custom | LangChain | Extension Optimized |

### 2. **Web Content Analysis**|---------|---------|-----------|-------------------|

- Advanced web scraping with BeautifulSoup4| **Memory Usage** | High | Medium | **Low** ✅ |

- JavaScript-rendered content support| **Storage** | File-based | Chroma | **SQLite + Temp** ✅ |

- Intelligent content extraction (removes nav, footer, ads)| **Cache Size** | Unlimited | Unlimited | **5 videos max** ✅ |

- 1000-character chunks with 200-character overlap| **Chunk Size** | 1500 chars | 1000 chars | **800 chars** ✅ |

- Vector embeddings using `all-mpnet-base-v2`| **Cleanup** | Manual | Manual | **Auto (3 days)** ✅ |

- Retrieves top 8 most relevant chunks per query| **Timeout** | None | None | **15 seconds** ✅ |

- URL caching for fast repeated analysis| **Transcript Limit** | None | None | **50KB max** ✅ |



### 3. **AI Response Quality**## 📡 **API Endpoints**

- Powered by **Google Gemini 2.5 Flash** (latest model)

- Temperature 0.0 for deterministic, factual answers### 🎬 **Extension Endpoints** (`/extension/*`)

- Natural ChatGPT-style formatting:```

  - Brief overview paragraphs (2-3 sentences)POST /extension/process-video     # Process video (optimized)

  - Bullet points for key facts and listsPOST /extension/ask-question      # Ask question (fast response)

  - Clear section breaks for readabilityGET  /extension/cache/stats       # View cache statistics

  - No excessive formatting or emojisPOST /extension/cache/cleanup     # Manual cleanup

- Aggressive post-processing to strip unwanted formattingGET  /extension/video/{id}/status # Check video status

DELETE /extension/video/{id}      # Remove specific video

---GET  /extension/health            # Health check

```

## 🔧 How It Works

### 🧠 **LangChain Endpoints** (`/langchain/*`)

### **RAG Pipeline Explained**```

POST /langchain/process-video     # Full LangChain processing

#### For YouTube Videos:POST /langchain/ask-question      # Advanced RAG with sources

GET  /langchain/health            # LangChain health

``````

1. User submits YouTube URL

   ↓### ⚙️ **Original Endpoints** (`/api/*`)

2. Extract video ID and fetch transcript```

   ↓POST /api/process-video           # Original custom implementation

3. Split transcript into 800-char chunks (overlap: 100 chars)POST /api/ask-question            # Original Q&A system

   ↓```

4. Generate embeddings using HuggingFace transformer

   ↓## 🧪 **Testing Interfaces**

5. Store in Chroma vector database (temporary directory)

   ↓1. **Extension Testing**: `http://127.0.0.1:8000/static/extension-test.html`

6. User asks question → Embed query   - Optimized for Chrome extension

   ↓   - Cache statistics monitoring

7. Cosine similarity search → Retrieve top 10 chunks   - Performance metrics

   ↓   - Cleanup controls

8. Pass to Gemini 2.5 Flash with structured prompt

   ↓2. **LangChain Comparison**: `http://127.0.0.1:8000/static/test-langchain.html`

9. Post-process response (strip markdown, emojis, excess formatting)   - Side-by-side comparison

   ↓   - Performance benchmarking

10. Return clean, natural answer to user   - Feature comparison

```

3. **Original Testing**: `http://127.0.0.1:8000/static/test.html`

#### For Web Pages:   - Original implementation testing



```## 🚀 **Quick Start**

1. User submits URL

   ↓### 1. **Start Server**

2. Fetch HTML with aiohttp (async)```powershell

   ↓cd f:\YT\video-ai-assistant

3. Parse with BeautifulSoup4 → Remove scripts, nav, footer.\myenv\Scripts\Activate.ps1

   ↓cd server

4. Extract main content (article, main, body tags)python start_server.py

   ↓```

5. Split into 1000-char chunks (overlap: 200 chars)

   ↓### 2. **Test Extension Optimization**

6. Generate embeddings using all-mpnet-base-v2```javascript

   ↓// Process video (optimized)

7. Store in Chroma vector database (temporary directory)fetch('http://127.0.0.1:8000/extension/process-video', {

   ↓    method: 'POST',

8. User asks question → Same RAG process as YouTube    headers: {'Content-Type': 'application/json'},

   ↓    body: JSON.stringify({video_url: 'https://youtube.com/watch?v=...'})

9. Retrieve top 8 most relevant chunks})

   ↓

10. Generate and return natural answer// Ask question (fast)

```fetch('http://127.0.0.1:8000/extension/ask-question', {

    method: 'POST', 

### **Key Technical Decisions**    headers: {'Content-Type': 'application/json'},

    body: JSON.stringify({video_id: 'abc123', question: 'What is this about?'})

| Component | Choice | Why? |})

|-----------|--------|------|

| **LLM** | Gemini 2.5 Flash | Latest, fast, cost-effective |// Check cache stats

| **Temperature** | 0.0 | Deterministic, factual responses |fetch('http://127.0.0.1:8000/extension/cache/stats')

| **Embeddings (YouTube)** | paraphrase-multilingual-MiniLM-L12-v2 | Supports multiple languages |```

| **Embeddings (Web)** | all-mpnet-base-v2 | Best quality for English content |

| **Vector DB** | Chroma | Easy, lightweight, fast |### 3. **Monitor Cache**

| **Chunk Size (YT)** | 800 chars | Balances context vs. precision |- View real-time cache statistics

| **Chunk Size (Web)** | 1000 chars | More content needed for web pages |- Monitor memory usage

| **Retrieval (YT)** | k=10 chunks | Comprehensive answers |- Track processing times

| **Retrieval (Web)** | k=8 chunks | Sufficient for most web content |- Automatic cleanup logs



---## 🎯 **Perfect for Chrome Extension**



## 🏗️ Architecture### ✅ **Why This Works for Extensions**

- **Lightweight**: SQLite database (not heavy vector files)

### **Tech Stack**- **Fast**: 15-second timeouts, optimized chunks

- **Clean**: Auto-cleanup prevents storage bloat

**Backend:**- **Smart**: LRU cache, size limits, efficient processing

- **FastAPI** - Modern async Python web framework- **Reliable**: Error handling, fallbacks, health monitoring

- **LangChain** - RAG orchestration framework

- **Google Gemini AI** - Latest 2.5 Flash model### 📱 **Extension Integration**

- **HuggingFace Transformers** - Embedding models```javascript

- **Chroma** - Vector database// Your Chrome extension can call:

- **BeautifulSoup4** - Web scrapingchrome.runtime.sendMessage({

- **aiohttp** - Async HTTP client    action: "processVideo",

- **youtube-transcript-api** - Transcript extraction    url: "https://youtube.com/watch?v=..."

});

**Frontend:**

- **Vanilla JavaScript** - No frameworks, pure performancechrome.runtime.sendMessage({

- **Modern CSS** - Glassmorphism design    action: "askQuestion", 

- **Responsive UI** - Works on all devices    videoId: "abc123",

    question: "What is this video about?"

### **Project Structure**});

```

```

video-ai-assistant/## 📊 **Storage Comparison**

├── server/                          # Backend server

│   ├── app/| Implementation | Storage Type | Size per Video | Cleanup |

│   │   ├── main.py                 # FastAPI application entry|---------------|--------------|----------------|---------|

│   │   ├── config.py               # Configuration settings| **Extension** ✅ | SQLite + Temp | ~2-5MB | Auto (3 days) |

│   │   ├── routes/                 # API endpoints| LangChain | Chroma DB | ~10-20MB | Manual |

│   │   │   ├── langchain_routes.py # YouTube analysis endpoints| Custom | File-based | ~5-15MB | Manual |

│   │   │   ├── web_routes.py       # Web scraping endpoints

│   │   │   ├── simple_routes.py    # Alternative endpoints## 🎉 **Ready for Production**

│   │   │   └── health.py           # Health check

│   │   ├── services/               # Core business logicYour YouTube AI Assistant is now optimized for Chrome extension deployment with:

│   │   │   ├── langchain_service.py    # YouTube RAG service- ✅ Smart storage management

│   │   │   ├── rag_web_service.py      # Web content RAG service- ✅ Performance optimization  

│   │   │   ├── fast_web_service.py     # Lightweight web service- ✅ Automatic cleanup

│   │   │   └── simple_ai_service.py    # Fallback service- ✅ Size limitations

│   │   └── models/                 # Data models- ✅ Fast responses

│   ├── static/                     # Frontend files- ✅ Production-ready caching

│   │   ├── youtube-web-ai-clean.html   # Main UI

│   │   ├── css/Test the optimized version at: **http://127.0.0.1:8000/static/extension-test.html**

│   │   │   └── youtube-web-ai.css      # Styles

│   │   └── js/An intelligent Chrome extension that allows users to ask questions about YouTube video content using AI. The extension extracts video transcripts, processes them with AI, and provides accurate answers based on the video content.

│   │       └── youtube-web-ai.js       # Frontend logic

│   ├── requirements.txt            # Python dependencies## Features

│   └── start_server.py            # Server startup script

├── extension/                      # Chrome extension (optional)- 🎥 **YouTube Integration**: Automatically detects YouTube videos and extracts transcripts

│   ├── manifest.json- 🤖 **AI-Powered Q&A**: Ask any question about video content and get intelligent answers

│   ├── popup.html- 🔍 **Semantic Search**: Find relevant sections of videos based on your questions

│   ├── popup.js- 💬 **Chat Interface**: Intuitive chat-style interface for asking questions

│   └── background/- ⚡ **Real-time Processing**: Fast response times with efficient text chunking and embedding

├── myenv/                          # Python virtual environment- 🔒 **Privacy Focused**: Process videos on-demand, no permanent storage of personal data

├── README.md                       # This file

└── LICENSE                         # MIT License## Architecture

```

### Frontend (Chrome Extension)

---- **Manifest V3** Chrome extension

- **Content Scripts** for YouTube integration

## 📦 Installation- **Popup Interface** for user interaction

- **Background Service Worker** for coordination

### **Prerequisites**

- Python 3.11 or higher### Backend (FastAPI)

- pip (Python package manager)- **FastAPI** web framework

- 8GB RAM minimum (for embedding models)- **YouTube Transcript API** for video content extraction

- Internet connection (for API calls)- **OpenAI GPT** for question answering

- **Sentence Transformers** for text embeddings

### **Step 1: Clone Repository**- **FAISS** for vector similarity search

```bash

git clone https://github.com/P-Saroha/Agent-For-YT-Video.git## Quick Start

cd video-ai-assistant

```### Prerequisites

- Python 3.11+

### **Step 2: Create Virtual Environment**- Node.js (optional, for development)

```bash- OpenAI API key

python -m venv myenv- YouTube API key (optional, for enhanced metadata)



# On Windows### Installation

myenv\Scripts\activate

1. **Clone the repository**

# On macOS/Linux   ```bash

source myenv/bin/activate   git clone <repository-url>

```   cd video-ai-assistant

   ```

### **Step 3: Install Dependencies**

```bash2. **Set up the backend**

cd server   ```bash

pip install -r requirements.txt   cd server

```   python -m venv venv

   

### **Step 4: Configure API Key**   # On Windows

Create a `.env` file in the `server` directory:   venv\Scripts\activate

```env   # On macOS/Linux

GEMINI_API_KEY=your_gemini_api_key_here   source venv/bin/activate

```   

   pip install -r requirements.txt

**Get your Gemini API key:**   ```

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)

2. Click "Create API Key"3. **Configure environment variables**

3. Copy and paste into `.env` file   ```bash

   cp .env.example .env

### **Step 5: Start Server**   # Edit .env with your API keys

```bash   ```

# From server directory

python start_server.py4. **Start the backend server**

   ```bash

# Or using uvicorn directly   uvicorn app.main:app --reload

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000   ```

```

5. **Build and install the extension**

Server will start at: **http://localhost:8000**   ```bash

   # Build the extension

---   cd ../

   chmod +x scripts/build_ext.sh

## 🎮 Usage   ./scripts/build_ext.sh

   ```

### **Web Interface**

6. **Load extension in Chrome**

1. Open browser and navigate to:   - Open Chrome and go to `chrome://extensions/`

   ```   - Enable "Developer mode"

   http://localhost:8000/static/youtube-web-ai-clean.html   - Click "Load unpacked" and select `extension/build/` folder

   ```

## Usage

2. **For YouTube Videos:**

   - Switch to "YouTube Analysis" mode1. **Navigate to any YouTube video**

   - Paste any YouTube URL2. **Click the extension icon** to open the AI assistant

   - Click "Analyze Video"3. **Process the video** by clicking "Process Video" (or it auto-detects current video)

   - Wait for processing (5-15 seconds)4. **Ask questions** about the video content in the chat interface

   - Ask questions in the text box5. **Get AI-powered answers** based on the video transcript

   - Get instant, intelligent answers

## Example Questions

3. **For Web Pages:**

   - Switch to "Web Analysis" mode- "What are the main topics discussed in this video?"

   - Paste any website URL- "Can you summarize the key points?"

   - Click "Analyze Website"- "What did they say about [specific topic]?"

   - Wait for scraping (3-10 seconds)- "At what time do they discuss [topic]?"

   - Ask questions about the content- "What are the conclusions or takeaways?"

   - Get answers based on page content

## API Endpoints

### **Example Questions**

### Process Video

**For YouTube Videos:**```http

```POST /process-video

"What is the main topic of this video?"Content-Type: application/json

"Summarize the key points"

"What does the speaker say about [topic]?"{

"List the steps mentioned in the tutorial"  "video_url": "https://www.youtube.com/watch?v=VIDEO_ID"

```}

```

**For Web Pages:**

```### Ask Question

"What is this article about?"```http

"What are the main features discussed?"POST /ask-question

"Summarize the pricing information"Content-Type: application/json

"What requirements are mentioned?"

```{

  "video_id": "VIDEO_ID",

---  "question": "Your question here"

}

## 📚 API Documentation```



### **Health Check**### Health Check

```http```http

GET /healthGET /health

``````

Returns API status and version information.

## Development

### **YouTube Video Processing**

```http### Backend Development

POST /langchain/process-video```bash

Content-Type: application/jsoncd server

pip install -r requirements.txt

{uvicorn app.main:app --reload --log-level debug

  "video_url": "https://www.youtube.com/watch?v=VIDEO_ID"```

}

```### Extension Development

```bash

**Response:**# Build extension

```json./scripts/build_ext.sh

{

  "video_id": "VIDEO_ID",# The extension files are in extension/build/

  "title": "Video Title",# Reload the extension in Chrome after changes

  "channel": "Channel Name",```

  "chunks_count": 45,

  "language": "en",### Docker Development

  "status": "processed"```bash

}cd deploy

```docker-compose up --build

```

### **Ask Question (YouTube)**

```http## Configuration

POST /langchain/ask-question

Content-Type: application/json### Environment Variables



{| Variable | Description | Default |

  "video_id": "VIDEO_ID",|----------|-------------|---------|

  "question": "What is the main topic?"| `OPENAI_API_KEY` | OpenAI API key for GPT | Required |

}| `OPENAI_MODEL` | GPT model to use | `gpt-3.5-turbo` |

```| `YOUTUBE_API_KEY` | YouTube Data API key | Optional |

| `VECTOR_STORE_PATH` | Path for vector storage | `store/faiss` |

**Response:**| `EMBEDDINGS_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` |

```json| `CACHE_TTL` | Cache time-to-live (seconds) | `3600` |

{

  "question": "What is the main topic?",### Extension Configuration

  "answer": "The video discusses...\n\nKey points:\n- Point 1\n- Point 2\n...",

  "confidence": 0.85,The extension automatically connects to `http://localhost:8000` by default. For production deployment, update the API endpoint in `extension/popup.js`.

  "method": "langchain_qa",

  "language": "en"## Deployment

}

```### Using Docker

```bash

### **Web Content Analysis**cd deploy

```httpdocker-compose up -d

POST /web/extract-content```

Content-Type: application/json

### Manual Deployment

{1. Deploy the FastAPI backend to your preferred platform (Railway, Render, etc.)

  "url": "https://example.com/article"2. Update the API endpoint in the extension

}3. Build and package the extension for Chrome Web Store

```

## Troubleshooting

**Response:**

```json### Common Issues

{

  "url": "https://example.com/article",1. **"Video processing failed"**

  "title": "Article Title",   - Check if the video has available transcripts

  "content": "Full extracted text...",   - Verify YouTube API key (if used)

  "word_count": 1234,   - Check server logs for errors

  "char_count": 7890

}2. **"Server connection failed"**

```   - Ensure backend server is running on port 8000

   - Check CORS configuration

### **Ask Question (Web)**   - Verify firewall settings

```http

POST /web/ask-question3. **"No embeddings generated"**

Content-Type: application/json   - Check OpenAI API key

   - Verify sentence-transformers installation

{   - Check available disk space for model downloads

  "url": "https://example.com/article",

  "question": "What is discussed in this article?"### Debug Mode

}

```Enable debug mode by setting `DEBUG=True` in your `.env` file for detailed logging.



**Response:**## Contributing

```json

{1. Fork the repository

  "success": true,2. Create a feature branch

  "answer": "The article covers...\n\nMain topics:\n- Topic 1\n- Topic 2\n...",3. Make your changes

  "url": "https://example.com/article",4. Add tests if applicable

  "title": "Article Title",5. Submit a pull request

  "confidence": 0.8,

  "chunks_used": 8## License

}

```This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.



---## Acknowledgments



## 📊 Performance- [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) for transcript extraction

- [sentence-transformers](https://github.com/UKPLab/sentence-transformers) for text embeddings

### **Speed Benchmarks**- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework

- [OpenAI](https://openai.com/) for GPT models

| Operation | Time | Notes |
|-----------|------|-------|
| YouTube transcript fetch | 1-3s | Depends on video length |
| Chunking + embeddings | 2-5s | Based on content size |
| Vector search | <100ms | Very fast similarity search |
| LLM generation | 1-3s | Gemini 2.5 Flash response |
| **Total (first query)** | **5-15s** | Full RAG pipeline |
| **Total (cached)** | **2-5s** | No re-processing needed |

### **Memory Usage**

| Component | RAM Usage | Notes |
|-----------|-----------|-------|
| FastAPI server | ~200MB | Base application |
| Embedding model | ~400MB | HuggingFace transformer |
| Vector database | ~50-200MB | Per processed video/page |
| Chroma overhead | ~100MB | Database operations |
| **Total** | **~1-2GB** | Per active session |

---

## 🐛 Troubleshooting

### **Common Issues**

**1. "Could not get transcript"**
- Video may not have captions/transcript available
- Video may be private or age-restricted
- Try a different video

**2. "HTTP 403 Forbidden" (Web scraping)**
- Website blocks automated scraping
- Try a different URL
- Some sites require JavaScript rendering

**3. "Out of memory" error**
- Reduce chunk_size in config
- Reduce retrieval_k in config
- Process smaller content
- Increase system RAM

**4. "Gemini API error"**
- Check API key is correct in `.env`
- Verify API key has quota remaining
- Check internet connection

**5. Server won't start**
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill process using port (Windows)
taskkill /PID <process_id> /F

# Try different port
uvicorn app.main:app --port 8080
```

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Pankaj Saroha**
- GitHub: [@P-Saroha](https://github.com/P-Saroha)
- Repository: [Agent-For-YT-Video](https://github.com/P-Saroha/Agent-For-YT-Video)

---

## 🙏 Acknowledgments

- **Google Gemini** - Powerful LLM for generation
- **LangChain** - RAG orchestration framework
- **HuggingFace** - Transformer models and embeddings
- **Chroma** - Vector database
- **FastAPI** - Modern Python web framework
- **YouTube Transcript API** - Transcript extraction

---

<div align="center">

**Made with ❤️ by Pankaj Saroha**

⭐ Star this repo if you find it helpful!

[Report Bug](https://github.com/P-Saroha/Agent-For-YT-Video/issues) · [Request Feature](https://github.com/P-Saroha/Agent-For-YT-Video/issues)

</div>
