# 🎬 YouTube AI Assistant - Optimized for Chrome Extension

## 🚀 **Optimized Storage & Performance System**

### 📊 **Your Questions Answered**

**Q: Do you store video transcripts when users provide video links?**
✅ **YES** - Smart caching system:
- Transcripts are processed and stored in chunks
- Uses SQLite database for lightweight persistence
- Implements LRU (Least Recently Used) cache management

**Q: Are you using vector database to store transcripts?**  
✅ **YES** - Optimized Chroma vector database:
- HuggingFace embeddings for similarity search
- Temporary vector stores per video
- Smart cleanup to prevent storage bloat

**Q: Won't storing transcripts for every video be too large?**
✅ **SOLVED** - Multiple optimizations implemented:

## 🎯 **Extension Optimizations**

### 📏 **Size Limits**
- **50KB max transcript** per video (truncated if larger)
- **800 characters max** per chunk (vs 1000 in original)
- **20 chunks max** per video (vs unlimited)
- **5 videos max** in memory cache (LRU eviction)

### 🗄️ **Smart Storage**
- **SQLite database** for metadata (lightweight vs full embeddings)
- **Temporary vector stores** (cleaned up automatically)
- **3-day auto cleanup** of old cache entries
- **LRU cache management** for memory efficiency

### ⚡ **Performance Optimizations**
- **15-second timeout** for extension responsiveness
- **Smaller embedding model** (`all-MiniLM-L6-v2` vs multilingual large)
- **3 similar chunks** for answers (vs 5)
- **No source documents** returned to save memory
- **Async processing** with timeouts

### 🧹 **Automatic Cleanup**
- Old videos auto-removed after 3 days
- Memory cache limited to 5 videos
- Temp directories cleaned up on exit
- Database optimization built-in

## 🛠️ **Three Implementation Levels**

| Feature | Custom | LangChain | Extension Optimized |
|---------|---------|-----------|-------------------|
| **Memory Usage** | High | Medium | **Low** ✅ |
| **Storage** | File-based | Chroma | **SQLite + Temp** ✅ |
| **Cache Size** | Unlimited | Unlimited | **5 videos max** ✅ |
| **Chunk Size** | 1500 chars | 1000 chars | **800 chars** ✅ |
| **Cleanup** | Manual | Manual | **Auto (3 days)** ✅ |
| **Timeout** | None | None | **15 seconds** ✅ |
| **Transcript Limit** | None | None | **50KB max** ✅ |

## 📡 **API Endpoints**

### 🎬 **Extension Endpoints** (`/extension/*`)
```
POST /extension/process-video     # Process video (optimized)
POST /extension/ask-question      # Ask question (fast response)
GET  /extension/cache/stats       # View cache statistics
POST /extension/cache/cleanup     # Manual cleanup
GET  /extension/video/{id}/status # Check video status
DELETE /extension/video/{id}      # Remove specific video
GET  /extension/health            # Health check
```

### 🧠 **LangChain Endpoints** (`/langchain/*`)
```
POST /langchain/process-video     # Full LangChain processing
POST /langchain/ask-question      # Advanced RAG with sources
GET  /langchain/health            # LangChain health
```

### ⚙️ **Original Endpoints** (`/api/*`)
```
POST /api/process-video           # Original custom implementation
POST /api/ask-question            # Original Q&A system
```

## 🧪 **Testing Interfaces**

1. **Extension Testing**: `http://127.0.0.1:8000/static/extension-test.html`
   - Optimized for Chrome extension
   - Cache statistics monitoring
   - Performance metrics
   - Cleanup controls

2. **LangChain Comparison**: `http://127.0.0.1:8000/static/test-langchain.html`
   - Side-by-side comparison
   - Performance benchmarking
   - Feature comparison

3. **Original Testing**: `http://127.0.0.1:8000/static/test.html`
   - Original implementation testing

## 🚀 **Quick Start**

### 1. **Start Server**
```powershell
cd f:\YT\video-ai-assistant
.\myenv\Scripts\Activate.ps1
cd server
python start_server.py
```

### 2. **Test Extension Optimization**
```javascript
// Process video (optimized)
fetch('http://127.0.0.1:8000/extension/process-video', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({video_url: 'https://youtube.com/watch?v=...'})
})

// Ask question (fast)
fetch('http://127.0.0.1:8000/extension/ask-question', {
    method: 'POST', 
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({video_id: 'abc123', question: 'What is this about?'})
})

// Check cache stats
fetch('http://127.0.0.1:8000/extension/cache/stats')
```

### 3. **Monitor Cache**
- View real-time cache statistics
- Monitor memory usage
- Track processing times
- Automatic cleanup logs

## 🎯 **Perfect for Chrome Extension**

### ✅ **Why This Works for Extensions**
- **Lightweight**: SQLite database (not heavy vector files)
- **Fast**: 15-second timeouts, optimized chunks
- **Clean**: Auto-cleanup prevents storage bloat
- **Smart**: LRU cache, size limits, efficient processing
- **Reliable**: Error handling, fallbacks, health monitoring

### 📱 **Extension Integration**
```javascript
// Your Chrome extension can call:
chrome.runtime.sendMessage({
    action: "processVideo",
    url: "https://youtube.com/watch?v=..."
});

chrome.runtime.sendMessage({
    action: "askQuestion", 
    videoId: "abc123",
    question: "What is this video about?"
});
```

## 📊 **Storage Comparison**

| Implementation | Storage Type | Size per Video | Cleanup |
|---------------|--------------|----------------|---------|
| **Extension** ✅ | SQLite + Temp | ~2-5MB | Auto (3 days) |
| LangChain | Chroma DB | ~10-20MB | Manual |
| Custom | File-based | ~5-15MB | Manual |

## 🎉 **Ready for Production**

Your YouTube AI Assistant is now optimized for Chrome extension deployment with:
- ✅ Smart storage management
- ✅ Performance optimization  
- ✅ Automatic cleanup
- ✅ Size limitations
- ✅ Fast responses
- ✅ Production-ready caching

Test the optimized version at: **http://127.0.0.1:8000/static/extension-test.html**

An intelligent Chrome extension that allows users to ask questions about YouTube video content using AI. The extension extracts video transcripts, processes them with AI, and provides accurate answers based on the video content.

## Features

- 🎥 **YouTube Integration**: Automatically detects YouTube videos and extracts transcripts
- 🤖 **AI-Powered Q&A**: Ask any question about video content and get intelligent answers
- 🔍 **Semantic Search**: Find relevant sections of videos based on your questions
- 💬 **Chat Interface**: Intuitive chat-style interface for asking questions
- ⚡ **Real-time Processing**: Fast response times with efficient text chunking and embedding
- 🔒 **Privacy Focused**: Process videos on-demand, no permanent storage of personal data

## Architecture

### Frontend (Chrome Extension)
- **Manifest V3** Chrome extension
- **Content Scripts** for YouTube integration
- **Popup Interface** for user interaction
- **Background Service Worker** for coordination

### Backend (FastAPI)
- **FastAPI** web framework
- **YouTube Transcript API** for video content extraction
- **OpenAI GPT** for question answering
- **Sentence Transformers** for text embeddings
- **FAISS** for vector similarity search

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js (optional, for development)
- OpenAI API key
- YouTube API key (optional, for enhanced metadata)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd video-ai-assistant
   ```

2. **Set up the backend**
   ```bash
   cd server
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Start the backend server**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Build and install the extension**
   ```bash
   # Build the extension
   cd ../
   chmod +x scripts/build_ext.sh
   ./scripts/build_ext.sh
   ```

6. **Load extension in Chrome**
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked" and select `extension/build/` folder

## Usage

1. **Navigate to any YouTube video**
2. **Click the extension icon** to open the AI assistant
3. **Process the video** by clicking "Process Video" (or it auto-detects current video)
4. **Ask questions** about the video content in the chat interface
5. **Get AI-powered answers** based on the video transcript

## Example Questions

- "What are the main topics discussed in this video?"
- "Can you summarize the key points?"
- "What did they say about [specific topic]?"
- "At what time do they discuss [topic]?"
- "What are the conclusions or takeaways?"

## API Endpoints

### Process Video
```http
POST /process-video
Content-Type: application/json

{
  "video_url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

### Ask Question
```http
POST /ask-question
Content-Type: application/json

{
  "video_id": "VIDEO_ID",
  "question": "Your question here"
}
```

### Health Check
```http
GET /health
```

## Development

### Backend Development
```bash
cd server
pip install -r requirements.txt
uvicorn app.main:app --reload --log-level debug
```

### Extension Development
```bash
# Build extension
./scripts/build_ext.sh

# The extension files are in extension/build/
# Reload the extension in Chrome after changes
```

### Docker Development
```bash
cd deploy
docker-compose up --build
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for GPT | Required |
| `OPENAI_MODEL` | GPT model to use | `gpt-3.5-turbo` |
| `YOUTUBE_API_KEY` | YouTube Data API key | Optional |
| `VECTOR_STORE_PATH` | Path for vector storage | `store/faiss` |
| `EMBEDDINGS_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` |
| `CACHE_TTL` | Cache time-to-live (seconds) | `3600` |

### Extension Configuration

The extension automatically connects to `http://localhost:8000` by default. For production deployment, update the API endpoint in `extension/popup.js`.

## Deployment

### Using Docker
```bash
cd deploy
docker-compose up -d
```

### Manual Deployment
1. Deploy the FastAPI backend to your preferred platform (Railway, Render, etc.)
2. Update the API endpoint in the extension
3. Build and package the extension for Chrome Web Store

## Troubleshooting

### Common Issues

1. **"Video processing failed"**
   - Check if the video has available transcripts
   - Verify YouTube API key (if used)
   - Check server logs for errors

2. **"Server connection failed"**
   - Ensure backend server is running on port 8000
   - Check CORS configuration
   - Verify firewall settings

3. **"No embeddings generated"**
   - Check OpenAI API key
   - Verify sentence-transformers installation
   - Check available disk space for model downloads

### Debug Mode

Enable debug mode by setting `DEBUG=True` in your `.env` file for detailed logging.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) for transcript extraction
- [sentence-transformers](https://github.com/UKPLab/sentence-transformers) for text embeddings
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [OpenAI](https://openai.com/) for GPT models
