class ChatClient {
    constructor() {
        this.ws = null;
        this.chatContainer = document.getElementById('chat-container');
        this.messageInput = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-button');

        this.connect();
        this.setupEventListeners();
    }

    connect() {
        const wsUrl = `ws://${window.location.host}/ws`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            this.addSystemMessage('✅ Připojeno k J.A.R.V.I.S.');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'routing_info') {
                // Zobraz routing info (volitelné)
                const target = data.routing.target;
                const service = data.routing.service;
                this.addSystemMessage(
                    `🔀 Routing: ${target} → ${service} (${data.routing.mode})`
                );
            } else if (data.type === 'response') {
                this.removeTypingIndicator();
                this.addMessage(data.content, 'assistant');
            }
        };

        this.ws.onerror = (error) => {
            this.addSystemMessage('❌ Chyba připojení');
            console.error('WebSocket error:', error);
        };

        this.ws.onclose = () => {
            this.addSystemMessage('⚠️ Odpojeno. Zkouším reconnect...');
            setTimeout(() => this.connect(), 3000);
        };
    }

    setupEventListeners() {
        this.sendButton.addEventListener('click', () => this.sendMessage());

        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }

    sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;

        // Zobraz uživatelovu zprávu
        this.addMessage(message, 'user');

        // Pošli přes WebSocket
        this.ws.send(message);

        // Zobraz typing indicator
        this.addTypingIndicator();

        // Clear input
        this.messageInput.value = '';
    }

    addMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        messageDiv.textContent = content;
        this.chatContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    addSystemMessage(content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system';
        messageDiv.textContent = content;
        this.chatContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    addTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.id = 'typing';
        indicator.innerHTML = '<span></span><span></span><span></span>';
        this.chatContainer.appendChild(indicator);
        this.scrollToBottom();
    }

    removeTypingIndicator() {
        const indicator = document.getElementById('typing');
        if (indicator) {
            indicator.remove();
        }
    }

    scrollToBottom() {
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new ChatClient();
});
