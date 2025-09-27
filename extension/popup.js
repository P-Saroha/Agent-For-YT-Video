// YouTube AI Assistant Popup Script
// Update this URL when deploying to production
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : 'https://your-deployed-app.vercel.app'; // Replace with your deployed URL

class YouTubeAIAssistant {
    constructor() {
        this.currentVideoId = null;
        this.isProcessing = false;
        this.initializeElements();
        this.attachEventListeners();
        this.checkCurrentTab();
    }

    initializeElements() {
        this.elements = {
            videoInfo: document.getElementById('videoInfo'),
            videoThumbnail: document.getElementById('videoThumbnail'),
            videoTitle: document.getElementById('videoTitle'),
            videoChannel: document.getElementById('videoChannel'),
            processingStatus: document.getElementById('processingStatus'),
            urlInput: document.getElementById('urlInput'),
            videoUrlInput: document.getElementById('videoUrl'),
            processVideoBtn: document.getElementById('processVideo'),
            chatSection: document.getElementById('chatSection'),
            chatContainer: document.getElementById('chatContainer'),
            questionInput: document.getElementById('questionInput'),
            sendQuestionBtn: document.getElementById('sendQuestion'),
            loading: document.getElementById('loading'),
            error: document.getElementById('error'),
            errorMessage: document.getElementById('errorMessage'),
            retryBtn: document.getElementById('retryBtn')
        };
    }

    attachEventListeners() {
        this.elements.processVideoBtn.addEventListener('click', () => this.processVideo());
        this.elements.sendQuestionBtn.addEventListener('click', () => this.sendQuestion());
        this.elements.questionInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendQuestion();
        });
        this.elements.videoUrlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.processVideo();
        });
        this.elements.retryBtn.addEventListener('click', () => this.hideError());
    }

    async checkCurrentTab() {
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (tab.url && tab.url.includes('youtube.com/watch')) {
                const videoId = this.extractVideoId(tab.url);
                if (videoId) {
                    this.elements.videoUrlInput.value = tab.url;
                    this.currentVideoId = videoId;
                }
            }
        } catch (error) {
            console.log('Could not check current tab:', error);
        }
    }

    extractVideoId(url) {
        const regex = /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/;
        const match = url.match(regex);
        return match ? match[1] : null;
    }

    async processVideo() {
        const videoUrl = this.elements.videoUrlInput.value.trim();
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

            // Process the video using extension-optimized endpoint
            const response = await fetch(`${API_BASE_URL}/extension/process-video`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ video_url: videoUrl })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            this.onVideoProcessed(result);

        } catch (error) {
            console.error('Error processing video:', error);
            this.showError('Failed to process video. Please check if the server is running.');
        } finally {
            this.hideLoading();
        }
    }

    async fetchVideoInfo(videoId) {
        // This would typically call YouTube API, but for demo we'll use placeholder
        return {
            title: 'Video Title',
            channel: 'Channel Name',
            thumbnail: `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`
        };
    }

    displayVideoInfo(videoInfo) {
        this.elements.videoThumbnail.src = videoInfo.thumbnail;
        this.elements.videoTitle.textContent = videoInfo.title;
        this.elements.videoChannel.textContent = videoInfo.channel;
        this.elements.processingStatus.textContent = 'Processing...';
        this.elements.processingStatus.className = 'status';
        this.elements.videoInfo.classList.remove('hidden');
    }

    onVideoProcessed(result) {
        this.elements.processingStatus.textContent = 'Ready';
        this.elements.processingStatus.className = 'status success';
        this.elements.urlInput.style.display = 'none';
        this.elements.chatSection.classList.remove('hidden');
        this.elements.questionInput.focus();
    }

    async sendQuestion() {
        const question = this.elements.questionInput.value.trim();
        if (!question || !this.currentVideoId || this.isProcessing) return;

        this.isProcessing = true;
        this.addMessage(question, 'user');
        this.elements.questionInput.value = '';
        this.elements.sendQuestionBtn.disabled = true;

        try {
            const response = await fetch(`${API_BASE_URL}/extension/ask-question`, {
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
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            this.addMessage(result.answer, 'ai');

        } catch (error) {
            console.error('Error asking question:', error);
            this.addMessage('Sorry, I encountered an error while processing your question. Please try again.', 'ai');
        } finally {
            this.isProcessing = false;
            this.elements.sendQuestionBtn.disabled = false;
        }
    }

    addMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(contentDiv);
        this.elements.chatContainer.appendChild(messageDiv);
        
        // Remove welcome message if exists
        const welcomeMessage = this.elements.chatContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        // Scroll to bottom
        this.elements.chatContainer.scrollTop = this.elements.chatContainer.scrollHeight;
    }

    showLoading(message = 'Loading...') {
        this.elements.loading.querySelector('p').textContent = message;
        this.elements.loading.classList.remove('hidden');
    }

    hideLoading() {
        this.elements.loading.classList.add('hidden');
    }

    showError(message) {
        this.elements.errorMessage.textContent = message;
        this.elements.error.classList.remove('hidden');
    }

    hideError() {
        this.elements.error.classList.add('hidden');
    }
}

// Initialize the assistant when the popup loads
document.addEventListener('DOMContentLoaded', () => {
    new YouTubeAIAssistant();
});
