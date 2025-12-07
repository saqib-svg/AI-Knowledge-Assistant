// Ensure CONFIG is defined
window.CONFIG = window.CONFIG || { API_BASE_URL: 'http://localhost:8000' };
const API_URL = window.CONFIG.API_BASE_URL;

// Debug logging
console.log('API URL:', API_URL);

<<<<<<< Updated upstream
let accessToken = '';
let selectedChatId = '';
let currentMessages = [];
// =============================================
// AUTHENTICATION & SESSION MANAGEMENT
// =============================================

function initializeAuth() {
    console.log('Initializing auth...');
    accessToken = localStorage.getItem('access_token') || '';
    selectedChatId = localStorage.getItem('selected_chat_id') || '';

    if (!accessToken) {
        console.log('No access token found, redirecting to login...');
        window.location.href = '/login.html';
        return;
=======
    // Track uploaded documents with their IDs for filtering
    let uploadedDocs = JSON.parse(localStorage.getItem('uploaded_docs') || '[]');

    // --- Chat History Persistence ---

    function saveChatHistory() {
        const messages = [...chatHistory.querySelectorAll('.message:not(.typing-indicator-msg)')]
            .map(m => ({
                isUser: m.classList.contains('user-message'),
                text: m.querySelector('.content').innerHTML
            }));
        localStorage.setItem('chat_history', JSON.stringify(messages));
    }

    function loadChatHistory() {
        const saved = localStorage.getItem('chat_history');
        if (saved) {
            const messages = JSON.parse(saved);
            // Keep the initial welcome message, add saved messages
            messages.forEach(m => addMessage(m.text, m.isUser, false));
        }
    }

    function clearChatHistory() {
        // Remove all messages except the first welcome message
        const messages = chatHistory.querySelectorAll('.message');
        messages.forEach((msg, index) => {
            if (index > 0) msg.remove();
        });
        localStorage.removeItem('chat_history');
    }

    // --- Auth Handling ---

    if (!accessToken) {
        loginModal.style.display = 'flex';
    } else {
        // Load chat history if logged in
        loadChatHistory();
        loadUploadedDocs();
>>>>>>> Stashed changes
    }

    console.log('✓ Auth initialized. Token:', accessToken ? accessToken.substring(0, 20) + '...' : 'none');
}

function logout() {
    console.log('Logging out...');
    localStorage.removeItem('access_token');
    localStorage.removeItem('selected_chat_id');
    window.location.href = '/login.html';
}

// =============================================
// CHAT MANAGEMENT
// =============================================

async function loadChats() {
    console.log('Loading chats...');
    try {
        const response = await fetch(`${API_URL}/chats`, {
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            }
        });

<<<<<<< Updated upstream
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
=======
            const data = await response.json();
            accessToken = data.access_token;
            localStorage.setItem('access_token', accessToken);
            loginModal.style.display = 'none';
            loginForm.reset();

            // Load chat history after login
            loadChatHistory();
            loadUploadedDocs();

            // Welcome message
            addMessage('Welcome back! You can now upload documents and ask questions.', false);
        } catch (error) {
            authError.textContent = error.message;
            authError.style.display = 'block';
>>>>>>> Stashed changes
        }

        const chats = await response.json();
        renderChatList(chats);
    } catch (error) {
        console.error('Error loading chats:', error);
        // Don't alert on load, just log
    }
}

function renderChatList(chats) {
    const chatList = document.getElementById('chat-list');
    if (!chatList) return;

    if (!chats || chats.length === 0) {
        chatList.innerHTML = '<div style="padding: 15px; color: #999; font-size: 13px; text-align: center;">No chats yet</div>';
        return;
    }

    chatList.innerHTML = chats.map(chat => `
        <div class="chat-item ${chat.id == selectedChatId ? 'active' : ''}" 
             data-chat-id="${chat.id}" 
             onclick="selectChat('${chat.id}')">
            <div class="chat-item-content">
                <div class="chat-item-title">${escapeHtml(chat.title || 'Untitled Chat')}</div>
                <div class="chat-item-date">${new Date(chat.created_at).toLocaleDateString()}</div>
            </div>
            <button class="chat-delete-btn" onclick="deleteChat(event, '${chat.id}')" title="Delete chat">
                <i class="fa-solid fa-trash"></i>
            </button>
        </div>
    `).join('');
}

function selectChat(chatId) {
    console.log('Selecting chat:', chatId);
    selectedChatId = chatId;
    localStorage.setItem('selected_chat_id', chatId);

    // Update UI
    document.querySelectorAll('.chat-item').forEach(item => {
        item.classList.toggle('active', item.dataset.chatId == chatId);
    });

    // Show chat interface
    updateChatDisplay();

    // Update header title
    const chatTitleDisplay = document.getElementById('chat-title-display');
    const chatItem = document.querySelector(`.chat-item[data-chat-id="${chatId}"] .chat-item-title`);
    if (chatTitleDisplay && chatItem) {
        chatTitleDisplay.textContent = chatItem.textContent;
    }

    // Load messages and documents for this chat
    loadMessages();
    loadDocuments();
}

async function createChat() {
    const titleInput = document.getElementById('new-chat-title');
    const title = titleInput ? titleInput.value.trim() : 'New Chat';

    if (!title) return;

    try {
        const response = await fetch(`${API_URL}/chats`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const newChat = await response.json();

<<<<<<< Updated upstream
        // Clear the input
        if (titleInput) titleInput.value = '';
=======
    // Prevent double-click issue: only trigger fileInput from dropZone if not clicking the button
    dropZone.addEventListener('click', (e) => {
        // Don't trigger if clicking the button (button has its own onclick)
        if (e.target.tagName !== 'BUTTON' && !e.target.closest('button')) {
            fileInput.click();
        }
    });
>>>>>>> Stashed changes

        // Reload chats
        await loadChats();

        // Select the new chat
        selectChat(newChat.id);

    } catch (error) {
        console.error('Error creating chat:', error);
        alert('Failed to create chat. Please try again.');
    }
}

<<<<<<< Updated upstream
async function deleteChat(event, chatId) {
    event.stopPropagation();
=======
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
        // Reset file input to allow uploading the same file again
        fileInput.value = '';
    });
>>>>>>> Stashed changes

    if (!confirm('Are you sure you want to delete this chat? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/chats/${chatId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // If the deleted chat was selected, clear the selection
        if (selectedChatId == chatId) {
            selectedChatId = '';
            localStorage.removeItem('selected_chat_id');
            updateChatDisplay();
        }

        // Reload chats
        await loadChats();

    } catch (error) {
        console.error('Error deleting chat:', error);
        alert('Failed to delete chat. Please try again.');
    }
}

// =============================================
// MESSAGE & DOCUMENT MANAGEMENT
// =============================================

async function loadMessages() {
    if (!selectedChatId) return;

    try {
        const response = await fetch(`${API_URL}/chats/${selectedChatId}/messages`, {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        currentMessages = await response.json();
        renderMessages();

    } catch (error) {
        console.error('Error loading messages:', error);
    }
}

<<<<<<< Updated upstream
function renderMessages() {
    const messagesContainer = document.getElementById('messages');
    if (!messagesContainer) return;

    messagesContainer.innerHTML = currentMessages.map(msg => `
        <div class="message ${msg.sender === 'user' ? 'message-user' : 'message-assistant'}">
            <div class="message-content">
                ${msg.content} <!-- Content is already HTML safe or needs sanitization if markdown -->
            </div>
        </div>
    `).join('');

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

async function sendMessage() {
    const messageInput = document.getElementById('message-input');
    if (!messageInput || !messageInput.value.trim()) return;

    const message = messageInput.value.trim();
    messageInput.value = '';

    // Optimistic UI update
    const tempId = Date.now();
    currentMessages.push({ id: tempId, sender: 'user', content: escapeHtml(message) });
    renderMessages();

    // Show loading state
    const messagesContainer = document.getElementById('messages');
    const typingIndicatorId = 'typing-indicator-' + Date.now();
    const typingIndicatorHtml = `
        <div id="${typingIndicatorId}" class="message message-assistant typing-indicator">
            <div class="message-content">
                <div class="typing-dots">
                    <span></span><span></span><span></span>
                </div>
            </div>
        </div>
    `;
    messagesContainer.insertAdjacentHTML('beforeend', typingIndicatorHtml);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    try {
        const response = await fetch(`${API_URL}/chats/${selectedChatId}/messages`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content: message })
        });

        // Remove typing indicator
        const indicatorElement = document.getElementById(typingIndicatorId);
        if (indicatorElement) indicatorElement.remove();

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        // Remove optimistic message and replace with real ones
        currentMessages = currentMessages.filter(m => m.id !== tempId);

        if (result.user_message) {
            result.user_message.sender = 'user';
            currentMessages.push(result.user_message);
        }
        if (result.ai_message) {
            result.ai_message.sender = 'ai';
            currentMessages.push(result.ai_message);
        } else if (result.message) {
            // Fallback for older API structure if needed
            currentMessages.push({ sender: 'ai', content: result.message });
        }

        renderMessages();

    } catch (error) {
        console.error('Error sending message:', error);
        alert('Failed to send message. Please try again.');

        // Remove optimistic message and typing indicator on failure
        currentMessages = currentMessages.filter(m => m.id !== tempId);
        document.querySelectorAll('.typing-indicator').forEach(el => el.remove());

        renderMessages();
    }
}

async function uploadFile() {
    const fileInput = document.getElementById('file-input');
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) return;

    if (!selectedChatId) {
        alert("Please select or create a chat first.");
        return;
    }

    const files = Array.from(fileInput.files);
    const formData = new FormData();

    files.forEach(file => {
        formData.append('files', file);
    });

    try {
        const response = await fetch(`${API_URL}/chats/${selectedChatId}/documents`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            },
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        // Show success message
        alert(`Successfully uploaded ${files.length} file(s)`);

        // Clear file input
        fileInput.value = '';

        // Reload documents
        loadDocuments();

    } catch (error) {
        console.error('Error uploading file:', error);
        alert('Failed to upload file(s). Please try again.');
    }
}

async function loadDocuments() {
    if (!selectedChatId) return;

    try {
        const response = await fetch(`${API_URL}/chats/${selectedChatId}/documents`, {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const docs = await response.json();
        renderDocuments(docs);

    } catch (error) {
        console.error('Error loading documents:', error);
    }
}

function renderDocuments(docs) {
    const container = document.getElementById('chat-documents-container');
    if (!container) return;

    if (!docs || docs.length === 0) {
        container.innerHTML = '';
        return;
    }

    container.innerHTML = docs.map(doc => {
        const isProcessing = doc.status === 'processing';
        return `
        <div class="document-chip ${isProcessing ? 'processing' : ''}" title="${escapeHtml(doc.filename)}">
            <i class="fa-solid ${isProcessing ? 'fa-spinner fa-spin' : 'fa-file-lines'}"></i>
            <span class="doc-name">${escapeHtml(doc.filename)}</span>
            ${isProcessing ? '<span class="status-badge">Processing</span>' : ''}
            <button class="btn-remove-doc" onclick="deleteDocument(event, '${doc.id}')" title="Remove document">
                <i class="fa-solid fa-xmark"></i>
            </button>
        </div>
    `}).join('');
}

async function deleteDocument(event, docId) {
    event.stopPropagation();
    if (!confirm('Remove this document from the chat?')) return;

    try {
        const response = await fetch(`${API_URL}/chats/${selectedChatId}/documents/${docId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (!response.ok) throw new Error('Failed to delete document');

        loadDocuments();
    } catch (error) {
        console.error('Error deleting document:', error);
        alert('Failed to remove document.');
    }
}

// =============================================
// UI HELPERS
// =============================================

function updateChatDisplay() {
    const noChatSelected = document.getElementById('no-chat-selected');
    const chatInterface = document.getElementById('chat-interface');

    if (selectedChatId) {
        if (noChatSelected) noChatSelected.style.display = 'none';
        if (chatInterface) chatInterface.style.display = 'flex'; // Changed to flex
    } else {
        if (noChatSelected) noChatSelected.style.display = 'flex';
        if (chatInterface) chatInterface.style.display = 'none';
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// =============================================
// GLOBALS
// =============================================

let newChatBtn, logoutBtn, sendBtn, fileUploadBtn, messageInput, newChatTitle, fileInput;

// =============================================
// INITIALIZATION
// =============================================

function initializeApp() {
    console.log('========== Initializing application ==========');

    // Initialize authentication
    try {
        initializeAuth();
    } catch (error) {
        console.error('Error initializing auth:', error);
        alert('Failed to initialize authentication. Please refresh the page.');
        return;
    }

    // Get all DOM elements
    newChatBtn = document.getElementById('new-chat-btn');
    logoutBtn = document.getElementById('logout-btn');
    sendBtn = document.getElementById('send-btn');
    fileUploadBtn = document.getElementById('file-upload-btn');
    messageInput = document.getElementById('message-input');
    newChatTitle = document.getElementById('new-chat-title');
    fileInput = document.getElementById('file-input');

    // Add event listeners with null checks
    setupEventListeners();

    // Load initial data
    loadInitialData();

    // Update UI based on selected chat
    updateChatDisplay();
}

function setupEventListeners() {
    // New chat button
    if (newChatBtn) {
        newChatBtn.addEventListener('click', createChat);
    }

    // Logout button
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }

    // Send message
    if (sendBtn && messageInput) {
        sendBtn.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
=======
                if (response.ok) {
                    const data = await response.json();
                    // Store doc_id from response for filtering
                    if (data.files && data.files[0] && data.files[0].doc_id) {
                        const docInfo = {
                            filename: file.name,
                            doc_id: data.files[0].doc_id,
                            selected: true // Default selected
                        };
                        uploadedDocs.push(docInfo);
                        localStorage.setItem('uploaded_docs', JSON.stringify(uploadedDocs));
                        updateFileItemWithCheckbox(file.name, data.files[0].doc_id);
                    }
                    updateFileStatus(file.name, 'Ingested');
                } else {
                    const error = await response.json();
                    updateFileStatus(file.name, 'Failed');
                    console.error('Upload error:', error);
                }
            } catch (error) {
                console.error('Upload error:', error);
                updateFileStatus(file.name, 'Error');
>>>>>>> Stashed changes
            }
        });
    }

<<<<<<< Updated upstream
    // File upload
    if (fileUploadBtn && fileInput) {
        fileUploadBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', uploadFile);
    }

    // New chat title (Enter key)
    if (newChatTitle) {
        newChatTitle.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                createChat();
=======
    function loadUploadedDocs() {
        // Reload previously uploaded docs into the file list
        uploadedDocs.forEach(doc => {
            addFileToListFromStorage(doc);
        });
    }

    function addFileToListFromStorage(doc) {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.id = `file-${doc.filename.replace(/\s+/g, '-')}`;
        fileItem.dataset.docId = doc.doc_id;

        const iconClass = doc.filename.endsWith('.pdf') ? 'fa-file-pdf' : 'fa-file-word';

        fileItem.innerHTML = `
            <input type="checkbox" class="doc-checkbox" data-doc-id="${doc.doc_id}" ${doc.selected ? 'checked' : ''} title="Include in search">
            <i class="fa-solid ${iconClass}"></i>
            <div class="file-info">
                <span class="file-name" title="${doc.filename}">${doc.filename}</span>
                <span class="file-status">Ingested</span>
            </div>
            <i class="fa-solid fa-check-circle" style="color: #10b981;"></i>
        `;

        // Handle checkbox changes
        fileItem.querySelector('.doc-checkbox').addEventListener('change', (e) => {
            const docId = e.target.dataset.docId;
            const docIndex = uploadedDocs.findIndex(d => d.doc_id === docId);
            if (docIndex !== -1) {
                uploadedDocs[docIndex].selected = e.target.checked;
                localStorage.setItem('uploaded_docs', JSON.stringify(uploadedDocs));
            }
        });

        fileList.prepend(fileItem);
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

    function updateFileItemWithCheckbox(fileName, docId) {
        const safeName = fileName.replace(/\s+/g, '-');
        const item = document.getElementById(`file-${safeName}`);
        if (item) {
            item.dataset.docId = docId;
            // Add checkbox at the beginning
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'doc-checkbox';
            checkbox.dataset.docId = docId;
            checkbox.checked = true;
            checkbox.title = 'Include in search';
            checkbox.addEventListener('change', (e) => {
                const docIndex = uploadedDocs.findIndex(d => d.doc_id === docId);
                if (docIndex !== -1) {
                    uploadedDocs[docIndex].selected = e.target.checked;
                    localStorage.setItem('uploaded_docs', JSON.stringify(uploadedDocs));
                }
            });
            item.insertBefore(checkbox, item.firstChild);
        }
    }

    function updateFileStatus(fileName, status) {
        const safeName = fileName.replace(/\s+/g, '-');
        const item = document.getElementById(`file-${safeName}`);
        if (item) {
            const statusSpan = item.querySelector('.file-status');
            statusSpan.textContent = status;
            if (status === 'Ingested') {
                item.querySelector('.fa-check-circle').style.display = 'block';
>>>>>>> Stashed changes
            }
        });
    }
}

<<<<<<< Updated upstream
function loadInitialData() {
    // Load chats if user is authenticated
    if (accessToken) {
        loadChats().catch(error => {
            console.error('Error loading initial data:', error);
        });
=======
    function getSelectedDocIds() {
        return uploadedDocs
            .filter(doc => doc.selected)
            .map(doc => doc.doc_id);
    }

    // --- Chat Handling ---

    function addMessage(text, isUser = false, save = true) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;

        const avatarIcon = isUser ? 'fa-user' : 'fa-robot';

        messageDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid ${avatarIcon}"></i></div>
            <div class="content">${text}</div>
        `;

        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;

        // Save chat history after each message
        if (save) {
            saveChatHistory();
        }
>>>>>>> Stashed changes
    }
}

// Initialize the app when the DOM is fully loaded
function initApp() {
    console.log('Initializing app...');
    try {
        initializeApp();
    } catch (error) {
        console.error('Error initializing app:', error);
    }
}

// Check if DOM is already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    // DOM already loaded, initialize immediately
    setTimeout(initApp, 0);
}

<<<<<<< Updated upstream
// Expose functions to window for debugging
window.app = {
    logout,
    createChat,
    loadChats,
    sendMessage,
    uploadFile,
    deleteChat,
    deleteDocument
};
=======
        // Add user message
        addMessage(text, true);
        userInput.value = '';
        userInput.style.height = 'auto'; // Reset height

        const typingIndicator = showTypingIndicator();

        // Get selected document IDs for filtering
        const selectedDocIds = getSelectedDocIds();

        try {
            const response = await fetch(`${API_URL}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${accessToken}`
                },
                body: JSON.stringify({
                    query: text,
                    doc_ids: selectedDocIds.length > 0 ? selectedDocIds : null
                })
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

    // Clear chat button handler
    const clearChatBtn = document.querySelector('.icon-btn[title="Clear Chat"]');
    if (clearChatBtn) {
        clearChatBtn.addEventListener('click', () => {
            if (confirm('Clear all chat history?')) {
                clearChatHistory();
            }
        });
    }
});
>>>>>>> Stashed changes
