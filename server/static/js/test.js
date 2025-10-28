/* Test.html JavaScript */

// Redirect to the new universal interface after 3 seconds
setTimeout(function() {
    window.location.href = '/static/youtube-web-ai.html';
}, 3000);

// YouTube AI Tester Class (legacy functionality)
class YouTubeAITester {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000';
        this.currentVideoId = null;
        this.isProcessing = false;
        this.initializeElements();
        this.attachEventListeners();
    }

    initializeElements() {
        this.elements = {
            videoUrl: document.getElementById('videoUrl'),
            processVideoBtn: document.getElementById('processVideo'),
            videoInfo: document.getElementById('videoInfo'),
            videoThumbnail: document.getElementById('videoThumbnail'),
            videoTitle: document.getElementById('videoTitle'),
            videoChannel: document.getElementById('videoChannel'),
            processingStatus: document.getElementById('processingStatus'),
            chatSection: document.getElementById('chatSection'),
            chatMessages: document.getElementById('chatMessages'),
            questionInput: document.getElementById('questionInput'),
            sendQuestionBtn: document.getElementById('sendQuestion'),
            loading: document.getElementById('loading'),
            error: document.getElementById('error'),
            errorMessage: document.getElementById('errorMessage')
        };
    }

    attachEventListeners() {
        if (this.elements.processVideoBtn) {
            this.elements.processVideoBtn.addEventListener('click', () => this.processVideo());
        }
        if (this.elements.sendQuestionBtn) {
            this.elements.sendQuestionBtn.addEventListener('click', () => this.sendQuestion());
        }
        if (this.elements.questionInput) {
            this.elements.questionInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.sendQuestion();
            });
        }
        if (this.elements.videoUrl) {
            this.elements.videoUrl.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.processVideo();
            });
        }
    }

    extractVideoId(url) {
        const regex = /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/;
        const match = url.match(regex);
        return match ? match[1] : null;
    }

    async processVideo() {
        const videoUrl = this.elements.videoUrl.value.trim();
        if (!videoUrl) {
            this.showError('Please enter a YouTube video URL');
            return;
        }

        const videoId = this.extractVideoId(videoUrl);
        if (!videoId) {
            this.showError('Please enter a valid YouTube video URL');
            return;
        }

        this.currentVideoId = videoId;
        this.showLoading('Processing video...');
        this.hideError();

        try {
            // Get video info first
            const videoInfo = await this.fetchVideoInfo(videoId);
            this.displayVideoInfo(videoInfo);

            // Process the video
            const response = await fetch(`${this.apiBaseUrl}/langchain/process-video`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ video_url: videoUrl })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            this.onVideoProcessed(result);

        } catch (error) {
            console.error('Error processing video:', error);
            this.showError(`Failed to process video: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    async fetchVideoInfo(videoId) {
        // For demo purposes, we'll create a placeholder
        // In a real app, you'd call YouTube API
        return {
            title: 'YouTube Video',
            channel: 'Channel Name',
            thumbnail: `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`
        };
    }

    displayVideoInfo(videoInfo) {
        if (this.elements.videoThumbnail) {
            this.elements.videoThumbnail.src = videoInfo.thumbnail;
        }
        if (this.elements.videoTitle) {
            this.elements.videoTitle.textContent = videoInfo.title;
        }
        if (this.elements.videoChannel) {
            this.elements.videoChannel.textContent = videoInfo.channel;
        }
        if (this.elements.processingStatus) {
            this.elements.processingStatus.textContent = 'Processing...';
            this.elements.processingStatus.className = 'status processing';
        }
        if (this.elements.videoInfo) {
            this.elements.videoInfo.classList.add('show');
        }
    }

    onVideoProcessed(result) {
        if (this.elements.processingStatus) {
            this.elements.processingStatus.textContent = 'Ready for questions!';
            this.elements.processingStatus.className = 'status ready';
        }
        if (this.elements.chatSection) {
            this.elements.chatSection.classList.add('show');
        }
        if (this.elements.questionInput) {
            this.elements.questionInput.focus();
        }

        // Clear any previous messages except welcome
        if (this.elements.chatMessages) {
            const messages = this.elements.chatMessages.querySelectorAll('.message');
            messages.forEach(msg => msg.remove());
        }
    }

    async sendQuestion() {
        if (!this.elements.questionInput) return;
        
        const question = this.elements.questionInput.value.trim();
        if (!question || !this.currentVideoId || this.isProcessing) return;

        this.isProcessing = true;
        this.addMessage(question, 'user');
        this.elements.questionInput.value = '';
        if (this.elements.sendQuestionBtn) {
            this.elements.sendQuestionBtn.disabled = true;
        }
        this.showLoading('Thinking...');

        try {
            const response = await fetch(`${this.apiBaseUrl}/langchain/ask-question`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    video_id: this.currentVideoId,
                    question: question
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            this.addMessage(result.answer, 'ai');

        } catch (error) {
            console.error('Error asking question:', error);
            this.addMessage(`Sorry, I encountered an error: ${error.message}. Please try again.`, 'ai');
        } finally {
            this.isProcessing = false;
            if (this.elements.sendQuestionBtn) {
                this.elements.sendQuestionBtn.disabled = false;
            }
            this.hideLoading();
        }
    }

    addMessage(content, sender) {
        if (!this.elements.chatMessages) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (sender === 'ai' && typeof marked !== 'undefined') {
            // Configure marked for better rendering
            marked.setOptions({
                breaks: true,  // Convert line breaks to <br>
                gfm: true,     // GitHub Flavored Markdown
                headerIds: false,
                mangle: false
            });
            
            // Render markdown for AI responses
            try {
                contentDiv.innerHTML = marked.parse(content);
                
                // Apply syntax highlighting if highlight.js is available
                if (typeof hljs !== 'undefined') {
                    contentDiv.querySelectorAll('pre code').forEach((block) => {
                        hljs.highlightElement(block);
                    });
                }
            } catch (error) {
                console.error('Markdown parsing error:', error);
                contentDiv.textContent = content; // Fallback to plain text
            }
        } else {
            // Plain text for user messages
            contentDiv.textContent = content;
        }

        messageDiv.appendChild(contentDiv);
        this.elements.chatMessages.appendChild(messageDiv);

        // Scroll to bottom
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }

    showLoading(message = 'Loading...') {
        if (this.elements.loading) {
            const loadingP = this.elements.loading.querySelector('p');
            if (loadingP) {
                loadingP.textContent = message;
            }
            this.elements.loading.classList.add('show');
        }
    }

    hideLoading() {
        if (this.elements.loading) {
            this.elements.loading.classList.remove('show');
        }
    }

    showError(message) {
        if (this.elements.errorMessage) {
            this.elements.errorMessage.textContent = message;
        }
        if (this.elements.error) {
            this.elements.error.classList.add('show');
        }
    }

    hideError() {
        if (this.elements.error) {
            this.elements.error.classList.remove('show');
        }
    }
}

// Initialize the tester when the page loads (only if elements exist)
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('videoUrl')) {
        new YouTubeAITester();
    }
});