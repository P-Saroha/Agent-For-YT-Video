/**
 * AI Content Analysis Frontend
 * 
 * This JavaScript file handles:
 * 1. User interface interactions
 * 2. API calls to the backend
 * 3. Response display with markdown formatting
 */

// ==================== Configuration ====================
// Setup markdown rendering with clear formatting
marked.setOptions({
    breaks: true,      // Convert line breaks to <br>
    gfm: true,         // GitHub Flavored Markdown
});

// ==================== UI Helper Functions ====================

/**
 * Switch between different analysis modes (YouTube, Web, PDF, Text)
 * @param {string} mode - The mode to switch to
 */
function switchMode(mode) {
    // Remove active class from all buttons
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Add active class to clicked button
    event.target.classList.add('active');
    
    // Hide all sections
    document.querySelectorAll('.form-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Show selected section
    document.getElementById(mode + '-section').classList.add('active');
    
    // Clear previous results
    document.getElementById('result').innerHTML = '';
}

/**
 * Set YouTube URL from example
 * @param {string} url - YouTube URL
 */
function setYouTubeUrl(url) {
    document.getElementById('youtube-url').value = url;
}

/**
 * Set web URL from example
 * @param {string} url - Website URL
 */
function setWebUrl(url) {
    document.getElementById('web-url').value = url;
}

/**
 * Toggle the question field visibility for web content
 */
function toggleWebQuestion() {
    const action = document.getElementById('web-action').value;
    const questionGroup = document.getElementById('web-question-group');
    questionGroup.style.display = action === 'question' ? 'block' : 'none';
}

/**
 * Toggle the question field visibility for PDF
 */
function togglePDFQuestion() {
    const action = document.getElementById('pdf-action').value;
    const questionGroup = document.getElementById('pdf-question-group');
    questionGroup.style.display = action === 'question' ? 'block' : 'none';
}

/**
 * Toggle the question field visibility for text
 */
function toggleTextQuestion() {
    const action = document.getElementById('text-action').value;
    const questionGroup = document.getElementById('text-question-group');
    questionGroup.style.display = action === 'question' ? 'block' : 'none';
}

/**
 * Handle PDF file selection
 * @param {Event} event - File input change event
 */
function handlePDFSelection(event) {
    const file = event.target.files[0];
    if (file) {
        const fileInfo = document.getElementById('pdf-file-info');
        fileInfo.textContent = `Selected: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
        document.getElementById('pdf-submit-btn').disabled = false;
    }
}

/**
 * Validate text input (minimum characters)
 */
function validateTextInput() {
    const text = document.getElementById('text-content').value;
    const charCount = document.getElementById('text-char-count');
    charCount.textContent = `${text.length} characters`;
    document.getElementById('text-submit-btn').disabled = text.length < 100;
}

// ==================== Display Functions ====================

/**
 * Show loading state
 */
function showLoading() {
    document.getElementById('result').innerHTML = `
        <div class="result loading">
            <div class="spinner"></div>
            <p>⏳ Processing your request... Please wait</p>
        </div>
    `;
}

/**
 * Show error message
 * @param {string} message - Error message to display
 */
function showError(message) {
    document.getElementById('result').innerHTML = `
        <div class="result error">
            <h3>❌ Error</h3>
            <p>${message}</p>
        </div>
    `;
}

/**
 * Show AI response with markdown rendering
 * @param {string} response - The AI response text (may contain markdown)
 * @param {string} title - Title for the response
 * @param {Object} metadata - Additional metadata to display (optional)
 */
function showResponse(response, title, metadata = {}) {
    const resultDiv = document.getElementById('result');
    
    // Create result container
    let html = `<div class="result success"><h3>${title}</h3>`;
    
    // Add metadata if provided
    if (metadata.url) {
        html += `<p><strong>URL:</strong> ${metadata.url}</p>`;
    }
    if (metadata.question) {
        html += `<p><strong>Question:</strong> ${metadata.question}</p>`;
    }
    if (metadata.document) {
        html += `<p><strong>Document:</strong> ${metadata.document}</p>`;
    }
    
    // Render markdown response
    const htmlResponse = marked.parse(response);
    html += `<div class="ai-response">${htmlResponse}</div>`;
    
    // Add processing time if available
    if (metadata.time) {
        html += `<p class="processing-time">⏱️ Processing time: ${metadata.time}</p>`;
    }
    
    html += '</div>';
    resultDiv.innerHTML = html;
}

// ==================== API Calls ====================

/**
 * Call API endpoint and handle response
 * @param {string} endpoint - API endpoint path
 * @param {Object} data - Request data
 * @returns {Promise<Object>} - API response
 */
async function callAPI(endpoint, data) {
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || `API Error: ${response.status}`);
        }

        return result;
    } catch (error) {
        throw new Error(`API Call Failed: ${error.message}`);
    }
}

// ==================== YouTube Processing ====================

/**
 * Process YouTube video
 */
async function processYouTube() {
    const url = document.getElementById('youtube-url').value.trim();
    const question = document.getElementById('youtube-question').value.trim();

    // Validate input
    if (!url) {
        showError('❌ Please enter a YouTube URL');
        return;
    }

    showLoading();

    try {
        let result;
        
        if (question) {
            // If question provided, ask about video
            result = await callAPI('/youtube/simple/ask', {
                video_url: url,
                question: question
            });
        } else {
            // Otherwise, get summary
            result = await callAPI('/youtube/simple/summarize', {
                video_url: url
            });
        }

        // Display response
        const title = question ? '📺 YouTube Video Analysis' : '📺 YouTube Video Summary';
        const response = result.summary || result.answer || 'No response';
        
        showResponse(response, title, {
            url: url,
            question: question || undefined,
            time: result.processing_time || 'Unknown'
        });

    } catch (error) {
        showError(`❌ ${error.message}`);
    }
}

// ==================== Website Processing ====================

/**
 * Process website
 */
async function processWebsite() {
    const url = document.getElementById('web-url').value.trim();
    const action = document.getElementById('web-action').value;
    const question = document.getElementById('web-question').value.trim();

    // Validate input
    if (!url) {
        showError('❌ Please enter a website URL');
        return;
    }

    if (action === 'question' && !question) {
        showError('❌ Please enter a question');
        return;
    }

    showLoading();

    try {
        let result;
        
        if (action === 'question') {
            // Ask question about website
            result = await callAPI('/web/ask-question', {
                url: url,
                question: question
            });
        } else {
            // Summarize website
            result = await callAPI('/web/summarize', {
                url: url
            });
        }

        // Display response
        const title = action === 'question' ? '🌐 Website Analysis' : '🌐 Website Summary';
        const response = result.summary || result.answer || 'No response';
        
        showResponse(response, title, {
            url: url,
            question: question || undefined,
            time: result.processing_time || 'Unknown'
        });

    } catch (error) {
        showError(`❌ ${error.message}`);
    }
}

// ==================== PDF Processing ====================

/**
 * Process PDF document
 */
async function processPDF() {
    const file = document.getElementById('pdf-file').files[0];
    const action = document.getElementById('pdf-action').value;

    // Validate input
    if (!file) {
        showError('❌ Please select a PDF file');
        return;
    }

    showError('❌ PDF upload feature coming soon! Use the Text mode to paste text from your PDF instead.');
}

// ==================== Text Processing ====================

/**
 * Process plain text
 */
async function processText() {
    const content = document.getElementById('text-content').value.trim();
    const title = document.getElementById('text-title').value.trim();
    const action = document.getElementById('text-action').value;
    const question = document.getElementById('text-question').value.trim();

    // Validate input
    if (content.length < 100) {
        showError('❌ Please enter at least 100 characters');
        return;
    }

    if (action === 'question' && !question) {
        showError('❌ Please enter a question');
        return;
    }

    showLoading();

    try {
        let result;
        
        if (action === 'question') {
            // Ask question about text
            result = await callAPI('/documents/text/ask', {
                text_content: content,
                question: question,
                doc_title: title
            });
        } else {
            // Summarize text
            result = await callAPI('/documents/text/summarize', {
                text_content: content,
                doc_title: title
            });
        }

        // Display response
        const responseTitle = action === 'question' ? '📝 Text Analysis' : '📝 Text Summary';
        const response = result.summary || result.answer || 'No response';
        
        showResponse(response, responseTitle, {
            document: title,
            question: question || undefined,
            time: result.processing_time || 'Unknown'
        });

    } catch (error) {
        showError(`❌ ${error.message}`);
    }
}

// ==================== Utility Functions ====================

/**
 * Copy shareable link to clipboard
 */
function copyYouTubeLink() {
    const url = document.getElementById('youtube-url').value.trim();
    if (!url) {
        alert('Please enter a YouTube URL first');
        return;
    }
    navigator.clipboard.writeText(url);
    alert('✅ URL copied to clipboard!');
}

/**
 * Copy web URL to clipboard
 */
function copyWebLink() {
    const url = document.getElementById('web-url').value.trim();
    if (!url) {
        alert('Please enter a website URL first');
        return;
    }
    navigator.clipboard.writeText(url);
    alert('✅ URL copied to clipboard!');
}

// ==================== Initialize on Page Load ====================
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ AI Content Analysis Frontend loaded');
    // Validate text input on page load
    validateTextInput();
});
