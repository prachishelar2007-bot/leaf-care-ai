document.addEventListener('DOMContentLoaded', function() {
    // ----------------------------------------------------
    // 1. Drag & Drop + Preview File Upload Setup
    // ----------------------------------------------------
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const dropZoneContent = document.getElementById('drop-zone-content');
    const previewContainer = document.getElementById('preview-container');
    const imagePreview = document.getElementById('image-preview');
    const removeBtn = document.getElementById('remove-btn');
    const submitBtn = document.getElementById('submit-btn');
    const uploadForm = document.getElementById('upload-form');
    const loadingOverlay = document.getElementById('loading-overlay');

    if (dropZone && fileInput) {
        // Trigger file input click when clicking the zone
        dropZone.addEventListener('click', function(e) {
            // Avoid click trigger when remove button is clicked
            if (e.target.closest('#remove-btn')) return;
            fileInput.click();
        });

        // Handle Drag state animations
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, function(e) {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, function(e) {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove('dragover');
            }, false);
        });

        // Drop handling
        dropZone.addEventListener('drop', function(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0) {
                fileInput.files = files;
                handleFileSelect(files[0]);
            }
        });

        // Browse input change handling
        fileInput.addEventListener('change', function() {
            if (fileInput.files.length > 0) {
                handleFileSelect(fileInput.files[0]);
            }
        });

        // File selection handler
        function handleFileSelect(file) {
            // Basic extension check
            const allowedExtensions = ['png', 'jpg', 'jpeg'];
            const fileExtension = file.name.split('.').pop().toLowerCase();
            if (!allowedExtensions.includes(fileExtension)) {
                alert("Invalid file format. Please upload a PNG, JPG, or JPEG image.");
                clearSelection();
                return;
            }

            // Max 5MB size check
            if (file.size > 5 * 1024 * 1024) {
                alert("File is too large. Maximum size allowed is 5MB.");
                clearSelection();
                return;
            }

            // Render Preview
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onloadend = function() {
                imagePreview.src = reader.result;
                dropZoneContent.classList.add('d-none');
                previewContainer.classList.remove('d-none');
                submitBtn.disabled = false;
            }
        }

        // Remove Selection
        if (removeBtn) {
            removeBtn.addEventListener('click', function(e) {
                e.preventDefault();
                clearSelection();
            });
        }

        function clearSelection() {
            fileInput.value = '';
            imagePreview.src = '#';
            previewContainer.classList.add('d-none');
            dropZoneContent.classList.remove('d-none');
            submitBtn.disabled = true;
        }

        // Show loading spinner when submitting scan
        if (uploadForm) {
            uploadForm.addEventListener('submit', function() {
                if (fileInput.files.length > 0) {
                    loadingOverlay.classList.remove('d-none');
                }
            });
        }
    }

    // ----------------------------------------------------
    // 2. Chatbot Operations
    // ----------------------------------------------------
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatHistory = document.getElementById('chat-history');
    const chatSendBtn = document.getElementById('chat-send-btn');
    
    // Tracks conversation history in-memory (excl system prompts)
    let messageHistory = [];

    if (chatForm && chatInput && chatHistory) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const message = chatInput.value.trim();
            if (!message) return;

            // 1. Append User Message
            appendMessage('user', message);
            chatInput.value = '';
            
            // Disable input/buttons while waiting
            chatInput.disabled = true;
            chatSendBtn.disabled = true;

            // Scroll history down
            scrollToBottom();

            // 2. Query chatbot API
            fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    prediction_id: predictionId, // Pulled from inline HTML script
                    message: message,
                    history: messageHistory
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error("Server error.");
                }
                return response.json();
            })
            .then(data => {
                const responseText = data.response;
                // 3. Append Bot Message
                appendMessage('assistant', responseText);
                
                // Add to history list for context mapping
                messageHistory.push({ role: 'user', content: message });
                messageHistory.push({ role: 'assistant', content: responseText });
            })
            .catch(error => {
                console.error("Chat error:", error);
                appendMessage('assistant', "I'm sorry, I ran into an error communicating with the leaf server. Please verify your connection or AI keys.");
            })
            .finally(() => {
                // Re-enable inputs
                chatInput.disabled = false;
                chatSendBtn.disabled = false;
                chatInput.focus();
                scrollToBottom();
            });
        });

        function appendMessage(role, text) {
            const msgDiv = document.createElement('div');
            msgDiv.className = 'd-flex align-items-start mb-3';
            
            if (role === 'assistant') {
                msgDiv.innerHTML = `
                    <div class="chat-avatar bg-success text-white rounded-circle p-2 me-2">
                        <i class="bi bi-robot"></i>
                    </div>
                    <div class="chat-bubble bot-bubble p-3 rounded-3 shadow-sm">
                        <p class="mb-0">${formatMarkdownLinks(text)}</p>
                    </div>
                `;
            } else {
                msgDiv.innerHTML = `
                    <div class="chat-bubble user-bubble p-3 rounded-3 shadow-sm ms-auto me-2">
                        <p class="mb-0">${escapeHTML(text)}</p>
                    </div>
                    <div class="chat-avatar bg-secondary text-white rounded-circle p-2">
                        <i class="bi bi-person-fill"></i>
                    </div>
                `;
            }
            
            chatHistory.appendChild(msgDiv);
        }

        function scrollToBottom() {
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }

        function escapeHTML(str) {
            return str.replace(/[&<>'"]/g, 
                tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
            );
        }

        function formatMarkdownLinks(str) {
            // Helper to escape basic text and format new lines, and replace simple markdown bold or bullets
            let escaped = escapeHTML(str);
            // Replace new lines with breaks
            escaped = escaped.replace(/\n/g, '<br>');
            // Replace **bold** with <strong>bold</strong>
            escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            // Replace * bullet points
            escaped = escaped.replace(/(?:^|<br>)\s*\*\s+(.*?)(?=<br>|$)/g, '$&').replace(/\*\s+/g, '&bull; ');
            return escaped;
        }
    }
});
