// Background service worker
class BackgroundService {
    constructor() {
        this.init();
    }

    init() {
        // Listen for extension installation
        chrome.runtime.onInstalled.addListener(() => {
            console.log('YouTube AI Assistant installed');
        });

        // Listen for messages from content scripts and popup
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            this.handleMessage(request, sender, sendResponse);
            return true; // Keep message channel open for async responses
        });

        // Listen for tab updates (when user navigates to YouTube)
        chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
            if (changeInfo.status === 'complete' && tab.url && tab.url.includes('youtube.com/watch')) {
                this.handleYouTubeNavigation(tab);
            }
        });
    }

    async handleMessage(request, sender, sendResponse) {
        try {
            switch (request.action) {
                case 'videoChanged':
                    await this.onVideoChanged(request.videoId, request.url);
                    sendResponse({ success: true });
                    break;
                    
                case 'getCurrentTab':
                    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
                    sendResponse({ tab });
                    break;
                    
                case 'extractVideoInfo':
                    const videoInfo = await this.extractVideoInfo(request.videoId);
                    sendResponse({ videoInfo });
                    break;
                    
                default:
                    sendResponse({ error: 'Unknown action' });
            }
        } catch (error) {
            console.error('Background script error:', error);
            sendResponse({ error: error.message });
        }
    }

    async onVideoChanged(videoId, url) {
        // Store current video information
        await chrome.storage.local.set({
            currentVideo: {
                videoId,
                url,
                timestamp: Date.now()
            }
        });
    }

    async handleYouTubeNavigation(tab) {
        // Inject content script if needed
        try {
            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                files: ['content/content.js']
            });
        } catch (error) {
            console.log('Content script already injected or error:', error);
        }
    }

    async extractVideoInfo(videoId) {
        // This would typically make API calls to get video metadata
        // For now, return basic info
        return {
            videoId,
            thumbnail: `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`,
            title: 'Video Title', // Would be fetched from YouTube API
            channel: 'Channel Name' // Would be fetched from YouTube API
        };
    }
}

// Initialize background service
new BackgroundService();
