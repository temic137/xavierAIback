(function() {
    // Get configuration from script tag
    const script = document.currentScript;
    const config = {
        chatbotId: script.getAttribute('data-chatbot-id'),
        name: script.getAttribute('data-name') || 'Support Agent',
        askUrl: script.getAttribute('data-ask-url'),
        feedbackUrl: script.getAttribute('data-feedback-url'),
        ticketUrl: script.getAttribute('data-ticket-url'),
        avatar: script.getAttribute('data-avatar') || './assets/agent.png',
        themeColor: script.getAttribute('data-theme-color') || '#0066CC',
        escalateUrl: script.getAttribute('data-escalate-url'),
        escalationSendUrls: script.getAttribute('data-escalation-send-url'),
        escalationStatusUrls: script.getAttribute('data-escalation-status-url'),
        escalationMessages: script.getAttribute('data-escalation-messages-url'),
        sentimentUrl: script.getAttribute('data-sentiment-url'),

    };

    //  // URL templates for escalation
    //  const urlTemplates = {
    //     statusUrl: script.getAttribute('data-escalation-status-url'),
    //     sendUrl: script.getAttribute('data-escalation-send-url'),
    //     messagesUrl: script.getAttribute('data-escalation-messages-url')
    // };

    // // Function to generate escalation URLs
    // function getEscalationUrls(escalationId) {
    //     return {
    //         status: urlTemplates.statusUrl.replace(':escalation_id', escalationId),
    //         send: urlTemplates.sendUrl.replace(':escalation_id', escalationId),
    //         messages: urlTemplates.messagesUrl.replace(':escalation_id', escalationId)
    //     };
    // }

    // // Add URL generator to config
    // config.getEscalationUrls = getEscalationUrls;


    // Styles
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
            background: none;
            border: none;
            color: #FFFFFF;
            cursor: pointer;
            padding: 8px;
            font-size: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 4px;
        }

        .chatbot-header-actions-button:hover {
            background: rgba(255, 255, 255, 0.1);
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

        .chatbot-dropdown-item:hover {
            background: #f5f5f5;
        }

        .chatbot-dropdown-item:first-child {
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }

        .chatbot-dropdown-item:last-child {
            border-bottom-left-radius: 8px;
            border-bottom-right-radius: 8px;
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
            padding: 0px;
            background: white;
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 1;
            overflow-y: auto;
        }

        .chatbot-ticket-form.chatbot-visible {
            display: block;
        }

        .chatbot-ticket-form h3 {
            margin: 0 0 0 0;
            color: ${config.themeColor};
            font-size: 18px;
        }

        .chatbot-form-group {
            margin-top:2px;
            margin-bottom: 5px;
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
            background: #e1e1e1 ;
            color: ${config.themeColor};
            border: none;
            padding: 12px;
            border-radius: 8px;
            cursor: pointer;
            margin-bottom: 8px;
            font-size: 14px;
            transition: background 0.2s ease;
        }

         .chatbot-feedback-submit:hover {
           
        }

        .chatbot-feedback-cancel {
            width: 100%;
            background:#e1e1e1 ;
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
  border-radius: 8px; /* Slightly rounded corners */
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 2px;
  width:15px;
  height:15px;
}

.chatbot-sentiment-button:hover {
  background: rgba(255, 255, 255, 0.1); /* Subtle hover effect */
  transform: scale(1.1);
}


.chatbot-sentiment-button svg {
  width: 24px; /* Icon size */
  height: 24px;
}

.chatbot-sentiment-button:hover svg {
  transform: scale(1.1); /* Slightly scale up icons on hover */
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
    `;

    // Helper function to adjust color brightness
    function adjustColor(color, amount) {
        const hex = color.replace('#', '');
        const r = Math.max(0, Math.min(255, parseInt(hex.substr(0, 2), 16) + amount));
        const g = Math.max(0, Math.min(255, parseInt(hex.substr(2, 2), 16) + amount));
        const b = Math.max(0, Math.min(255, parseInt(hex.substr(4, 2), 16) + amount));
        return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
    }

    // Inject styles
    const styleSheet = document.createElement('style');
    styleSheet.textContent = styles;
    document.head.appendChild(styleSheet);

    // Create widget HTML
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
            <!-- Thumbs Up SVG Icon -->
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="#e1e1e1" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
            </svg>
            </button>
            <button onclick="window.chatbotWidget.submitSentiment(false)" 
                    class="chatbot-sentiment-button chatbot-sentiment-negative" 
                    title="Not Helpful">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="#e1e1e1" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14h-4.764a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.737 3h4.017c.163 0 .326.02.485.06L17 4m-7 10v5a2 2 0 002 2h.095c.5 0 .905-.405.905-.905 0-.714.211-1.412.608-2.006L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
            </svg>
            </button>
            </div>
                
                        <div class="chatbot-header-actions">
                <div class="chatbot-header-dropdown">
                    <button class="chatbot-header-actions-button" onclick="window.chatbotWidget.toggleDropdown()">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="3" y1="12" x2="21" y2="12"></line>
                            <line x1="3" y1="6" x2="21" y2="6"></line>
                            <line x1="3" y1="18" x2="21" y2="18"></line>
                        </svg>
                    </button>
                    <div id="chatbot-dropdown-menu" class="chatbot-dropdown-menu">
                        <button class="chatbot-dropdown-item" onclick="window.chatbotWidget.openTicketForm()">
                            <span>Create Ticket</span>
                            <span>🎫</span>
                        </button>
                        <button class="chatbot-dropdown-item" onclick="window.chatbotWidget.openFeedback()">
                            <span>Feedback</span>
                            <span>💬</span>
                        </button>
                        <button class="chatbot-dropdown-item" onclick="window.chatbotWidget.startEscalation()">
                            <span>Escalate to Agent</span>
                            <span>🆘</span>
                        </button>
                    </div>
                </div>

                           
            </div>


                    
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

                <!-- Ticket Form -->
                <div id="chatbot-ticket-form" class="chatbot-ticket-form">
                    <h3>Create Support Ticket</h3>
                    <h5>(It might take sometime to get a response)</h5>
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
                        <label for="ticket-account">Account Details</label>
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

            <!-- Feedback Modal -->
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

    // Initialize widget functionality
    window.chatbotWidget = {
        userId: 'user_' + Math.random().toString(36).substr(2, 9),
        isTyping: false,
        

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

            // Store the URLs returned from the server
            this.escalationStatusUrl = data.status_url;
            this.escalationSendUrl = data.send_url;

            // Start SSE connection for real-time updates
            this.startSSE(this.currentEscalationId);

            console.log('Escalation created with ID:', this.currentEscalationId);
            this.showEscalationChat();

            // Start polling for status and messages using SSE
            this.pollEscalationStatus();
            this.pollEscalationMessages();

        } catch (error) {
            console.error('Escalation error:', error);
            this.displayError(`Connection failed: ${error.message}`);
        }
    },

    // Start SSE connection for real-time updates
    startSSE(escalationId) {
        if (this.eventSource) {
            this.eventSource.close(); // Close existing connection
        }

        const url = `http://localhost:5000/escalation/${escalationId}/events`;
        this.eventSource = new EventSource(url);

        this.eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'status') {
                // Handle status updates
                this.handleEscalationStatus(data);
            } else if (data.type === 'message') {
                // Handle new messages
                this.handleEscalationMessage(data);
            }
        };

        this.eventSource.onerror = (error) => {
            console.error('SSE error:', error);
            this.eventSource.close();
            this.displayError('Connection to the agent was lost. Please try again.');
        };
    },

    async submitSentiment(sentiment) {
        try {
            const sentimentButtons = document.querySelectorAll('.chatbot-sentiment-button');
            
            // Disable buttons
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

            // Show temporary thank you message and re-enable after delay
            setTimeout(() => {
                sentimentButtons.forEach(button => {
                    button.classList.remove('disabled');
                });
            }, 3000);

        } catch (error) {
            console.error('Sentiment submission error:', error);
            // Re-enable buttons on error
            sentimentButtons.forEach(button => {
                button.classList.remove('disabled');
            });
        }
    },

    // Handle escalation status updates
    handleEscalationStatus(data) {
        if (data.agent_joined) {
            this.displayMessage('Agent has joined the conversation. You can now chat directly.', 'bot');
        } else {
            this.displayMessage(`Escalation status: ${data.status}`, 'bot');
        }
    },

    // Handle new escalation messages
    // handleEscalationMessage(data) {
    //     this.displayMessage(data.message, data.sender === 'agent' ? 'bot' : 'user', data.id);
    // },

    handleEscalationMessage(data) {
        const messages = document.getElementById('chatbot-messages');
    
        // Check if the message already exists in the UI
        const existingMessage = messages.querySelector(`[data-message-id="${data.id}"]`);
        if (existingMessage) {
            return; // Skip if the message already exists
        }
    
        // Display the new message
        this.displayMessage(data.message, data.sender === 'agent' ? 'bot' : 'user', data.id);
    },

    // Poll escalation status using SSE
    pollEscalationStatus() {
        if (!this.currentEscalationId) {
            console.error('No active escalation to poll status for.');
            return;
        }

        // SSE already handles status updates, so no need for additional polling
        console.log('Polling escalation status via SSE...');
    },

    // Poll escalation messages using SSE
    pollEscalationMessages() {
        if (!this.currentEscalationId) {
            console.error('No active escalation to poll messages for.');
            return;
        }

        // SSE already handles message updates, so no need for additional polling
        console.log('Polling escalation messages via SSE...');
    },

    // Show escalation chat UI
    // showEscalationChat() {
    //     const messages = document.getElementById('chatbot-messages');
    //     messages.innerHTML = `
    //         <div class="chatbot-message bot">
    //             Connecting you to a live agent... Please wait.
    //         </div>
    //     `;

    //     const inputContainer = document.querySelector('.chatbot-input-container');
    //     inputContainer.innerHTML = `
    //         <div class="chatbot-input-wrapper">
    //             <input type="text" 
    //                    id="escalation-input" 
    //                    class="chatbot-input"
    //                    placeholder="Type your message to the agent..."
    //                    autocomplete="off">
    //             <button id="send-to-agent" class="chatbot-send">
    //                 ${document.querySelector('#chatbot-send').innerHTML}
    //             </button>
    //         </div>
    //     `;

    //     // Add event listeners
    //     const input = document.getElementById('escalation-input');
    //     const sendButton = document.getElementById('send-to-agent');

    //     input.addEventListener('keypress', (event) => {
    //         if (event.key === 'Enter') this.sendToAgent();
    //     });

    //     sendButton.addEventListener('click', () => this.sendToAgent());
    // },



    // showEscalationChat() {
    //     const messages = document.getElementById('chatbot-messages');
    //     messages.innerHTML = `
    //         <div class="chatbot-message bot">
    //             Connecting you to a live agent... Please wait.
    //         </div>
    //     `;
    
    //     const inputContainer = document.querySelector('.chatbot-input-container');
    //     inputContainer.innerHTML = `
    //         <div class="chatbot-input-wrapper">
    //             <input type="text" 
    //                    id="escalation-input" 
    //                    class="chatbot-input"
    //                    placeholder="Type your message to the agent..."
    //                    autocomplete="off">
    //             <button id="send-to-agent" class="chatbot-send">
    //                 ${document.querySelector('#chatbot-send').innerHTML}
    //             </button>
    //         </div>
    //     `;
    
    //     // Add event listeners (only once)
    //     const input = document.getElementById('escalation-input');
    //     const sendButton = document.getElementById('send-to-agent');
    
    //     // Remove existing event listeners to avoid duplicates
    //     input.removeEventListener('keypress', this.sendToAgent);
    //     sendButton.removeEventListener('click', this.sendToAgent);
    
    //     // Add new event listeners
    //     input.addEventListener('keypress', (event) => {
    //         if (event.key === 'Enter') this.sendToAgent();
    //     });
    
    //     sendButton.addEventListener('click', () => this.sendToAgent());
    // },



    showEscalationChat() {
        const messages = document.getElementById('chatbot-messages');
        messages.innerHTML = `
            <div class="chatbot-message bot">
                Connecting you to a live agent... Please wait.
            </div>
        `;
    
        const inputContainer = document.querySelector('.chatbot-input-container');
        inputContainer.innerHTML = `
            <div class="chatbot-input-wrapper">
                <input type="text" 
                       id="escalation-input" 
                       class="chatbot-input"
                       placeholder="Type your message to the agent..."
                       autocomplete="off">
                <button id="send-to-agent" class="chatbot-send">
                    ${document.querySelector('#chatbot-send').innerHTML}
                </button>
            </div>
        `;
    
        // Add event listeners (only once)
        const input = document.getElementById('escalation-input');
        const sendButton = document.getElementById('send-to-agent');
    
        // Remove existing event listeners to avoid duplicates
        input.removeEventListener('keypress', this.sendToAgent);
        sendButton.removeEventListener('click', this.sendToAgent);
    
        // Add new event listeners
        input.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') this.sendToAgent();
        });
    
        sendButton.addEventListener('click', () => this.sendToAgent());
    },

    // Send a message to the agent
    // async sendToAgent() {
    //     const input = document.getElementById('escalation-input');
    //     const message = input.value.trim();

    //     if (!message || !this.currentEscalationId || !this.escalationSendUrl) return;

    //     console.log('Sending message to agent:', message); // Debugging log

    //     const sendUrl = `http://localhost:5000/escalation/${this.currentEscalationId}/send`;
    //     try {
            
    //         const response = await fetch(sendUrl, {
    //             method: 'POST',
    //             headers: {
    //                 'Content-Type': 'application/json',
    //                 'User-ID': this.userId,
    //             },
    //             body: JSON.stringify({ message }),
    //         });
    //         console.log('powering:',this.escalationSendUrl);
    //         if (!response.ok) {
    //             throw new Error(`Failed to send message: ${response.status}`);
    //         }

    //         console.log('Message sent successfully:', message); // Debugging log

    //         this.displayMessage(message, 'user');
    //         input.value = '';
    //     } catch (error) {
    //         console.error('Message send error:', error);
    //         this.displayError('Failed to send message');
    //     }
    // },

    async sendToAgent() {
        const input = document.getElementById('escalation-input');
        const message = input.value.trim();
    
        if (!message || !this.currentEscalationId || !this.escalationSendUrl) return;
    
        console.log('Sending message to agent:', message); // Debugging log
    
        const sendUrl = `http://localhost:5000/escalation/${this.currentEscalationId}/send`;
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
            // Debugging log
            // console.log('Message sent successfully:', message); 
            input.value = ''; // Clear the input field
        } catch (error) {
            console.error('Message send error:', error);
            this.displayError('Failed to send message');
        }
    },


    // Display a message in the chat
    displayMessage(message, type, messageId = null) {
        const messages = document.getElementById('chatbot-messages');
        const div = document.createElement('div');
        div.className = `chatbot-message ${type}`;
        if (messageId) div.dataset.messageId = messageId;
        div.textContent = message;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    },

    // Display an error message in the chat
    displayError(message) {
        const messages = document.getElementById('chatbot-messages');
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
                document.getElementById('chatbot-input').focus();
            }
        },
        toggleDropdown() {
            const dropdown = document.getElementById('chatbot-dropdown-menu');
            dropdown.classList.toggle('show');

            // Close dropdown when clicking outside
            const closeDropdown = (event) => {
                if (!event.target.matches('.chatbot-header-actions-button')) {
                    dropdown.classList.remove('show');
                    document.removeEventListener('click', closeDropdown);
                }
            };

            if (dropdown.classList.contains('show')) {
                setTimeout(() => {
                    document.addEventListener('click', closeDropdown);
                }, 0);
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

        async send() {
            const input = document.getElementById('chatbot-input');
            const messages = document.getElementById('chatbot-messages');
            const sendButton = document.getElementById('chatbot-send');
            const question = input.value.trim();
            
            if (!question) return;
            
            try {
                // Disable input and button while sending
                input.disabled = true;
                sendButton.disabled = true;
                
                // Add user message
                messages.innerHTML += `<div class="chatbot-message user">${this.escapeHtml(question)}</div>`;
                input.value = '';
                messages.scrollTop = messages.scrollHeight;
                
                // Show typing indicator
                this.showTyping();
                
                // Send request to backend
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
                
                // Hide typing indicator and show response
                this.hideTyping();
                messages.innerHTML += `<div class="chatbot-message bot">${this.escapeHtml(data.answer)}</div>`;
                
            } catch (error) {
                console.error('Chatbot error:', error);
                this.hideTyping();
                messages.innerHTML += `
                    <div class="chatbot-message error">
                        Sorry, something went wrong. Please try again.
                    </div>
                `;
            } finally {
                // Re-enable input and button
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
            document.getElementById('chatbot-ticket-form').classList.add('chatbot-visible');
        },

        
        closeTicketForm() {
            document.getElementById('chatbot-ticket-form').classList.remove('chatbot-visible');
            // Reset form
            document.getElementById('ticket-subject').value = '';
            document.getElementById('ticket-description').value = '';
            document.getElementById('ticket-priority').value = 'medium';
            document.getElementById('ticket-account').value = '';
        },

        async submitTicket() {
            const subject = document.getElementById('ticket-subject').value.trim();
            const description = document.getElementById('ticket-description').value.trim();
            const priority = document.getElementById('ticket-priority').value;
            const accountDetails = document.getElementById('ticket-account').value.trim();

            if (!subject || !description || !accountDetails) {
                alert('Please fill in all required fields');
                return;
            }

            try {
                const response = await fetch(config.ticketUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'User-ID': this.userId
                    },
                    body: JSON.stringify({
                        subject,
                        description,
                        priority,
                        account_details: accountDetails
                    })
                });

                if (!response.ok) {
                    throw new Error('Failed to create ticket');
                }

                const data = await response.json();
                
                // Add success message to chat
                const messages = document.getElementById('chatbot-messages');
                messages.innerHTML += `
                    <div class="chatbot-message bot">
                        Ticket created successfully! Your ticket ID is: ${data.ticket_id}
                    </div>
                `;
                messages.scrollTop = messages.scrollHeight;

                this.closeTicketForm();
            } catch (error) {
                console.error('Ticket creation error:', error);
                alert('Sorry, we couldn\'t create your ticket. Please try again.');
            }
        },

        escapeHtml(unsafe) {
            return unsafe
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }
    };

    // Add event listeners
    document.getElementById('chatbot-toggle').onclick = () => window.chatbotWidget.toggle();
    

    
    const input = document.getElementById('chatbot-input');
    const sendButton = document.getElementById('chatbot-send');
    
    input.addEventListener('input', () => {
        sendButton.disabled = !input.value.trim();
    });
})();