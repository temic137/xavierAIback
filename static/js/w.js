
(function() {
    const scriptTag = document.currentScript;

    function initializeWidget(scriptTag) {
        const apiBase = scriptTag.getAttribute('data-api');
        const chatbotId = scriptTag.getAttribute('data-id');

        const urls = {
            ask: `${apiBase}chatbot/${chatbotId}/ask`,
            feedback: `${apiBase}chatbot/${chatbotId}/feedback`,
            sentiment: `${apiBase}/analytics/sentiment/${chatbotId}`,
            ticket: `${apiBase}ticket/create/${chatbotId}`,
            escalate: `${apiBase}escalate`,
            escalationStatus: `${apiBase}escalation/:escalation_id/status`,
            escalationSend: `${apiBase}escalation/:escalation_id/send`,
            escalationMessages: `${apiBase}escalation/:escalation_id/messages`,
        };

        const config = {
            chatbotId: chatbotId,
            name: scriptTag.getAttribute('data-name') || 'Support Agent',
            askUrl: urls.ask,
            feedbackUrl: urls.feedback,
            ticketUrl: urls.ticket,
            avatar: scriptTag.getAttribute('data-avatar') || './assets/agent.png',
            themeColor: scriptTag.getAttribute('data-theme') || '#0066CC',
            escalateUrl: urls.escalate,
            escalationSendUrls: urls.escalationSend,
            escalationStatusUrls: urls.escalationStatus,
            sentimentUrl: urls.sentiment,
            enableEscalation: scriptTag.getAttribute('data-enable-escalation') !== 'false',
            enableTickets: scriptTag.getAttribute('data-enable-tickets') !== 'false',
            pusherKey: scriptTag.getAttribute('data-pusher-key') || '43bd6f1835e5bb8165d8',
            pusherCluster: scriptTag.getAttribute('data-pusher-cluster') || 'us3'
        };

        // Styles (unchanged)
        const styles = `
            .chatbot-container {
                position: fixed;
                bottom: 20px;
                right: 20px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                z-index: 999999;
                width: 360px;
                line-height: normal;
            }
            .chatbot-toggle {
                background: ${config.themeColor};
                color: white;
                border: none;
                padding: 10px;
                border-radius: 50%;
                cursor: pointer;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                transition: all 0.3s ease;
                width: 60px;
                height: 60px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-left: auto;
            }
            .chatbot-toggle:hover {
                background: ${adjustColor(config.themeColor, -20)};
                transform: scale(1.05);
            }
            .chatbot-toggle svg {
                width: 30px;
                height: 30px;
                fill: currentColor;
            }
            .chatbot-avatar {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                border: 2px solid white;
                object-fit: cover;
            }
            .chatbot-content {
                display: none;
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                margin-bottom: 16px;
                overflow: hidden;
                height: 480px;
                flex-direction: column;
                position: relative;
            }
            .chatbot-content.chatbot-visible {
                display: flex;
            }
            .chatbot-header {
                padding: 20px;
                background: ${config.themeColor};
                border-bottom: 1px solid #eee;
                color: #FFFFFF;
                display: flex;
                align-items: flex-start;
                gap: 12px;
                position: relative;
            }
            .chatbot-header-info {
                display: flex;
                align-items: center;
                gap: 12px;
                flex: 1;
            }
            .chatbot-header-text {
                display: flex;
                flex-direction: column;
                gap: 4px;
            }
            .chatbot-header-dropdown {
                position: relative;
                display: inline-block;
            }
            .chatbot-header-actions {
                display: flex;
                flex-direction: column;
                gap: 8px;
                margin-top: 4px;
            }
            .chatbot-header-actions-button {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                color: #FFFFFF;
                cursor: pointer;
                padding: 8px;
                width: 36px;
                height: 36px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                transition: all 0.2s ease;
                margin-left: 8px;
            }
            .chatbot-header-actions-button:hover {
                background: rgba(255, 255, 255, 0.2);
                transform: scale(1.05);
            }
            .chatbot-header-actions-button svg {
                width: 20px;
                height: 20px;
                stroke-width: 2;
            }
            .chatbot-dropdown-menu {
                display: none;
                position: absolute;
                right: 0;
                top: 100%;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                min-width: 160px;
                z-index: 1000;
                margin-top: 4px;
            }
            .chatbot-dropdown-menu.show {
                display: block;
            }
            .chatbot-dropdown-item {
                padding: 12px 16px;
                color: #333;
                text-decoration: none;
                display: flex;
                align-items: center;
                gap: 8px;
                cursor: pointer;
                transition: background 0.2s ease;
                font-size: 14px;
            }
            .chatbot-feedback-trigger {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                color: #FFFFFF;
                cursor: pointer;
                padding: 8px 12px;
                font-size: 14px;
                border-radius: 6px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                width: 140px;
                transition: background-color 0.2s ease;
            }
            .chatbot-feedback-trigger:hover {
                background: rgba(255, 255, 255, 0.2);
            }
            .chatbot-feedback-trigger span:last-child {
                margin-left: 4px;
            }
            .chatbot-close-chat {
                position: absolute;
                top: 8px;
                right: 8px;
                background: none;
                border: none;
                color: #FFFFFF;
                font-size: 24px;
                cursor: pointer;
                padding: 4px;
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                transition: background-color 0.2s ease;
            }
            .chatbot-close-chat:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            .chatbot-status-dot {
                width: 8px;
                height: 8px;
                background: #22C55E;
                border-radius: 50%;
                margin-right: 4px;
                display: inline-block;
            }
            .chatbot-messages {
                flex-grow: 1;
                overflow-y: auto;
                padding: 20px;
                background: #f8f9fa;
            }
            .chatbot-messages::-webkit-scrollbar {
                width: 6px;
            }
            .chatbot-messages::-webkit-scrollbar-track {
                background: #f1f1f1;
            }
            .chatbot-messages::-webkit-scrollbar-thumb {
                background: #888;
                border-radius: 3px;
            }
            .chatbot-message {
                margin-bottom: 12px;
                padding: 12px 16px;
                border-radius: 12px;
                max-width: 85%;
                font-size: 14px;
                line-height: 1.5;
                word-wrap: break-word;
            }
            .chatbot-message.user {
                background: ${config.themeColor};
                color: white;
                margin-left: auto;
                border-bottom-right-radius: 4px;
            }
            .chatbot-message.bot {
                background: white;
                color: #1a1a1a;
                border-bottom-left-radius: 4px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            .chatbot-message.error {
                background: #fee2e2;
                color: #991b1b;
                margin-left: auto;
                border-bottom-right-radius: 4px;
            }
            .chatbot-input-container {
                padding: 16px;
                background: white;
                border-top: 1px solid #eee;
            }
            .chatbot-input-wrapper {
                display: flex;
                align-items: center;
                background: #f8f9fa;
                border-radius: 8px;
                padding: 8px 16px;
                gap: 8px;
            }
            .chatbot-input {
                flex-grow: 1;
                border: none;
                background: transparent;
                padding: 8px 0;
                font-size: 14px;
                min-width: 0;
                color: #1a1a1a;
            }
            .chatbot-input:focus {
                outline: none;
            }
            .chatbot-input::placeholder {
                color: #6b7280;
            }
            .chatbot-send {
                background: none;
                border: none;
                color: ${config.themeColor};
                padding: 8px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .chatbot-send:disabled {
                color: #ccc;
                cursor: not-allowed;
            }
            .chatbot-send svg {
                width: 20px;
                height: 20px;
            }
            .powered-by {
                text-align: center;
                font-size: 12px;
                color: #666;
                padding: 8px;
                background: white;
                border-top: 1px solid #eee;
            }
            .chatbot-typing {
                padding: 12px 16px;
                background: #F5F5F5;
                border-radius: 12px;
                border-bottom-left-radius: 4px;
                display: inline-block;
                margin-bottom: 12px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            .chatbot-typing-dots {
                display: flex;
                gap: 4px;
                padding: 0 4px;
            }
            .chatbot-typing-dot {
                width: 8px;
                height: 8px;
                background: ${config.themeColor};
                border-radius: 50%;
                animation: typing 1.4s infinite;
                opacity: 0.2;
            }
            .chatbot-typing-dot:nth-child(2) {
                animation-delay: 0.2s;
            }
            .chatbot-typing-dot:nth-child(3) {
                animation-delay: 0.4s;
            }
            .chatbot-ticket-form {
                display: none;
                padding: 20px;
                background: white;
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                z-index: 2;
                overflow-y: auto;
            }
            .chatbot-ticket-form.chatbot-visible {
                display: block;
            }
            .chatbot-ticket-form h3 {
                margin: 0 0 16px 0;
                color: ${config.themeColor};
                font-size: 18px;
            }
            .chatbot-form-group {
                margin-top: 2px;
                margin-bottom: 16px;
            }
            .chatbot-form-group label {
                display: block;
                margin-bottom: 8px;
                color: #333;
                font-size: 14px;
            }
            .chatbot-form-group input,
            .chatbot-form-group textarea,
            .chatbot-form-group select {
                width: 100%;
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            .chatbot-form-group textarea {
                height: 100px;
                resize: vertical;
            }
            .chatbot-ticket-actions {
                display: flex;
                gap: 8px;
            }
            .chatbot-ticket-submit,
            .chatbot-ticket-cancel {
                flex: 1;
                padding: 10px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                transition: background 0.2s ease;
                margin-bottom: 0px;
            }
            .chatbot-ticket-submit {
                background: ${config.themeColor};
                color: white;
            }
            .chatbot-ticket-cancel {
                background: #e1e1e1;
                color: #333;
            }
            .chatbot-feedback-modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                justify-content: center;
                align-items: center;
                z-index: 1000000;
            }
            .chatbot-feedback-modal.chatbot-visible {
                display: flex;
            }
            .chatbot-feedback-content {
                background: white;
                padding: 24px;
                border-radius: 12px;
                width: 90%;
                max-width: 400px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            .chatbot-feedback-content h3 {
                margin: 0 0 16px 0;
                color: #1a1a1a;
                font-size: 18px;
            }
            .chatbot-feedback-content textarea {
                width: 100%;
                height: 120px;
                padding: 12px;
                margin-bottom: 16px;
                border: 1px solid ${config.themeColor};
                border-radius: 8px;
                font-size: 14px;
                resize: vertical;
            }
            .chatbot-feedback-content textarea:focus {
                border-color: ${config.themeColor};
            }
            .chatbot-feedback-submit {
                width: 100%;
                background: #e1e1e1;
                color: ${config.themeColor};
                border: none;
                padding: 12px;
                border-radius: 8px;
                cursor: pointer;
                margin-bottom: 8px;
                font-size: 14px;
                transition: background 0.2s ease;
            }
            .chatbot-feedback-cancel {
                width: 100%;
                background: #e1e1e1;
                color: ${config.themeColor};
                border: none;
                padding: 12px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.2s ease;
            }
            .chatbot-feedback-cancel:hover {
                background: #e1e1e1;
            }
            @keyframes typing {
                0%, 100% { opacity: 0.2; transform: translateY(0); }
                50% { opacity: 1; transform: translateY(-2px); }
            }
            @media (max-width: 480px) {
                .chatbot-container {
                    right: 10px;
                    left: 10px;
                    bottom: 10px;
                    width: auto;
                }
                .chatbot-content {
                    height: calc(100vh - 100px);
                }
            }
            .chatbot-header-sentiment {
                display: flex;
                gap: 15px;
                justify-content: flex-end;
                margin-top: 5px;
                opacity: 0.7;
                transition: opacity 0.2s ease;
            }
            .chatbot-header-sentiment:hover {
                opacity: 1;
            }
            .chatbot-sentiment-button {
                background: none;
                border: none;
                cursor: pointer;
                border-radius: 8px;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 2px;
                width: 15px;
                height: 15px;
            }
            .chatbot-sentiment-button:hover {
                background: rgba(255, 255, 255, 0.1);
                transform: scale(1.1);
            }
            .chatbot-sentiment-button svg {
                width: 24px;
                height: 24px;
            }
            .chatbot-sentiment-button:hover svg {
                transform: scale(1.1);
            }
            .chatbot-sentiment.submitted {
                pointer-events: none;
                opacity: 0.5;
            }
            .chatbot-sentiment-button.disabled {
                opacity: 0.5;
                cursor: not-allowed;
                pointer-events: none;
            }
            .chatbot-form-field {
                background: white;
                padding: 12px 16px;
                border-radius: 8px;
                margin: 8px 0;
                border: 1px solid #e1e1e1;
            }
            .chatbot-form-field.completed {
                border-left: 3px solid #22C55E;
            }
            .chatbot-form-field label {
                display: block;
                font-size: 12px;
                color: #666;
                margin-bottom: 4px;
            }
            .chatbot-form-field input {
                width: 100%;
                border: none;
                font-size: 14px;
                outline: none;
            }
            .chatbot-checkmark {
                color: #22C55E;
                margin-left: 8px;
            }
        `;

        function adjustColor(color, amount) {
            const hex = color.replace('#', '');
            const r = Math.max(0, Math.min(255, parseInt(hex.substr(0, 2), 16) + amount));
            const g = Math.max(0, Math.min(255, parseInt(hex.substr(2, 2), 16) + amount));
            const b = Math.max(0, Math.min(255, parseInt(hex.substr(4, 2), 16) + amount));
            return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
        }

        const styleSheet = document.createElement('style');
        styleSheet.textContent = styles;
        document.head.appendChild(styleSheet);

        const widget = document.createElement('div');
        widget.innerHTML = `
            <div id="chatbot-widget" class="chatbot-container">
                <button id="chatbot-toggle" class="chatbot-toggle">
                    <svg viewBox="0 0 24 24" width="50" height="50" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                        <path d="M20 2H4C2.9 2 2 2.9 2 4V18C2 19.1 2.9 20 4 20H6V24L12 20H20C21.1 20 22 19.1 22 18V4C22 2.9 21.1 2 20 2ZM7 11C6.45 11 6 10.55 6 10C6 9.45 6.45 9 7 9C7.55 9 8 9.45 8 10C8 10.55 7.55 11 7 11ZM12 11C11.45 11 11 10.55 11 10C11 9.45 11.45 9 12 9C12.55 9 13 9.45 13 10C13 10.55 12.55 11 12 11ZM17 11C16.45 11 16 10.55 16 10C16 9.45 16.45 9 17 9C17.55 9 18 9.45 18 10C18 10.55 17.55 11 17 11Z"/>
                    </svg>
                </button>
                <div id="chatbot-content" class="chatbot-content">
                    <div class="chatbot-header">
                        <div class="chatbot-header-info">
                            <img src="${config.avatar}" class="chatbot-avatar" alt="${config.name}">
                            <div class="chatbot-header-text">
                                <div style="font-weight: 600">${config.name}</div>
                                <div style="font-size: 14px;">
                                    <span class="chatbot-status-dot"></span>Online
                                </div>
                            </div>
                        </div>
                        <div class="chatbot-header-sentiment">
                            <button onclick="window.chatbotWidget.submitSentiment(true)" 
                                    class="chatbot-sentiment-button chatbot-sentiment-positive" 
                                    title="Helpful">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="#e1e1e1" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                                </svg>
                            </button>
                            <button onclick="window.chatbotWidget.submitSentiment(false)" 
                                    class="chatbot-sentiment-button chatbot-sentiment-negative" 
                                    title="Not Helpful">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="#e1e1e1" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14h-4.764a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.737 3h4.017c-.163 0 .326.02.485.06L17 4m-7 10v5a2 2 0 002 2h.095c.5 0 .905-.405.905-.905 0-.714.211-1.412.608-2.006L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
                                </svg>
                            </button>
                        </div>
                        <button class="chatbot-header-actions-button" onclick="window.chatbotWidget.openFeedback()">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 13.5997 2.37562 15.1116 3.04346 16.4525L2.20834 21.1667C2.09387 21.7651 2.60432 22.2756 3.20275 22.1611L7.91676 21.326C9.25766 21.9938 10.7696 22.3694 12.3693 22.3694" 
                                      stroke="currentColor" 
                                      stroke-width="1.5" 
                                      stroke-linecap="round" 
                                      stroke-linejoin="round"/>
                                <path d="M8 12H8.01M12 12H12.01M16 12H16.01" 
                                      stroke="currentColor" 
                                      stroke-width="2" 
                                      stroke-linecap="round" 
                                      stroke-linejoin="round"/>
                            </svg>
                        </button>
                        <button class="chatbot-close-chat" onclick="window.chatbotWidget.toggle()">×</button>
                    </div>
                    <div id="chatbot-messages" class="chatbot-messages">
                        <div class="chatbot-message bot">
                            Hi there! 👋 How can I help you today?
                        </div>
                    </div>
                    <div class="chatbot-input-container">
                        <div class="chatbot-input-wrapper">
                            <input type="text" 
                                   id="chatbot-input" 
                                   class="chatbot-input"
                                   placeholder="Type your message..."
                                   autocomplete="off"
                                   onkeypress="if(event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); window.chatbotWidget.send(); }">
                            <button id="chatbot-send" onclick="window.chatbotWidget.send()" class="chatbot-send" disabled>
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M22 2L11 13M22 2L15 22L11 13M11 13L2 9L22 2"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                    <div class="powered-by">Powered by Xavier AI</div>
                    <div id="chatbot-ticket-form" class="chatbot-ticket-form">
                        <h3>Create Support Ticket</h3>
                        <h5>(It might take some time to get a response)</h5>
                        <div class="chatbot-form-group">
                            <label for="ticket-subject">Subject</label>
                            <input type="text" id="ticket-subject" required>
                        </div>
                        <div class="chatbot-form-group">
                            <label for="ticket-description">Description</label>
                            <textarea id="ticket-description" required></textarea>
                        </div>
                        <div class="chatbot-form-group">
                            <label for="ticket-priority">Priority</label>
                            <select id="ticket-priority">
                                <option value="low">Low</option>
                                <option value="medium">Medium</option>
                                <option value="high">High</option>
                            </select>
                        </div>
                        <div class="chatbot-form-group">
                            <label for="ticket-account">Contact Details</label>
                            <input type="text" id="ticket-account" required>
                        </div>
                        <div class="chatbot-ticket-actions">
                            <button onclick="window.chatbotWidget.submitTicket()" 
                                    class="chatbot-ticket-submit">Submit Ticket</button>
                            <button onclick="window.chatbotWidget.closeTicketForm()" 
                                    class="chatbot-ticket-cancel">Cancel</button>
                        </div>
                    </div>
                </div>
                <div id="chatbot-feedback" class="chatbot-feedback-modal">
                    <div class="chatbot-feedback-content">
                        <h3>Provide Feedback</h3>
                        <textarea id="chatbot-feedback-text" 
                                 placeholder="Your feedback helps us improve..."></textarea>
                        <button onclick="window.chatbotWidget.submitFeedback()" 
                                class="chatbot-feedback-submit">Submit</button>
                        <button onclick="window.chatbotWidget.closeFeedback()" 
                                class="chatbot-feedback-cancel">Cancel</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(widget);

        window.chatbotWidget = {
            userId: 'user_' + Math.random().toString(36).substr(2, 9),
            isTyping: false,
            noResponseTimeout: null,
            escalationStartTime: null,
            ticketPromptShown: false,
            ticketFormData: {},
            oldInputHandler: null,
            pusher: new Pusher(config.pusherKey, {
                cluster: config.pusherCluster,
                encrypted: true
            }),
            agentJoined: false,

            async startEscalation() {
                try {
                    if (!config.chatbotId) {
                        throw new Error('Chatbot ID is missing in widget configuration');
                    }
                    const response = await fetch(config.escalateUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'User-ID': this.userId,
                        },
                        body: JSON.stringify({
                            chatbot_id: config.chatbotId,
                        }),
                    });
                    if (!response.ok) {
                        const errorText = await response.text();
                        throw new Error(`Server error: ${response.status} - ${errorText}`);
                    }
                    const data = await response.json();
                    this.currentEscalationId = data.escalation_id;
                    this.escalationStartTime = Date.now();
                    this.ticketPromptShown = false;
                    this.noResponseTimeout = setTimeout(() => {
                        this.promptTicketCreation("If no agent has responded to your request. Would you like to create a ticket?");
                    }, 30000);
                    this.escalationStatusUrl = data.status_url;
                    this.escalationSendUrl = data.send_url;
                    this.agentJoined = false;
                    this.startPusher(this.currentEscalationId);
                    this.showEscalationChat();
                } catch (error) {
                    console.error('Escalation error:', error);
                    this.displayError(`Connection failed: ${error.message}`);
                }
            },

            startPusher(escalationId) {
                console.log(`Subscribing to channel: escalation-${escalationId}`);
                const channel = this.pusher.subscribe(`escalation-${escalationId}`);
                channel.bind('new-message', (data) => {
                    console.log('Received new-message:', data);
                    this.handleEscalationMessage(data);
                });
                channel.bind('status-update', (data) => {
                    console.log('Received status-update:', data);
                    this.handleEscalationStatus(data);
                });
                channel.bind('pusher:subscription_succeeded', () => {
                    console.log(`Successfully subscribed to escalation-${escalationId}`);
                });
                channel.bind('pusher:subscription_error', (error) => {
                    console.error('Pusher subscription error:', error);
                    this.displayError('Failed to connect to the agent. Please try again.');
                });
            },

            async submitSentiment(sentiment) {
                try {
                    const sentimentButtons = document.querySelectorAll('.chatbot-sentiment-button');
                    sentimentButtons.forEach(button => {
                        button.classList.add('disabled');
                    });

                    const response = await fetch(config.sentimentUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'User-ID': this.userId
                        },
                        body: JSON.stringify({
                            sentiment: sentiment,
                            conversation_id: this.currentConversationId
                        })
                    });

                    if (!response.ok) {
                        throw new Error('Failed to submit sentiment');
                    }

                    setTimeout(() => {
                        sentimentButtons.forEach(button => {
                            button.classList.remove('disabled');
                        });
                    }, 3000);
                } catch (error) {
                    console.error('Sentiment submission error:', error);
                    sentimentButtons.forEach(button => {
                        button.classList.remove('disabled');
                    });
                }
            },

            handleEscalationStatus(data) {
                if (data.status === 'in_progress' && !this.agentJoined) {
                    if (this.noResponseTimeout) {
                        clearTimeout(this.noResponseTimeout);
                        this.noResponseTimeout = null;
                    }
                    this.displayMessage('Agent has joined the conversation. You can now chat directly.', 'bot');
                    this.agentJoined = true;
                } else if (data.status !== 'in_progress') {
                    this.displayMessage(`Escalation status: ${data.status}`, 'bot');
                    this.agentJoined = false;
                }
            },

            handleEscalationMessage(data) {
                console.log('Handling message:', data);
                const messages = document.getElementById('chatbot-messages');
                if (!messages) {
                    console.error('chatbot-messages element not found');
                    return;
                }
                const existingMessage = messages.querySelector(`[data-message-id="${data.id}"]`);
                if (!existingMessage) {
                    this.displayMessage(data.message, data.sender === 'agent' ? 'bot' : 'user', data.id);
                } else {
                    console.log(`Message ${data.id} already exists, skipping`);
                }
            },

            showEscalationChat() {
                const input = document.getElementById('chatbot-input');
                if (input) {
                    this.originalChatHandler = input.onkeypress;
                }

                const messages = document.getElementById('chatbot-messages');
                if (messages) {
                    messages.innerHTML = `
                        <div class="chatbot-message bot">
                            Connecting you to a live agent... Please wait.
                        </div>
                    `;
                }

                const inputContainer = document.querySelector('.chatbot-input-container');
                if (inputContainer) {
                    inputContainer.innerHTML = `
                        <div class="chatbot-input-wrapper">
                            <input type="text" 
                                   id="escalation-input" 
                                   class="chatbot-input"
                                   placeholder="Type your message to the agent..."
                                   autocomplete="off">
                            <button id="send-to-agent" class="chatbot-send">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M22 2L11 13M22 2L15 22L11 13M11 13L2 9L22 2"/>
                                </svg>
                            </button>
                        </div>
                    `;

                    const escalationInput = document.getElementById('escalation-input');
                    const sendButton = document.getElementById('send-to-agent');

                    if (escalationInput && sendButton) {
                        escalationInput.addEventListener('keypress', (event) => {
                            if (event.key === 'Enter') this.sendToAgent();
                        });
                        sendButton.addEventListener('click', () => this.sendToAgent());
                        escalationInput.focus();
                    }
                }
            },

            async sendToAgent() {
                const input = document.getElementById('escalation-input');
                if (!input) {
                    console.error('Escalation input not found');
                    return;
                }
                const message = input.value.trim();

                if (!message || !this.currentEscalationId) return;

                console.log('Sending message to agent:', message);

                const sendUrl = config.escalationSendUrls.replace(':escalation_id', this.currentEscalationId);
                try {
                    const response = await fetch(sendUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'User-ID': this.userId,
                        },
                        body: JSON.stringify({ message }),
                    });

                    if (!response.ok) {
                        throw new Error(`Failed to send message: ${response.status}`);
                    }
                    input.value = '';
                } catch (error) {
                    console.error('Message send error:', error);
                    this.displayError('Failed to send message');
                }
            },

            displayMessage(message, type, messageId = null) {
                const messages = document.getElementById('chatbot-messages');
                if (!messages) {
                    console.error('chatbot-messages element not found');
                    return;
                }
                const div = document.createElement('div');
                div.className = `chatbot-message ${type}`;
                if (messageId) div.dataset.messageId = messageId;
                div.textContent = message;
                messages.appendChild(div);
                messages.scrollTop = messages.scrollHeight;
            },

            displayError(message) {
                const messages = document.getElementById('chatbot-messages');
                if (!messages) {
                    console.error('chatbot-messages element not found');
                    return;
                }
                const div = document.createElement('div');
                div.className = 'chatbot-message error';
                div.textContent = message;
                messages.appendChild(div);
                messages.scrollTop = messages.scrollHeight;
            },

            toggle() {
                const content = document.getElementById('chatbot-content');
                const toggle = document.getElementById('chatbot-toggle');
                content.classList.toggle('chatbot-visible');
                toggle.style.display = content.classList.contains('chatbot-visible') ? 'none' : 'flex';
                if (content.classList.contains('chatbot-visible')) {
                    const input = document.getElementById('chatbot-input') || document.getElementById('escalation-input');
                    if (input) input.focus();
                } else if (this.currentEscalationId) {
                    this.pusher.unsubscribe(`escalation-${this.currentEscalationId}`);
                    if (this.noResponseTimeout) {
                        clearTimeout(this.noResponseTimeout);
                        this.noResponseTimeout = null;
                    }
                    this.currentEscalationId = null;
                    this.agentJoined = false;
                }
            },

            showTyping() {
                if (this.isTyping) return;
                
                this.isTyping = true;
                const messages = document.getElementById('chatbot-messages');
                messages.insertAdjacentHTML('beforeend', `
                    <div id="typing-indicator" class="chatbot-typing">
                        <div class="chatbot-typing-dots">
                            <div class="chatbot-typing-dot"></div>
                            <div class="chatbot-typing-dot"></div>
                            <div class="chatbot-typing-dot"></div>
                        </div>
                    </div>
                `);
                messages.scrollTop = messages.scrollHeight;
            },

            hideTyping() {
                if (!this.isTyping) return;
                
                this.isTyping = false;
                const typingIndicator = document.getElementById('typing-indicator');
                if (typingIndicator) {
                    typingIndicator.remove();
                }
            },

            checkCannotHelpResponse(response) {
                const text = response.toLowerCase().trim();
                const patterns = {
                    cannotPhrases: ['cannot', 'can\'t', 'unable to', 'not able to', 'don\'t have', 'do not have', 'couldn\'t', 'could not', 'won\'t be able'],
                    knowledgePhrases: ['context', 'information', 'knowledge', 'data', 'details', 'trained on', 'database', 'records', 'access to'],
                    limitationPhrases: ['limited', 'beyond', 'outside', 'exceed', 'limit', 'restriction', 'boundary', 'scope', 'coverage'],
                    uncertaintyPhrases: ['unsure', 'uncertain', 'not sure', 'don\'t know', 'do not know', 'unclear', 'ambiguous'],
                    apologyPhrases: ['sorry', 'apolog', 'unfortunately', 'regret', 'afraid', 'unable'],
                    impossibilityPhrases: ['cannot provide', 'can\'t assist', 'not possible', 'unable to help', 'can\'t answer', 'cannot answer'],
                    missingPhrases: ['missing', 'lack', 'need more', 'additional', 'insufficient', 'not enough'],
                    redirectionPhrases: ['suggest', 'recommend', 'might want to', 'better to', 'would be best', 'try asking']
                };

                const containsAnyPhrase = (text, phrases) => phrases.some(phrase => text.includes(phrase));
                
                let score = 0;
                
                if (containsAnyPhrase(text, patterns.cannotPhrases)) score += 2;
                if (containsAnyPhrase(text, patterns.knowledgePhrases)) score += 1;
                if (containsAnyPhrase(text, patterns.limitationPhrases)) score += 1;
                if (containsAnyPhrase(text, patterns.uncertaintyPhrases)) score += 1.5;
                if (containsAnyPhrase(text, patterns.apologyPhrases)) score += 1;
                if (containsAnyPhrase(text, patterns.impossibilityPhrases)) score += 2;
                if (containsAnyPhrase(text, patterns.missingPhrases)) score += 1;
                if (containsAnyPhrase(text, patterns.redirectionPhrases)) score += 1;
                
                if (text.includes('would need to') && text.includes('more')) score += 1;
                if (text.includes('don\'t') && text.includes('access')) score += 1.5;
                if (text.includes('not') && text.includes('available')) score += 1.5;
                
                const commonPatterns = [
                    /i (?:am|\'m) not (?:able|capable) to/,
                    /(?:cannot|can\'t) (?:help|assist|provide|answer)/,
                    /(?:don\'t|do not) have (?:enough|sufficient|the|that)/,
                    /(?:beyond|outside) (?:my|the) (?:scope|capability|knowledge)/,
                    /not (?:within|in) (?:my|the) (?:scope|capability|knowledge)/,
                    /would need more (?:information|details|context)/,
                    /(?:unable|impossible) to (?:provide|give|offer)/,
                    /not (?:authorized|permitted|allowed) to/
                ];
                
                commonPatterns.forEach(pattern => {
                    if (pattern.test(text)) score += 1.5;
                });
                
                if (score >= 3 && config.enableEscalation) {
                    setTimeout(() => this.addEscalationButtons(), 1000);
                }
                
                return score >= 3;
            },

            checkEscalationIntent(message) {
                const text = message.toLowerCase().trim();
                const patterns = {
                    directRequests: ['escalate', 'speak to agent', 'talk to human', 'talk to agent', 'live agent', 'real person', 'connect to agent', 'transfer to agent', 'speak with someone', 'talk to someone', 'connect me', 'transfer me', 'real agent', 'human agent', 'live person', 'real human', 'live human', 'speak to a person', 'talk to a person', 'speak to someone else', 'speak with a human', 'talk with a human', 'chat with human', 'chat with agent', 'human support', 'agent support'],
                    frustrationPhrases: ['not helping', 'this isn\'t helping', 'you don\'t understand', 'you\'re not understanding', 'this is frustrating', 'getting frustrated', 'need a human', 'need a person', 'useless', 'waste of time', 'going nowhere', 'not getting anywhere', 'this is pointless', 'you\'re just a bot', 'stupid bot', 'not what i need', 'you\'re not helpful', 'this isn\'t working', 'getting nowhere', 'tired of this', 'fed up', 'annoying', 'irritating'],
                    humanPreference: ['human please', 'real human', 'actual person', 'want to speak to a person', 'prefer to talk to', 'rather speak to', 'rather talk to', 'need to speak to', 'want to talk to', 'have to speak to', 'must speak to', 'need a real', 'want a real', 'prefer a real', 'can i get a human', 'can i speak to someone', 'is there anyone', 'is there someone', 'real support', 'human assistance'],
                    supportRequests: ['customer service', 'customer support', 'technical support', 'need assistance', 'help desk', 'support team', 'service desk', 'tech support', 'human support', 'live support', 'real support', 'support agent', 'help team', 'support staff', 'service team'],
                    actionVerbs: ['need', 'want', 'require', 'request', 'demand', 'prefer', 'like', 'wish', 'must', 'have to', 'got to', 'gotta']
                };

                const containsAnyPhrase = (text, phrases) => phrases.some(phrase => text.includes(phrase));
                let score = 0;

                if (containsAnyPhrase(text, patterns.directRequests)) score += 3;
                if (containsAnyPhrase(text, patterns.frustrationPhrases)) score += 2;
                if (containsAnyPhrase(text, patterns.humanPreference)) score += 2;
                if (containsAnyPhrase(text, patterns.supportRequests)) score += 1.5;

                patterns.actionVerbs.forEach(verb => {
                    if (text.includes(verb)) {
                        if (containsAnyPhrase(text, ['human', 'agent', 'person', 'someone'])) score += 2;
                        if (containsAnyPhrase(text, ['support', 'help', 'assistance'])) score += 1.5;
                    }
                });

                if (text.includes('can i') && containsAnyPhrase(text, ['speak', 'talk', 'connect', 'chat'])) score += 1.5;
                if (text.includes('please') && containsAnyPhrase(text, ['human', 'agent', 'person'])) score += 1.5;
                if (/^(can|could|may|would|is there|are there)/.test(text) && containsAnyPhrase(text, ['human', 'agent', 'person', 'someone', 'support'])) score += 1.5;
                if (text.includes('bot') && containsAnyPhrase(text, ['don\'t', 'not', 'stop', 'no'])) score += 1.5;

                return score >= 2;
            },

            checkTicketIntent(message) {
                const text = message.toLowerCase().trim();
                const patterns = {
                    directRequests: ['create ticket', 'open ticket', 'submit ticket', 'raise ticket', 'new ticket', 'support ticket', 'help ticket', 'make a ticket', 'start a ticket', 'generate ticket', 'file a ticket', 'get a ticket', 'issue a ticket'],
                    ticketPhrases: ['ticket', 'support request', 'issue report', 'problem report', 'case'],
                    actionVerbs: ['need', 'want', 'require', 'request', 'demand', 'create', 'open', 'submit', 'raise', 'make', 'start', 'generate', 'file', 'get', 'issue'],
                    helpPhrases: ['help me', 'assist me', 'can you', 'could you', 'please', 'i\'d like to', 'i want to'],
                    questionPhrases: ['do you', 'does it', 'is there', 'are there', 'can it', 'have you', 'feature', 'option', 'ability']
                };

                const containsAnyPhrase = (text, phrases) => phrases.some(phrase => text.includes(phrase));
                let score = 0;

                // Strong indicators: explicit ticket creation requests
                if (containsAnyPhrase(text, patterns.directRequests)) score += 3;

                // Action verbs with ticket-related terms
                patterns.actionVerbs.forEach(verb => {
                    if (text.includes(verb) && containsAnyPhrase(text, patterns.ticketPhrases)) {
                        score += 2;
                    }
                });

                // Help phrases with ticket terms
                if (containsAnyPhrase(text, patterns.helpPhrases) && containsAnyPhrase(text, patterns.ticketPhrases)) {
                    score += 2;
                }

                // Reduce score for question-like phrases unless explicitly requesting action
                if (containsAnyPhrase(text, patterns.questionPhrases)) {
                    if (!containsAnyPhrase(text, patterns.actionVerbs) && !containsAnyPhrase(text, patterns.helpPhrases)) {
                        score -= 2; // Penalize questions about features
                    }
                }

                // Boost for first-person intent
                if (text.includes('i') && containsAnyPhrase(text, patterns.ticketPhrases)) score += 1;

                console.log(`Ticket intent score for "${text}": ${score}`); // Debug log
                return score >= 2;
            },

            async send() {
                const input = document.getElementById('chatbot-input');
                const messages = document.getElementById('chatbot-messages');
                const sendButton = document.getElementById('chatbot-send');
                const question = input.value.trim();
                
                if (!question) return;
                
                try {
                    input.disabled = true;
                    sendButton.disabled = true;
                    
                    // Check for escalation intent
                    if (config.enableEscalation && this.checkEscalationIntent(question)) {
                        messages.innerHTML += `<div class="chatbot-message user">${this.escapeHtml(question)}</div>`;
                        input.value = '';
                        messages.scrollTop = messages.scrollHeight;
                        
                        setTimeout(() => {
                            this.displayMessage("I understand you'd like to speak with a live agent.", "bot");
                            this.addEscalationButtons();
                        }, 500);
                        
                        input.disabled = false;
                        sendButton.disabled = false;
                        return;
                    }

                    // Check for ticket creation intent
                    if (config.enableTickets && this.checkTicketIntent(question)) {
                        messages.innerHTML += `<div class="chatbot-message user">${this.escapeHtml(question)}</div>`;
                        input.value = '';
                        messages.scrollTop = messages.scrollHeight;
                        
                        setTimeout(() => {
                            this.displayMessage("I understand you'd like to create a ticket.", "bot");
                            this.openTicketForm();
                        }, 500);
                        
                        input.disabled = false;
                        sendButton.disabled = false;
                        return;
                    }
                    
                    // Normal chatbot response
                    messages.innerHTML += `<div class="chatbot-message user">${this.escapeHtml(question)}</div>`;
                    input.value = '';
                    messages.scrollTop = messages.scrollHeight;
                    
                    this.showTyping();
                    
                    const response = await fetch(config.askUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'User-ID': this.userId
                        },
                        body: JSON.stringify({ question })
                    });
                    
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    
                    const data = await response.json();
                    this.hideTyping();
                    const cannotHelp = this.checkCannotHelpResponse(data.answer);
                    messages.innerHTML += `<div class="chatbot-message bot">${this.escapeHtml(data.answer)}</div>`;
                    
                    if (cannotHelp) {
                        setTimeout(() => this.addEscalationButtons(), 1000);
                    }
                } catch (error) {
                    console.error('Chatbot error:', error);
                    this.hideTyping();
                    messages.innerHTML += `
                        <div class="chatbot-message error">
                            Sorry, something went wrong. Please try again.
                        </div>
                    `;
                } finally {
                    input.disabled = false;
                    sendButton.disabled = false;
                    input.focus();
                    messages.scrollTop = messages.scrollHeight;
                }
            },

            openFeedback() {
                document.getElementById('chatbot-feedback').classList.add('chatbot-visible');
            },

            closeFeedback() {
                document.getElementById('chatbot-feedback').classList.remove('chatbot-visible');
                document.getElementById('chatbot-feedback-text').value = '';
            },

            async submitFeedback() {
                const textarea = document.getElementById('chatbot-feedback-text');
                const feedback = textarea.value.trim();
                
                if (!feedback) {
                    alert('Please enter your feedback before submitting.');
                    return;
                }
                
                try {
                    await fetch(config.feedbackUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'User-ID': this.userId
                        },
                        body: JSON.stringify({ feedback })
                    });
                    
                    alert('Thank you for your feedback!');
                    this.closeFeedback();
                } catch (error) {
                    console.error('Feedback error:', error);
                    alert('Sorry, we couldn\'t submit your feedback. Please try again.');
                }
            },

            openTicketForm() {
                this.ticketFormData = {};
                const input = document.getElementById('chatbot-input');
                if (!input) {
                    console.error('Input element not found');
                    return;
                }
                
                this.oldInputHandler = input.onkeypress;
                input.onkeypress = null;
                input.placeholder = "Type your response...";
                
                const sendButton = document.getElementById('chatbot-send');
                if (sendButton) {
                    sendButton.disabled = false;
                }
                
                this.displayMessage("Let's create a ticket to help resolve your issue. First, please enter a subject for your ticket:", "bot");
                
                input.onkeypress = (event) => {
                    if (event.key === 'Enter') {
                        event.preventDefault();
                        this.handleTicketInput('subject');
                    }
                };
                
                input.addEventListener('input', () => {
                    if (sendButton) {
                        sendButton.disabled = !input.value.trim();
                    }
                });
            },

            handleTicketInput(field) {
                const input = document.getElementById('chatbot-input');
                const value = input.value.trim();
                
                if (!value) {
                    this.displayMessage("This field cannot be empty. Please try again.", "error");
                    return;
                }
                
                const fieldDiv = document.createElement('div');
                fieldDiv.className = 'chatbot-message bot';
                fieldDiv.innerHTML = `
                    <div class="chatbot-form-field completed">
                        <label>${this.getFieldLabel(field)}</label>
                        <div style="display: flex; align-items: center;">
                            <span>${this.escapeHtml(value)}</span>
                            <span class="chatbot-checkmark">✓</span>
                        </div>
                    </div>
                `;
                
                const messages = document.getElementById('chatbot-messages');
                messages.appendChild(fieldDiv);
                messages.scrollTop = messages.scrollHeight;
                
                input.value = '';
                this.ticketFormData[field] = value;
                
                switch (field) {
                    case 'subject':
                        this.displayMessage("Great! Now please provide a detailed description of the issue:", "bot");
                        input.onkeypress = (event) => {
                            if (event.key === 'Enter') {
                                event.preventDefault();
                                this.handleTicketInput('description');
                            }
                        };
                        break;
                    
                    case 'description':
                        this.displayMessage("Finally, please provide your contact details:", "bot");
                        input.onkeypress = (event) => {
                            if (event.key === 'Enter') {
                                event.preventDefault();
                                this.handleTicketInput('account');
                            }
                        };
                        break;
                    
                    case 'account':
                        this.ticketFormData.priority = 'medium';
                        this.displayTicketSummary();
                        break;
                }
            },

            getFieldLabel(field) {
                const labels = {
                    subject: 'Subject',
                    description: 'Description',
                    priority: 'Priority Level',
                    account: 'Account Details'
                };
                return labels[field] || field;
            },

            displayTicketSummary() {
                this.displayMessage("Perfect! I've collected all the information needed.", "bot");
                
                const messages = document.getElementById('chatbot-messages');
                const buttonDiv = document.createElement('div');
                buttonDiv.className = 'chatbot-message bot';
                buttonDiv.style.display = 'flex';
                buttonDiv.style.gap = '10px';
                buttonDiv.innerHTML = `
                    <button onclick="window.chatbotWidget.submitTicketForm()" 
                            style="background: ${config.themeColor}; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                        Submit Ticket
                    </button>
                    <button onclick="window.chatbotWidget.cancelTicketForm()" 
                            style="background: #e1e1e1; color: #333; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                        Cancel
                    </button>
                `;
                messages.appendChild(buttonDiv);
                messages.scrollTop = messages.scrollHeight;
            },

            async submitTicketForm() {
                try {
                    const response = await fetch(config.ticketUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'User-ID': this.userId
                        },
                        body: JSON.stringify({
                            subject: this.ticketFormData.subject,
                            description: this.ticketFormData.description,
                            priority: 'medium',
                            account_details: this.ticketFormData.account
                        })
                    });

                    if (!response.ok) {
                        throw new Error('Failed to create ticket');
                    }

                    const data = await response.json();
                    this.displayMessage(`Ticket created successfully! Your ticket ID is: ${data.ticket_id}`, "bot");
                    this.resetTicketForm();
                } catch (error) {
                    console.error('Ticket creation error:', error);
                    this.displayMessage("Sorry, we couldn't create your ticket. Please try again.", "error");
                }
            },

            cancelTicketForm() {
                this.displayMessage("Ticket creation cancelled.", "bot");
                this.resetTicketForm();
            },

            resetTicketForm() {
                const input = document.getElementById('chatbot-input');
                input.placeholder = "Type your message...";
                input.onkeypress = null;
                if (this.oldInputHandler) {
                    input.onkeypress = this.oldInputHandler;
                    this.oldInputHandler = null;
                }
                this.ticketFormData = {};
                input.value = '';
                input.focus();
            },

            escapeHtml(unsafe) {
                return unsafe
                    .replace(/&/g, "&")
                    .replace(/</g, "<")
                    .replace(/>/g, ">")
                    // .replace(/"/g, """)
                    .replace(/'/g, "'");
            },

            addEscalationButtons() {
                if (!config.enableEscalation) return;

                const messages = document.getElementById('chatbot-messages');
                const buttonDiv = document.createElement('div');
                buttonDiv.className = 'chatbot-message bot';
                buttonDiv.style.display = 'flex';
                buttonDiv.style.flexDirection = 'column';
                buttonDiv.style.gap = '10px';
                buttonDiv.innerHTML = `
                    <div style="margin-bottom: 10px;">It seems I'm unable to fully address your question. Would you like to speak with a live agent?</div>
                    <div style="display: flex; gap: 10px; justify-content: flex-start;">
                        <button 
                            class="escalate-button" 
                            style="
                                background: ${config.themeColor}; 
                                color: white; 
                                border: none; 
                                padding: 8px 8px; 
                                border-radius: 4px; 
                                cursor: pointer;
                                font-size: 14px;
                                transition: background-color 0.2s ease;
                            "
                            onclick="window.chatbotWidget.startEscalation()">
                            Yes, talk to an agent
                        </button>
                        <button 
                            class="escalate-button" 
                            style="
                                background: #e1e1e1; 
                                color: #333; 
                                border: none; 
                                padding: 8px 8px; 
                                border-radius: 5px; 
                                cursor: pointer;
                                font-size: 14px;
                                transition: background-color 0.2s ease;
                            "
                            onclick="window.chatbotWidget.declineEscalation()">
                            No, thanks
                        </button>
                    </div>
                `;
                messages.appendChild(buttonDiv);
                messages.scrollTop = messages.scrollHeight;
            },

            declineEscalation() {
                const messages = document.getElementById('chatbot-messages');
                messages.innerHTML += `
                    <div class="chatbot-message bot">
                        Okay, let me know if you need anything else!
                    </div>
                `;
                messages.scrollTop = messages.scrollHeight;
            },

            promptTicketCreation(message) {
                if (this.ticketPromptShown || !config.enableTickets) return;
                
                this.ticketPromptShown = true;
                const messages = document.getElementById('chatbot-messages');
                messages.innerHTML += `
                    <div class="chatbot-message bot">
                        ${message}
                        <div style="display: flex; gap: 10px; margin-top: 10px;">
                            <button onclick="window.chatbotWidget.startTicketFromEscalation()" 
                                    style="background: ${config.themeColor}; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                                Create Ticket
                            </button>
                            <button onclick="window.chatbotWidget.declineTicket()" 
                                    style="background: #e1e1e1; color: #333; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                                No, thanks
                            </button>
                        </div>
                    </div>
                `;
                messages.scrollTop = messages.scrollHeight;
            },

            startTicketFromEscalation() {
                if (this.noResponseTimeout) {
                    clearTimeout(this.noResponseTimeout);
                }
                
                const inputContainer = document.querySelector('.chatbot-input-container');
                inputContainer.innerHTML = `
                    <div class="chatbot-input-wrapper">
                        <input type="text" 
                               id="chatbot-input" 
                               class="chatbot-input"
                               placeholder="Type your response..."
                               autocomplete="off">
                        <button id="chatbot-send" class="chatbot-send">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M22 2L11 13M22 2L15 22L11 13M11 13L2 9L22 2"/>
                            </svg>
                        </button>
                    </div>
                `;
                
                this.currentEscalationId = null;
                this.escalationStartTime = null;
                this.ticketPromptShown = false;
                
                const input = document.getElementById('chatbot-input');
                input.onkeypress = null;
                this.openTicketForm();
            },

            declineTicket() {
                const messages = document.getElementById('chatbot-messages');
                messages.innerHTML += `
                    <div class="chatbot-message bot">
                        Okay, please let me know if you change your mind or need anything else!
                    </div>
                `;
                messages.scrollTop = messages.scrollHeight;
            }
        };

        document.getElementById('chatbot-toggle').onclick = () => window.chatbotWidget.toggle();
        const input = document.getElementById('chatbot-input');
        const sendButton = document.getElementById('chatbot-send');
        input.addEventListener('input', () => {
            sendButton.disabled = !input.value.trim();
        });
    }

    if (!window.Pusher) {
        const script = document.createElement('script');
        script.src = 'https://js.pusher.com/8.2/pusher.min.js';
        script.async = true;
        script.onload = () => {
            console.log('Pusher script loaded');
            initializeWidget(scriptTag);
        };
        script.onerror = () => {
            console.error('Failed to load Pusher script');
            document.body.innerHTML += '<div style="color: red;">Failed to load chatbot. Please refresh the page.</div>';
        };
        document.head.appendChild(script);
    } else {
        initializeWidget(scriptTag);
    }
})();