document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const fileList = document.getElementById('file-list');
    const chatHistory = document.getElementById('chat-history');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const loginModal = document.getElementById('login-modal');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const authToggleLink = document.getElementById('auth-toggle-link');
    const registerToggleLink = document.getElementById('register-toggle-link');
    const authTitle = document.getElementById('auth-title');
    const authError = document.getElementById('auth-error');

    // Use CONFIG from config.js
    const API_URL = CONFIG.API_BASE_URL;
    let accessToken = localStorage.getItem('access_token');

    // --- Auth Handling ---

    if (!accessToken) {
        loginModal.style.display = 'flex';
    }

    // Toggle between login and register forms
    authToggleLink.addEventListener('click', (e) => {
        e.preventDefault();
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
        authTitle.textContent = 'Register';
        authError.style.display = 'none';
    });

    registerToggleLink.addEventListener('click', (e) => {
        e.preventDefault();
        registerForm.style.display = 'none';
        loginForm.style.display = 'block';
        authTitle.textContent = 'Login';
        authError.style.display = 'none';
    });

    // Login form submission
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        authError.style.display = 'none';

        const formData = new FormData(loginForm);

        try {
            const response = await fetch(`${API_URL}/token`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Login failed');
            }

            const data = await response.json();
            accessToken = data.access_token;
            localStorage.setItem('access_token', accessToken);
            loginModal.style.display = 'none';
            loginForm.reset();

            // Welcome message
            addMessage('Welcome back! You can now upload documents and ask questions.', false);
        } catch (error) {
            authError.textContent = error.message;
            authError.style.display = 'block';
        }
    });

    // Register form submission
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        authError.style.display = 'none';

        const formData = {
            username: document.getElementById('reg-username').value,
            email: document.getElementById('reg-email').value,
            full_name: document.getElementById('reg-fullname').value,
            password: document.getElementById('reg-password').value
        };

        try {
            const response = await fetch(`${API_URL}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Registration failed');
            }

            // Auto-login after registration
            const loginFormData = new FormData();
            loginFormData.append('username', formData.username);
            loginFormData.append('password', formData.password);

            const loginResponse = await fetch(`${API_URL}/token`, {
                method: 'POST',
                body: loginFormData
            });

            if (!loginResponse.ok) {
                throw new Error('Registration successful but auto-login failed. Please login manually.');
            }

            const loginData = await loginResponse.json();
            accessToken = loginData.access_token;
            localStorage.setItem('access_token', accessToken);
            loginModal.style.display = 'none';
            registerForm.reset();

            // Welcome message
            addMessage(`Welcome ${formData.full_name}! Your account has been created. You can now upload documents and ask questions.`, false);
        } catch (error) {
            authError.textContent = error.message;
            authError.style.display = 'block';
        }
    });

    // --- File Upload Handling ---

    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--primary-color)';
        dropZone.style.background = '#eef2ff';
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--border-color)';
        dropZone.style.background = '#f9fafb';
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--border-color)';
        dropZone.style.background = '#f9fafb';
        handleFiles(e.dataTransfer.files);
    });

    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    function handleFiles(files) {
        Array.from(files).forEach(async file => {
            // Validate file type
            const validTypes = CONFIG.ALLOWED_FILE_TYPES;
            const fileExt = '.' + file.name.split('.').pop().toLowerCase();

            if (!validTypes.includes(fileExt)) {
                alert(`Invalid file type: ${file.name}. Only PDF and DOCX files are allowed.`);
                return;
            }

            // Validate file size
            if (file.size > CONFIG.MAX_FILE_SIZE) {
                alert(`File too large: ${file.name}. Maximum size is 10MB.`);
                return;
            }

            addFileToList(file);

            const formData = new FormData();
            formData.append('files', file);

            try {
                const response = await fetch(`${API_URL}/ingest`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${accessToken}`
                    },
                    body: formData
                });

                if (response.ok) {
                    updateFileStatus(file.name, 'Ingested');
                } else {
                    const error = await response.json();
                    updateFileStatus(file.name, 'Failed');
                    console.error('Upload error:', error);
                }
            } catch (error) {
                console.error('Upload error:', error);
                updateFileStatus(file.name, 'Error');
            }
        });
    }

    function addFileToList(file) {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.id = `file-${file.name.replace(/\s+/g, '-')}`;

        const iconClass = file.name.endsWith('.pdf') ? 'fa-file-pdf' : 'fa-file-word';

        fileItem.innerHTML = `
            <i class="fa-solid ${iconClass}"></i>
            <div class="file-info">
                <span class="file-name" title="${file.name}">${file.name}</span>
                <span class="file-status">Uploading...</span>
            </div>
            <i class="fa-solid fa-check-circle" style="color: #10b981; display: none;"></i>
        `;

        fileList.prepend(fileItem);
    }

    function updateFileStatus(fileName, status) {
        const safeName = fileName.replace(/\s+/g, '-');
        const item = document.getElementById(`file-${safeName}`);
        if (item) {
            const statusSpan = item.querySelector('.file-status');
            statusSpan.textContent = status;
            if (status === 'Ingested') {
                item.querySelector('.fa-check-circle').style.display = 'block';
            }
        }
    }

    // --- Chat Handling ---

    function addMessage(text, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;

        const avatarIcon = isUser ? 'fa-user' : 'fa-robot';

        messageDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid ${avatarIcon}"></i></div>
            <div class="content">${text}</div>
        `;

        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function showTypingIndicator() {
        const indicatorDiv = document.createElement('div');
        indicatorDiv.className = 'message ai-message typing-indicator-msg';
        indicatorDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="content">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        chatHistory.appendChild(indicatorDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        return indicatorDiv;
    }

    async function handleSend() {
        const text = userInput.value.trim();
        if (!text) return;

        // Add user message
        addMessage(text, true);
        userInput.value = '';
        userInput.style.height = 'auto'; // Reset height

        const typingIndicator = showTypingIndicator();

        try {
            const response = await fetch(`${API_URL}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${accessToken}`
                },
                body: JSON.stringify({ query: text })
            });

            typingIndicator.remove();

            if (response.ok) {
                const data = await response.json();
                addMessage(data.response);
            } else {
                const error = await response.json();
                addMessage(`Sorry, I encountered an error: ${error.detail || 'Unknown error'}`);
            }
        } catch (error) {
            typingIndicator.remove();
            console.error('Query error:', error);
            addMessage("Sorry, I couldn't reach the server. Please check your connection.");
        }
    }

    sendBtn.addEventListener('click', handleSend);

    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });

    // Auto-resize textarea
    userInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
});
