document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const fileList = document.getElementById('file-list');
    const chatHistory = document.getElementById('chat-history');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');

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
        Array.from(files).forEach(file => {
            addFileToList(file);
            // Simulate upload process
            setTimeout(() => {
                updateFileStatus(file.name, 'Ingested');
            }, 1500);
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
            item.querySelector('.fa-check-circle').style.display = 'block';
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

    function handleSend() {
        const text = userInput.value.trim();
        if (!text) return;

        // Add user message
        addMessage(text, true);
        userInput.value = '';
        userInput.style.height = 'auto'; // Reset height

        // Simulate AI response
        const typingIndicator = showTypingIndicator();

        setTimeout(() => {
            typingIndicator.remove();
            const response = generateMockResponse(text);
            addMessage(response);
        }, 1500 + Math.random() * 1000);
    }

    function generateMockResponse(query) {
        const responses = [
            "Based on the documents you uploaded, I found that section 3.2 discusses the implementation details of the RAG architecture.",
            "The file 'Project_Specs.pdf' mentions that the deadline is set for Q4 2024.",
            "I can confirm that the security protocols require JWT authentication as per the documentation.",
            "That's a great question. The documents suggest using FAISS for vector search to optimize performance.",
            "According to the executive summary, the primary goal is to improve document retrieval efficiency by 40%.",
            "Hello, how can i help you ?"
        ];
        return responses[Math.floor(Math.random() * responses.length)];
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
