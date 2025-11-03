/* YouTube + Web AI Assistant JavaScript */

// Advanced Marked.js Configuration for AI Responses
marked.setOptions({
    breaks: true,           // Convert \n to <br>
    gfm: true,             // GitHub Flavored Markdown
    sanitize: false,       // Allow HTML (we trust our AI)
    smartLists: true,      // Better list handling
    smartypants: true,     // Smart quotes and dashes
    headerIds: true,       // Add IDs to headers for navigation
    mangle: false          // Don't mangle email addresses
});

// Custom renderer for enhanced formatting
const renderer = new marked.Renderer();

// Enhance header rendering with better styling
renderer.heading = function(text, level) {
    const cleanText = text.trim();
    const id = cleanText.toLowerCase()
        .replace(/[^\w\s-]/g, '') // Remove special chars except hyphens
        .replace(/\s+/g, '-');    // Replace spaces with hyphens
        
    return `<h${level} id="${id}" class="ai-header level-${level}">${cleanText}</h${level}>`;
};

// Enhance paragraph rendering
renderer.paragraph = function(text) {
    return `<p class="ai-paragraph">${text.trim()}</p>`;
};

// Enhance list rendering
renderer.list = function(body, ordered) {
    const tag = ordered ? 'ol' : 'ul';
    return `<${tag} class="ai-list ai-${tag}">${body}</${tag}>`;
};

// Apply custom renderer
marked.use({ renderer });

// Minimal text preprocessing function
function preprocessAIText(text) {
    if (!text) return '';
    return text.trim();
}

// Render AI response with markdown formatting
function renderAIResponseWithAnimation(aiText, containerId) {
    const processedContent = preprocessAIText(aiText);
    const container = document.getElementById(containerId);
    if (container) {
        // Use marked.parse to convert markdown to HTML
        const htmlContent = marked.parse(processedContent);
        container.innerHTML = `<div class="ai-response" style="color: #ffffff; line-height: 1.8;">${htmlContent}</div>`;
    }
}

// Enhanced function for web content extraction that properly handles markdown
// Render web content with markdown formatting
function renderWebContent(content, containerId) {
    if (!content) return;
    
    const processedContent = preprocessAIText(content);
    const container = document.getElementById(containerId);
    if (container) {
        // Use marked.parse to convert markdown to HTML
        const htmlContent = marked.parse(processedContent);
        container.innerHTML = `<div class="ai-response" style="color: #ffffff; line-height: 1.8;">${htmlContent}</div>`;
    }
}

// Render RAG responses with markdown formatting
function renderRAGResponse(aiText, containerId) {
    if (!aiText) return;
    
    // Process and convert markdown to HTML
    let processedContent = preprocessAIText(aiText);
    
    // Update container with parsed markdown
    const container = document.getElementById(containerId);
    if (container) {
        // Use marked.parse to convert markdown to HTML
        const htmlContent = marked.parse(processedContent);
        container.innerHTML = `<div class="ai-response" style="color: #ffffff; line-height: 1.8;">${htmlContent}</div>`;
    }
}

// UI Functions
function switchMode(mode) {
    // Update buttons
    document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Show/hide sections
    document.querySelectorAll('.form-section').forEach(section => section.classList.remove('active'));
    document.getElementById(mode + '-section').classList.add('active');
    
    // Clear results
    document.getElementById('result').innerHTML = '';
}

function setYouTubeUrl(url) {
    document.getElementById('youtube-url').value = url;
}

function setWebUrl(url) {
    document.getElementById('web-url').value = url;
}

function toggleWebQuestion() {
    const action = document.getElementById('web-action').value;
    const questionGroup = document.getElementById('web-question-group');
    questionGroup.style.display = action === 'question' ? 'block' : 'none';
}

function showLoading() {
    document.getElementById('result').innerHTML = `<div class="result loading"><div class="spinner"></div><p>Analyzing content... Please wait</p></div>`;
}

function showError(message) {
    document.getElementById('result').innerHTML = `<div class="result error"><h3>Error</h3><p>${message}</p></div>`;
}

function showSuccess(content) {
    document.getElementById('result').innerHTML = `<div class="result success">${content}</div>`;
}

// YouTube Processing
async function processYouTube() {
    const url = document.getElementById('youtube-url').value.trim();
    const question = document.getElementById('youtube-question').value.trim();

    if (!url) {
        showError('Please enter a YouTube URL');
        return;
    }

    showLoading();

    try {
        const endpoint = question ? '/ask' : '/summarize';
        const body = question ? { video_url: url, question: question } : { video_url: url };

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body)
        });

        const data = await response.json();

        if (response.ok) {
            const title = question ? 'YouTube Video Analysis' : 'YouTube Video Summary';
            const responseText = data.summary || data.answer || 'No response received';
            
            // Use enhanced rendering with animations
            const resultDiv = document.createElement('div');
            resultDiv.className = 'result success';
            
            const titleEl = document.createElement('h3');
            titleEl.textContent = title;
            resultDiv.appendChild(titleEl);
            
            // Create container for AI response
            const responseContainer = document.createElement('div');
            responseContainer.id = 'youtube-response-' + Date.now();
            resultDiv.appendChild(responseContainer);
            
            const sectionDiv = document.createElement('div');
            sectionDiv.className = 'response-section';
            
            const videoP = document.createElement('p');
            videoP.innerHTML = `<strong>Video:</strong> ${url}`;
            sectionDiv.appendChild(videoP);
            
            if (question) {
                const questionP = document.createElement('p');
                questionP.innerHTML = `<strong>Question:</strong> ${question}`;
                sectionDiv.appendChild(questionP);
            }
            
            const responseH4 = document.createElement('h4');
            responseH4.textContent = 'AI Response:';
            sectionDiv.appendChild(responseH4);
            
            const responseDiv = document.createElement('div');
            responseDiv.className = 'ai-response';
            responseDiv.id = responseContainer.id + '-content';
            sectionDiv.appendChild(responseDiv);
            
            resultDiv.appendChild(sectionDiv);
            
            document.getElementById('result').innerHTML = '';
            document.getElementById('result').appendChild(resultDiv);
            
            // Use enhanced rendering with animations
            renderAIResponseWithAnimation(responseText.trim(), responseDiv.id);
        } else {
            showError(`YouTube processing failed: ${data.detail || 'Unknown error'}`);
        }
    } catch (error) {
        showError(`Network error: ${error.message}`);
    }
}

// Website Processing
async function processWebsite() {
    const url = document.getElementById('web-url').value.trim();
    const action = document.getElementById('web-action').value;
    const question = document.getElementById('web-question').value.trim();

    if (!url) {
        showError('Please enter a website URL');
        return;
    }

    if (action === 'question' && !question) {
        showError('Please enter a question');
        return;
    }

    showLoading();

    try {
        if (action === 'extract') {
            const response = await fetch('/web/extract-content', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            });

            const data = await response.json();

            if (response.ok) {
                // Debug: Log the actual response data
                console.log('WEB SCRAPING RESPONSE:', data);
                console.log('RESPONSE CONTENT LENGTH:', data.content ? data.content.length : 'NO CONTENT');
                console.log('RESPONSE CONTENT_PREVIEW LENGTH:', data.content_preview ? data.content_preview.length : 'NO PREVIEW');
                
                // Build clean HTML content using DOM methods
                const resultDiv = document.createElement('div');
                resultDiv.className = 'result success';
                
                const titleEl = document.createElement('h3');
                titleEl.textContent = 'Website Content Extracted';
                resultDiv.appendChild(titleEl);
                
                const sectionDiv = document.createElement('div');
                sectionDiv.className = 'response-section';
                
                const urlP = document.createElement('p');
                urlP.innerHTML = `<strong>URL:</strong> ${url}`;
                sectionDiv.appendChild(urlP);
                
                const titleP = document.createElement('p');
                titleP.innerHTML = `<strong>Title:</strong> ${data.title || 'No title'}`;
                sectionDiv.appendChild(titleP);
                
                const lengthP = document.createElement('p');
                lengthP.innerHTML = `<strong>Length:</strong> ${data.char_count || (data.content_preview ? data.content_preview.length : 0)} characters`;
                sectionDiv.appendChild(lengthP);
                
                const wordsP = document.createElement('p');
                wordsP.innerHTML = `<strong>Words:</strong> ${data.word_count || 0} words`;
                sectionDiv.appendChild(wordsP);
                
                // Determine content type icon
                let contentType = '📄';
                const domain = url.toLowerCase();
                if (domain.includes('wikipedia')) contentType = '📚';
                else if (domain.includes('reddit')) contentType = '💬';
                else if (domain.includes('github')) contentType = '💻';
                else if (domain.includes('youtube')) contentType = '📺';
                else if (domain.includes('news') || domain.includes('bbc') || domain.includes('cnn')) contentType = '📰';

                const previewH4 = document.createElement('h4');
                previewH4.textContent = `${contentType} AI Summary:`;
                sectionDiv.appendChild(previewH4);
                
                // Add metadata
                const metadataP = document.createElement('p');
                metadataP.style.fontSize = '12px';
                metadataP.style.opacity = '0.7';
                metadataP.style.margin = '5px 0';
                metadataP.textContent = `Source: ${new URL(url).hostname}`;
                sectionDiv.appendChild(metadataP);
                
                const previewDiv = document.createElement('div');
                previewDiv.className = 'ai-response';
                previewDiv.style.maxHeight = '80vh'; // Use viewport height for better scrolling
                previewDiv.style.overflowY = 'auto';
                previewDiv.style.fontSize = '14px';
                previewDiv.style.lineHeight = '1.6';
                previewDiv.id = 'web-content-' + Date.now();
                
                sectionDiv.appendChild(previewDiv);
                
                // Better content formatting using the new rendering function
                let content = data.content || data.content_preview || 'No content extracted';
                
                // If content is very short, show a helpful message
                if (content.length < 100) {
                    const domain = new URL(url).hostname;
                    content = `⚠️ Limited content extracted (${content.length} characters).\n\n` +
                             `This may be because ${domain} uses JavaScript to load content dynamically.\n\n` +
                             `For better results, try:\n` +
                             `• Wikipedia articles\n` +
                             `• BBC News articles\n` +
                             `• Documentation pages\n` +
                             `• Static blog posts\n\n` +
                             `Extracted content:\n${content}`;
                }
                
                resultDiv.appendChild(sectionDiv);
                
                document.getElementById('result').innerHTML = '';
                document.getElementById('result').appendChild(resultDiv);
                
                // Use the enhanced web content rendering function
                renderWebContent(content, previewDiv.id);
                
                // Add content length info
                const lengthInfo = document.createElement('p');
                lengthInfo.style.fontSize = '11px';
                lengthInfo.style.opacity = '0.6';
                lengthInfo.style.marginTop = '10px';
                lengthInfo.style.textAlign = 'right';
                lengthInfo.textContent = `${content.length} characters extracted`;
                sectionDiv.appendChild(lengthInfo);
                
                resultDiv.appendChild(sectionDiv);
                
                document.getElementById('result').innerHTML = '';
                document.getElementById('result').appendChild(resultDiv);
            } else {
                showError(`Website extraction failed: ${data.detail || 'Unknown error'}`);
            }
        } else {
            const response = await fetch('/web/ask-question', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    url: url,
                    question: question
                })
            });

            const data = await response.json();

            if (response.ok) {
                const responseText = data.answer || 'No response received';
                
                // Build clean HTML content
                const resultDiv = document.createElement('div');
                resultDiv.className = 'result success';
                
                const titleEl = document.createElement('h3');
                titleEl.textContent = 'Website Analysis Complete';
                resultDiv.appendChild(titleEl);
                
                const sectionDiv = document.createElement('div');
                sectionDiv.className = 'response-section';
                
                const websiteP = document.createElement('p');
                websiteP.innerHTML = `<strong>Website:</strong> ${url}`;
                sectionDiv.appendChild(websiteP);
                
                const questionP = document.createElement('p');
                questionP.innerHTML = `<strong>Question:</strong> ${question}`;
                sectionDiv.appendChild(questionP);
                
                const responseH4 = document.createElement('h4');
                responseH4.textContent = 'AI Response:';
                sectionDiv.appendChild(responseH4);
                
                const responseDiv = document.createElement('div');
                responseDiv.className = 'ai-response';
                responseDiv.id = 'website-response-' + Date.now();
                sectionDiv.appendChild(responseDiv);
                
                resultDiv.appendChild(sectionDiv);
                
                document.getElementById('result').innerHTML = '';
                document.getElementById('result').appendChild(resultDiv);
                
                // Use enhanced rendering with animations and RAG response processing
                renderRAGResponse(responseText.trim(), responseDiv.id);
            } else {
                showError(`Website analysis failed: ${data.detail || 'Unknown error'}`);
            }
        }
    } catch (error) {
        showError(`Network error: ${error.message}`);
    }
}

// Auto-fill URL from parameters on page load
window.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const youtubeUrl = urlParams.get('youtube');
    const webUrl = urlParams.get('website') || urlParams.get('url');
    const question = urlParams.get('question') || urlParams.get('q');
    
    if (youtubeUrl) {
        // Switch to YouTube mode and fill URL
        switchModeByName('youtube');
        document.getElementById('youtube-url').value = youtubeUrl;
        if (question) {
            document.getElementById('youtube-question').value = question;
        }
    } else if (webUrl) {
        // Switch to website mode and fill URL
        switchModeByName('web');
        document.getElementById('web-url').value = webUrl;
        if (question) {
            document.getElementById('web-action').value = 'question';
            toggleWebQuestion();
            document.getElementById('web-question').value = question;
        }
    }
});

function switchModeByName(mode) {
    // Update buttons
    document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
    if (mode === 'youtube') {
        document.querySelector('.mode-btn[onclick*="youtube"]').classList.add('active');
    } else {
        document.querySelector('.mode-btn[onclick*="web"]').classList.add('active');
    }
    
    // Show/hide sections
    document.querySelectorAll('.form-section').forEach(section => section.classList.remove('active'));
    document.getElementById(mode + '-section').classList.add('active');
}

// Function to generate shareable URLs
function copyYouTubeLink() {
    const url = document.getElementById('youtube-url').value.trim();
    const question = document.getElementById('youtube-question').value.trim();
    if (!url) {
        alert('Please enter a YouTube URL first');
        return;
    }
    
    let shareUrl = `${window.location.origin}${window.location.pathname}?youtube=${encodeURIComponent(url)}`;
    if (question) {
        shareUrl += `&question=${encodeURIComponent(question)}`;
    }
    
    navigator.clipboard.writeText(shareUrl).then(() => {
        alert('Link copied to clipboard! Share this link to open the app with your URL pre-filled.');
    });
}

function copyWebLink() {
    const url = document.getElementById('web-url').value.trim();
    const question = document.getElementById('web-question').value.trim();
    if (!url) {
        alert('Please enter a website URL first');
        return;
    }
    
    let shareUrl = `${window.location.origin}${window.location.pathname}?website=${encodeURIComponent(url)}`;
    if (question && document.getElementById('web-action').value === 'question') {
        shareUrl += `&question=${encodeURIComponent(question)}`;
    }
    
    navigator.clipboard.writeText(shareUrl).then(() => {
        alert('Link copied to clipboard! Share this link to open the app with your URL pre-filled.');
    });
}

// Force title visibility with sharp white color
function fixTitleVisibility() {
    const title = document.querySelector('h1');
    if (title) {
        title.style.color = '#ffffff';
        title.style.textShadow = 'none';
        title.style.background = 'none';
        title.style.webkitBackgroundClip = 'initial';
        title.style.webkitTextFillColor = 'initial';
        title.style.backgroundClip = 'initial';
    }
}

// Apply title fix when page loads and periodically
document.addEventListener('DOMContentLoaded', fixTitleVisibility);
window.addEventListener('load', fixTitleVisibility);
setInterval(fixTitleVisibility, 1000); // Force every second to override any conflicts

// =============================================================================
// PDF AND TEXT DOCUMENT PROCESSING FUNCTIONS
// =============================================================================

// Global variable to store selected PDF file
let selectedPDFFile = null;

// Handle PDF file selection
function handlePDFSelection(event) {
    const file = event.target.files[0];
    if (file) {
        selectedPDFFile = file;
        document.getElementById('pdf-file-info').textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(2)} KB)`;
        document.getElementById('pdf-submit-btn').disabled = false;
    }
}

// Toggle PDF question visibility
function togglePDFQuestion() {
    const action = document.getElementById('pdf-action').value;
    const questionGroup = document.getElementById('pdf-question-group');
    questionGroup.style.display = action === 'question' ? 'block' : 'none';
}

// Process PDF document
async function processPDF() {
    if (!selectedPDFFile) {
        showError('Please select a PDF file first');
        return;
    }

    const action = document.getElementById('pdf-action').value;
    const question = document.getElementById('pdf-question').value.trim();

    if (action === 'question' && !question) {
        showError('Please enter a question');
        return;
    }

    showLoading();

    try {
        const formData = new FormData();
        formData.append('file', selectedPDFFile);

        let endpoint = '/document/pdf/summarize';
        if (action === 'question') {
            formData.append('question', question);
            endpoint = '/document/pdf/ask-question';
        }

        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            const title = action === 'question' ? 'PDF Analysis - Question Answered' : 'PDF Summary';
            
            const resultDiv = document.createElement('div');
            resultDiv.className = 'result success';
            
            const titleEl = document.createElement('h3');
            titleEl.textContent = title;
            resultDiv.appendChild(titleEl);
            
            const responseContainer = document.createElement('div');
            responseContainer.id = 'pdf-response-' + Date.now();
            resultDiv.appendChild(responseContainer);
            
            const sectionDiv = document.createElement('div');
            sectionDiv.className = 'response-section';
            
            const fileP = document.createElement('p');
            fileP.innerHTML = `<strong>File:</strong> ${selectedPDFFile.name}`;
            sectionDiv.appendChild(fileP);
            
            const docTitleP = document.createElement('p');
            docTitleP.innerHTML = `<strong>Document:</strong> ${data.document_title}`;
            sectionDiv.appendChild(docTitleP);
            
            const statsP = document.createElement('p');
            statsP.innerHTML = `<strong>Processed:</strong> ${data.chunks_count} chunks, ${data.char_count} characters`;
            sectionDiv.appendChild(statsP);
            
            if (action === 'question') {
                const questionP = document.createElement('p');
                questionP.innerHTML = `<strong>Question:</strong> ${question}`;
                sectionDiv.appendChild(questionP);
            }
            
            const responseH4 = document.createElement('h4');
            responseH4.textContent = 'AI Response:';
            sectionDiv.appendChild(responseH4);
            
            const responseDiv = document.createElement('div');
            responseDiv.className = 'ai-response';
            responseDiv.id = responseContainer.id + '-content';
            sectionDiv.appendChild(responseDiv);
            
            resultDiv.appendChild(sectionDiv);
            
            document.getElementById('result').innerHTML = '';
            document.getElementById('result').appendChild(resultDiv);
            
            renderRAGResponse(data.answer, responseDiv.id);
        } else {
            showError(`PDF processing failed: ${data.detail || 'Unknown error'}`);
        }
    } catch (error) {
        showError(`Network error: ${error.message}`);
    }
}

// Validate text input and update character count
function validateTextInput() {
    const textContent = document.getElementById('text-content').value;
    const charCount = textContent.length;
    const charCountEl = document.getElementById('text-char-count');
    const submitBtn = document.getElementById('text-submit-btn');
    
    charCountEl.textContent = `${charCount} characters`;
    
    if (charCount >= 100) {
        charCountEl.style.color = '#4CAF50';
        submitBtn.disabled = false;
    } else {
        charCountEl.style.color = '#ff6b6b';
        submitBtn.disabled = true;
    }
}

// Toggle text question visibility
function toggleTextQuestion() {
    const action = document.getElementById('text-action').value;
    const questionGroup = document.getElementById('text-question-group');
    questionGroup.style.display = action === 'question' ? 'block' : 'none';
}

// Process text document
async function processText() {
    const textContent = document.getElementById('text-content').value.trim();
    const textTitle = document.getElementById('text-title').value.trim() || 'My Document';
    const action = document.getElementById('text-action').value;
    const question = document.getElementById('text-question').value.trim();

    if (!textContent || textContent.length < 100) {
        showError('Please enter at least 100 characters of text');
        return;
    }

    if (action === 'question' && !question) {
        showError('Please enter a question');
        return;
    }

    showLoading();

    try {
        let endpoint = '/document/text/summarize';
        let body = {
            text_content: textContent,
            document_title: textTitle
        };

        if (action === 'question') {
            endpoint = '/document/text/ask-question';
            body.question = question;
        }

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body)
        });

        const data = await response.json();

        if (response.ok) {
            const title = action === 'question' ? 'Text Analysis - Question Answered' : 'Text Summary';
            
            const resultDiv = document.createElement('div');
            resultDiv.className = 'result success';
            
            const titleEl = document.createElement('h3');
            titleEl.textContent = title;
            resultDiv.appendChild(titleEl);
            
            const responseContainer = document.createElement('div');
            responseContainer.id = 'text-response-' + Date.now();
            resultDiv.appendChild(responseContainer);
            
            const sectionDiv = document.createElement('div');
            sectionDiv.className = 'response-section';
            
            const docTitleP = document.createElement('p');
            docTitleP.innerHTML = `<strong>Document:</strong> ${data.document_title}`;
            sectionDiv.appendChild(docTitleP);
            
            const statsP = document.createElement('p');
            statsP.innerHTML = `<strong>Processed:</strong> ${data.chunks_count} chunks, ${data.char_count} characters`;
            sectionDiv.appendChild(statsP);
            
            if (action === 'question') {
                const questionP = document.createElement('p');
                questionP.innerHTML = `<strong>Question:</strong> ${question}`;
                sectionDiv.appendChild(questionP);
            }
            
            const responseH4 = document.createElement('h4');
            responseH4.textContent = 'AI Response:';
            sectionDiv.appendChild(responseH4);
            
            const responseDiv = document.createElement('div');
            responseDiv.className = 'ai-response';
            responseDiv.id = responseContainer.id + '-content';
            sectionDiv.appendChild(responseDiv);
            
            resultDiv.appendChild(sectionDiv);
            
            document.getElementById('result').innerHTML = '';
            document.getElementById('result').appendChild(resultDiv);
            
            renderRAGResponse(data.answer, responseDiv.id);
        } else {
            showError(`Text processing failed: ${data.detail || 'Unknown error'}`);
        }
    } catch (error) {
        showError(`Network error: ${error.message}`);
    }
}