// Content script for YouTube pages
class YouTubeContentScript {
    constructor() {
        this.currentVideoId = null;
        this.init();
    }

    init() {
        // Listen for URL changes (YouTube uses pushState)
        this.observeUrlChanges();
        this.checkCurrentVideo();
        
        // Listen for messages from popup
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            if (request.action === 'getCurrentVideoId') {
                sendResponse({ videoId: this.currentVideoId });
            }
        });
    }

    observeUrlChanges() {
        let lastUrl = location.href;
        new MutationObserver(() => {
            const url = location.href;
            if (url !== lastUrl) {
                lastUrl = url;
                this.checkCurrentVideo();
            }
        }).observe(document, { subtree: true, childList: true });
    }

    checkCurrentVideo() {
        const urlParams = new URLSearchParams(window.location.search);
        const videoId = urlParams.get('v');
        
        if (videoId && videoId !== this.currentVideoId) {
            this.currentVideoId = videoId;
            this.onVideoChanged(videoId);
        }
    }

    onVideoChanged(videoId) {
        // Notify background script about video change
        chrome.runtime.sendMessage({
            action: 'videoChanged',
            videoId: videoId,
            url: window.location.href
        });
    }

    extractVideoMetadata() {
        const titleElement = document.querySelector('h1.title yt-formatted-string, h1.ytd-video-primary-info-renderer');
        const channelElement = document.querySelector('yt-formatted-string.ytd-channel-name a, .ytd-video-owner-renderer a');
        
        return {
            title: titleElement ? titleElement.textContent.trim() : 'Unknown Title',
            channel: channelElement ? channelElement.textContent.trim() : 'Unknown Channel',
            url: window.location.href,
            videoId: this.currentVideoId
        };
    }
}

// Initialize content script
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new YouTubeContentScript());
} else {
    new YouTubeContentScript();
}
