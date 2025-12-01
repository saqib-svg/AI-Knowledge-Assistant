// Configuration for API endpoints
// This allows the frontend to work in both local and Docker environments

const CONFIG = {
    // Check if we're running in Docker (nginx proxy) or local development
    API_BASE_URL: window.location.hostname === 'localhost' && window.location.port && window.location.port !== '80'
        ? 'http://localhost:8000'  // Local development with explicit port
        : window.location.origin,   // Docker/Production (nginx proxy on port 80)

    // Maximum file size (10MB)
    MAX_FILE_SIZE: 10 * 1024 * 1024,

    // Allowed file types
    ALLOWED_FILE_TYPES: ['.pdf', '.docx'],
};

// Freeze config to prevent modifications
Object.freeze(CONFIG);
