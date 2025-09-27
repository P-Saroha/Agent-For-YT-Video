// Configuration for different environments
const config = {
    development: {
        API_BASE_URL: 'http://localhost:8000'
    },
    production: {
        API_BASE_URL: 'https://your-deployed-app.com' // Update this with your actual domain
    }
};

// Auto-detect environment
const isDevelopment = chrome.runtime && chrome.runtime.getManifest().key === undefined;
const currentConfig = isDevelopment ? config.development : config.production;

// Export configuration
const API_BASE_URL = currentConfig.API_BASE_URL;