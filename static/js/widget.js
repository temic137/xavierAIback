(function() {
    // Get the script tag
    const scriptTag = document.currentScript;
    let apiBase = scriptTag.getAttribute('data-api');
    const chatbotId = scriptTag.getAttribute('data-id');

    // Ensure API base ends with a slash
    if (apiBase && !apiBase.endsWith('/')) {
        apiBase += '/';
    }

    // Log the API base for debugging
    console.log('API Base:', apiBase);
    console.log('Chatbot ID:', chatbotId);

    // Validate required attributes
    if (!apiBase) {
        console.error('Missing data-api attribute in script tag');
    }

    if (!chatbotId) {
        console.error('Missing data-id attribute in script tag');
    }

    // Build API URLs from base
    const urls = {
        ask: `${apiBase}chatbot/${chatbotId}/ask`,
        feedback: `${apiBase}chatbot/${chatbotId}/feedback`,
        sentiment: `${apiBase}/analytics/sentiment/${chatbotId}`,
        ticket: `${apiBase}ticket/create/${chatbotId}`,
        submitLead: `${apiBase}api/leads/submit`
    };

    // Update the config object to include the new settings
    const config = {
        chatbotId: chatbotId,
        name: scriptTag.getAttribute('data-name') || 'Support Agent',
        askUrl: urls.ask,
        feedbackUrl: urls.feedback,
        ticketUrl: urls.ticket,
        avatar: scriptTag.getAttribute('data-avatar') || './assets/agent.png',
        themeColor: scriptTag.getAttribute('data-theme') || '#0066CC',
        sentimentUrl: urls.sentiment,
        submitLeadUrl: urls.submitLead,
        enableTickets: scriptTag.getAttribute('data-enable-tickets') !== 'false', // Default to true
        enableLeads: scriptTag.getAttribute('data-enable-leads') === 'true' // Default to false
    };

    // Apply embedded CSS styles directly
    function loadChatbotStyles() {
        console.log('Applying embedded CSS styles');

        // Create a style element
        const style = document.createElement('style');

        // Add the CSS content directly
        style.textContent = `/* Chatbot Widget Styles */

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
    background: var(--theme-color, #0066CC);
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
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
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
    background: var(--theme-color, #0066CC);
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
    border-radius: 12px;
    box-shadow: 0 6px 24px rgba(0,0,0,0.15);
    min-width: 220px;
    z-index: 1000;
    margin-top: 8px;
    padding: 10px 0;
    border: 1px solid rgba(0,0,0,0.05);
    transform-origin: top right;
    transform: scale(0.95);
    opacity: 0;
    transition: transform 0.3s ease, opacity 0.3s ease;
}

.chatbot-dropdown-menu.show {
    display: block;
    transform: scale(1);
    opacity: 1;
}

.chatbot-dropdown-menu:before {
    content: '';
    position: absolute;
    top: -6px;
    right: 10px;
    width: 12px;
    height: 12px;
    background: white;
    transform: rotate(45deg);
    border-left: 1px solid rgba(0,0,0,0.05);
    border-top: 1px solid rgba(0,0,0,0.05);
}

.chatbot-dropdown-item {
    padding: 12px 16px;
    color: #333;
    text-decoration: none;
    display: flex;
    align-items: center;
    gap: 16px;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 15px;
    border-left: 3px solid transparent;
    margin: 4px 0;
    font-weight: 500;
}

.chatbot-dropdown-item:hover {
    background-color: #f3f4f6;
    border-left-color: var(--theme-color, #0066CC);
}

.chatbot-dropdown-item svg {
    color: var(--theme-color, #0066CC);
    width: 24px;
    height: 24px;
    transition: all 0.3s ease;
    stroke-width: 1.5;
}

.chatbot-dropdown-item:hover svg {
    transform: scale(1.1);
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
    background: var(--theme-color, #0066CC);
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
    color: var(--theme-color, #0066CC);
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
    background: var(--theme-color, #0066CC);
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

.chatbot-lead-form {
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

.chatbot-lead-form.chatbot-visible {
    display: block;
}

.chatbot-ticket-form h3,
.chatbot-lead-form h3 {
    margin: 0 0 8px 0;
    color: var(--theme-color, #0066CC);
    font-size: 20px;
    font-weight: 600;
}

.ticket-form-subtitle,
.lead-form-subtitle {
    color: #666;
    font-size: 14px;
    margin-bottom: 20px;
}

.chatbot-form-group {
    margin-top: 2px;
    margin-bottom: 20px;
}

.chatbot-form-group label {
    display: block;
    margin-bottom: 8px;
    color: #333;
    font-size: 14px;
    font-weight: 500;
}

.chatbot-form-group input,
.chatbot-form-group textarea,
.chatbot-form-group select {
    width: 100%;
    padding: 10px 14px;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 14px;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.chatbot-form-group input:focus,
.chatbot-form-group textarea:focus,
.chatbot-form-group select:focus {
    outline: none;
    border-color: var(--theme-color, #0066CC);
    box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.15);
}

.chatbot-form-group textarea {
    height: 120px;
    resize: vertical;
}

.chatbot-ticket-actions {
    display: flex;
    gap: 12px;
    margin-top: 8px;
}

.chatbot-ticket-submit,
.chatbot-ticket-cancel {
    flex: 1;
    padding: 12px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s ease;
    margin-bottom: 0px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.chatbot-ticket-submit {
    background: var(--theme-color, #0066CC);
    color: white;
}

.chatbot-ticket-submit:hover {
    background: var(--theme-color, #0055AA);
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.chatbot-ticket-cancel {
    background: #f0f0f0;
    color: #333;
}

.chatbot-ticket-cancel:hover {
    background: #e1e1e1;
    transform: translateY(-1px);
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
    border: 1px solid var(--theme-color, #0066CC);
    border-radius: 8px;
    font-size: 14px;
    resize: vertical;
}

.chatbot-feedback-content textarea:focus {
    outline: none;
    border-color: var(--theme-color, #0066CC);
}

.chatbot-feedback-submit {
    width: 100%;
    background: var(--theme-color, #0066CC);
    color: white;
    border: none;
    padding: 12px;
    border-radius: 8px;
    cursor: pointer;
    margin-bottom: 8px;
    font-size: 14px;
    transition: background 0.2s ease;
}

.chatbot-feedback-submit:hover {
    filter: brightness(1.1);
}

.chatbot-feedback-cancel {
    width: 100%;
    background: #e1e1e1;
    color: #333;
    border: none;
    padding: 12px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s ease;
}

.chatbot-feedback-cancel:hover {
    background: #d1d1d1;
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
    width: 24px;
    height: 24px;
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

.chatbot-check-mark {
    color: #22C55E;
    margin-left: 8px;
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
}`;

        // Add the style element to the document head
        document.head.appendChild(style);

        // Set theme color as CSS variable
        document.documentElement.style.setProperty('--theme-color', config.themeColor);

        console.log('CSS styles applied successfully');
    }

    // No fallback needed since CSS is embedded directly

    // Define the initializeWidget function
    function initializeWidget() {
        // Load the CSS
        loadChatbotStyles();

        // Create widget HTML
        const widget = document.createElement('div');
        widget.innerHTML = `
            <div id="chatbot-widget" class="chatbot-container">
                <button id="chatbot-toggle" class="chatbot-toggle" aria-label="Toggle chat">
                    <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
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
                            <button class="chatbot-sentiment-button chatbot-sentiment-positive"
                                    title="Helpful"
                                    aria-label="Mark as helpful">
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                                </svg>
                            </button>
                            <button class="chatbot-sentiment-button chatbot-sentiment-negative"
                                    title="Not Helpful"
                                    aria-label="Mark as not helpful">
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14h-4.764a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.737 3h4.017c.163 0 .326.02.485.06L17 4m-7 10v5a2 2 0 002 2h.095c.5 0 .905-.405.905-.905 0-.714.211-1.412.608-2.006L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
                                </svg>
                            </button>
                        </div>

                        <div class="chatbot-header-dropdown">
                            <button class="chatbot-header-actions-button" aria-label="Menu" id="chatbot-menu-button">
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <circle cx="12" cy="12" r="2"></circle>
                                    <circle cx="12" cy="5" r="2"></circle>
                                    <circle cx="12" cy="19" r="2"></circle>
                                </svg>
                            </button>
                            <div class="chatbot-dropdown-menu" id="chatbot-dropdown-menu">
                                <button class="chatbot-dropdown-item" id="chatbot-ticket-button">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                        <polyline points="14 2 14 8 20 8"></polyline>
                                        <line x1="16" y1="13" x2="8" y2="13"></line>
                                        <line x1="16" y1="17" x2="8" y2="17"></line>
                                        <polyline points="10 9 9 9 8 9"></polyline>
                                    </svg>
                                    <span>Create Support Ticket</span>
                                </button>
                                <button class="chatbot-dropdown-item" id="chatbot-feedback-button">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                                        <line x1="9" y1="10" x2="15" y2="10"></line>
                                        <line x1="9" y1="14" x2="15" y2="14"></line>
                                    </svg>
                                    <span>Provide Feedback</span>
                                </button>
                                <button class="chatbot-dropdown-item" id="chatbot-lead-button">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                                        <circle cx="9" cy="7" r="4"></circle>
                                        <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                                        <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                                    </svg>
                                    <span>Request Information</span>
                                </button>
                            </div>
                        </div>

                        <button class="chatbot-close-chat" aria-label="Close chat">×</button>
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
                                   autocomplete="off">
                            <button id="chatbot-send" class="chatbot-send" disabled aria-label="Send message">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M22 2L11 13M22 2L15 22L11 13M11 13L2 9L22 2"/>
                                </svg>
                            </button>
                        </div>
                    </div>

                    <div class="powered-by">Powered by Xavier AI</div>

                   <!-- Lead Collection Form -->
                   <div id="chatbot-lead-form" class="chatbot-lead-form">
                       <h3>Interested in learning more?</h3>
                       <p class="lead-form-subtitle">Fill out this form and we'll get back to you soon.</p>
                       <div class="chatbot-form-group">
                           <label for="lead-name">Name *</label>
                           <input type="text" id="lead-name" required>
                       </div>
                       <div class="chatbot-form-group">
                           <label for="lead-email">Email *</label>
                           <input type="email" id="lead-email" required>
                       </div>
                       <div class="chatbot-form-group">
                           <label for="lead-phone">Phone</label>
                           <input type="tel" id="lead-phone">
                       </div>
                       <div class="chatbot-form-group">
                           <label for="lead-message">Message</label>
                           <textarea id="lead-message"></textarea>
                       </div>
                       <div class="chatbot-ticket-actions">
                           <button class="chatbot-ticket-submit">Submit</button>
                           <button class="chatbot-ticket-cancel">Cancel</button>
                       </div>
                   </div>

                   <!-- Ticket Form -->
                   <div id="chatbot-ticket-form" class="chatbot-ticket-form">
                        <h3>Create Support Ticket</h3>
                        <p class="ticket-form-subtitle">It might take some time to get a response</p>
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
                            <button class="chatbot-ticket-submit">Submit Ticket</button>
                            <button class="chatbot-ticket-cancel">Cancel</button>
                        </div>
                   </div>
                </div>

                <!-- Feedback Modal -->
                <div id="chatbot-feedback" class="chatbot-feedback-modal">
                    <div class="chatbot-feedback-content">
                        <h3>Provide Feedback</h3>
                        <textarea id="chatbot-feedback-text"
                                 placeholder="Your feedback helps us improve..."></textarea>
                        <button class="chatbot-feedback-submit">Submit</button>
                        <button class="chatbot-feedback-cancel">Cancel</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(widget);

        // Initialize widget functionality
        window.chatbotWidget = {
            userId: 'user_' + Math.random().toString(36).substring(2, 11),
            isTyping: false,
            ticketFormData: {},
            isCreatingTicket: false,
            currentTicketField: null,

            // Helper function to adjust color brightness (kept for potential future use)
            adjustColor(color, amount) {
                const hex = color.replace('#', '');
                const r = Math.max(0, Math.min(255, parseInt(hex.substr(0, 2), 16) + amount));
                const g = Math.max(0, Math.min(255, parseInt(hex.substr(2, 2), 16) + amount));
                const b = Math.max(0, Math.min(255, parseInt(hex.substr(4, 2), 16) + amount));
                return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
            },

            // Escape HTML to prevent XSS
            escapeHtml(unsafe) {
                return unsafe
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;")
                    .replace(/"/g, "&quot;")
                    .replace(/'/g, "&#039;");
            },

            // Toggle the chatbot visibility
            toggle() {
                const content = document.getElementById('chatbot-content');
                const toggle = document.getElementById('chatbot-toggle');
                content.classList.toggle('chatbot-visible');
                toggle.style.display = content.classList.contains('chatbot-visible') ? 'none' : 'flex';
                if (content.classList.contains('chatbot-visible')) {
                    document.getElementById('chatbot-input').focus();
                }
            },

            // Show typing indicator
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

            // Hide typing indicator
            hideTyping() {
                if (!this.isTyping) return;

                this.isTyping = false;
                const typingIndicator = document.getElementById('typing-indicator');
                if (typingIndicator) {
                    typingIndicator.remove();
                }
            },

            // Send a message
            async send() {
                const input = document.getElementById('chatbot-input');
                const messages = document.getElementById('chatbot-messages');
                const sendButton = document.getElementById('chatbot-send');
                const question = input.value.trim();

                if (!question) return;

                // If we're in ticket creation mode, handle the ticket input instead
                if (this.isCreatingTicket && this.currentTicketField) {
                    this.handleTicketInput(this.currentTicketField);
                    return;
                }

                try {
                    input.disabled = true;
                    sendButton.disabled = true;

                    // Display user message
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
                    messages.innerHTML += `<div class="chatbot-message bot">${this.escapeHtml(data.answer)}</div>`;
                    messages.scrollTop = messages.scrollHeight;

                    // Check if the answer indicates the chatbot couldn't resolve the issue
                    const lowerCaseAnswer = data.answer.toLowerCase();
                    if (lowerCaseAnswer.includes("would you like to create a support ticket") ||
                        lowerCaseAnswer.includes("would you like to create a ticket") ||
                        lowerCaseAnswer.includes("i don't have enough information") ||
                        lowerCaseAnswer.includes("i don't have any information") ||
                        lowerCaseAnswer.includes("i couldn't extract any useful information")) {

                        // Wait a moment before asking about ticket creation
                        setTimeout(() => {
                            this.askAboutTicketCreation();
                        }, 1000);
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

            // Submit sentiment feedback
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

            // Open feedback modal
            openFeedback() {
                document.getElementById('chatbot-feedback').classList.add('chatbot-visible');
            },

            // Close feedback modal
            closeFeedback() {
                document.getElementById('chatbot-feedback').classList.remove('chatbot-visible');
                document.getElementById('chatbot-feedback-text').value = '';
            },

            // Submit feedback
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

            // Open ticket form
            openTicketForm() {
                this.ticketFormData = {};
                this.isCreatingTicket = true;
                this.currentTicketField = 'subject';

                const input = document.getElementById('chatbot-input');
                if (!input) {
                    console.error('Input element not found');
                    return;
                }

                input.placeholder = "Type your response...";
                const sendButton = document.getElementById('chatbot-send');
                if (sendButton) {
                    sendButton.disabled = false;
                }

                this.displayMessage("Let's create a ticket to help resolve your issue. First, please enter a subject for your ticket:", "bot");

                // Clear any existing event listeners
                const newInput = input.cloneNode(true);
                input.parentNode.replaceChild(newInput, input);

                // Re-add the input event listener
                newInput.addEventListener('input', () => {
                    const sendBtn = document.getElementById('chatbot-send');
                    if (sendBtn) {
                        sendBtn.disabled = !newInput.value.trim();
                    }
                });

                // Focus the input
                newInput.focus();
            },

            // Handle ticket input
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
                            <span class="chatbot-check-mark">✓</span>
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
                        this.currentTicketField = 'description';
                        this.displayMessage("Great! Now please provide a detailed description of the issue:", "bot");
                        break;

                    case 'description':
                        this.currentTicketField = 'account';
                        this.displayMessage("Finally, please provide your contact details:", "bot");
                        break;

                    case 'account':
                        this.currentTicketField = null;
                        this.isCreatingTicket = false;
                        this.ticketFormData.priority = 'medium';
                        this.displayTicketSummary();
                        break;
                }

                // Focus the input after processing
                input.focus();
            },

            // Get field label
            getFieldLabel(field) {
                const labels = {
                    subject: 'Subject',
                    description: 'Description',
                    priority: 'Priority Level',
                    account: 'Account Details'
                };
                return labels[field] || field;
            },

            // Display ticket summary
            displayTicketSummary() {
                this.displayMessage("Perfect! I've collected all the information needed.", "bot");

                const messages = document.getElementById('chatbot-messages');
                const buttonDiv = document.createElement('div');
                buttonDiv.className = 'chatbot-message bot';
                buttonDiv.style.display = 'flex';
                buttonDiv.style.gap = '10px';
                buttonDiv.innerHTML = `
                    <button class="chatbot-ticket-submit">
                        Submit Ticket
                    </button>
                    <button class="chatbot-ticket-cancel">
                        Cancel
                    </button>
                `;

                // Add event listeners
                const submitButton = buttonDiv.querySelector('.chatbot-ticket-submit');
                const cancelButton = buttonDiv.querySelector('.chatbot-ticket-cancel');

                submitButton.addEventListener('click', () => this.submitTicketForm());
                cancelButton.addEventListener('click', () => this.cancelTicketForm());

                messages.appendChild(buttonDiv);
                messages.scrollTop = messages.scrollHeight;
            },

            // Submit ticket form
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

            // Cancel ticket form
            cancelTicketForm() {
                this.displayMessage("Ticket creation cancelled.", "bot");
                this.resetTicketForm();
            },

            // Reset ticket form
            resetTicketForm() {
                const input = document.getElementById('chatbot-input');
                input.placeholder = "Type your message...";
                this.ticketFormData = {};
                this.isCreatingTicket = false;
                this.currentTicketField = null;
                input.value = '';
                input.focus();

                // Clear any existing event listeners
                const newInput = input.cloneNode(true);
                input.parentNode.replaceChild(newInput, input);

                // Re-add the input event listener
                newInput.addEventListener('input', () => {
                    const sendBtn = document.getElementById('chatbot-send');
                    if (sendBtn) {
                        sendBtn.disabled = !newInput.value.trim();
                    }
                });

                // Re-add the keypress event listener for Enter
                newInput.addEventListener('keypress', (event) => {
                    if (event.key === 'Enter' && !event.shiftKey) {
                        event.preventDefault();
                        window.chatbotWidget.send();
                    }
                });

                // Focus the input
                newInput.focus();
            },

            // Open lead form
            openLeadForm() {
                document.getElementById('chatbot-lead-form').classList.add('chatbot-visible');
            },

            // Close lead form
            closeLeadForm() {
                document.getElementById('chatbot-lead-form').classList.remove('chatbot-visible');
                // Reset form fields
                document.getElementById('lead-name').value = '';
                document.getElementById('lead-email').value = '';
                document.getElementById('lead-phone').value = '';
                document.getElementById('lead-message').value = '';
            },

            // Submit lead form
            async submitLeadForm() {
                const name = document.getElementById('lead-name').value.trim();
                const email = document.getElementById('lead-email').value.trim();
                const phone = document.getElementById('lead-phone').value.trim();
                const message = document.getElementById('lead-message').value.trim();

                if (!name || !email) {
                    alert('Please fill in all required fields (Name and Email)');
                    return;
                }

                // Validate email format
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(email)) {
                    alert('Please enter a valid email address');
                    return;
                }

                try {
                    const response = await fetch(config.submitLeadUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            name: name,
                            email: email,
                            phone: phone || null,
                            message: message || null,
                            chatbot_id: config.chatbotId
                        })
                    });

                    if (!response.ok) {
                        throw new Error('Failed to submit lead');
                    }

                    this.closeLeadForm();
                    this.displayMessage('Thank you for your interest! We will contact you soon.', 'bot');
                } catch (error) {
                    console.error('Lead submission error:', error);
                    alert('Sorry, we couldn\'t submit your information. Please try again.');
                }
            },

            // Ask the user if they want to create a ticket
            askAboutTicketCreation() {
                const messages = document.getElementById('chatbot-messages');

                // Create a message with buttons
                const messageDiv = document.createElement('div');
                messageDiv.className = 'chatbot-message bot';
                messageDiv.innerHTML = `
                    <p>Would you like to create a support ticket so a human agent can help you with this?</p>
                    <div style="display: flex; gap: 12px; margin-top: 12px;">
                        <button class="ticket-yes-btn" style="background: var(--theme-color, #0066CC); color: white; border: none; padding: 10px 16px; border-radius: 8px; cursor: pointer; font-weight: 500; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: all 0.2s ease;">Yes, create a ticket</button>
                        <button class="ticket-no-btn" style="background: #f0f0f0; color: #333; border: none; padding: 10px 16px; border-radius: 8px; cursor: pointer; font-weight: 500; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: all 0.2s ease;">No, thanks</button>
                    </div>
                `;

                // Add event listeners to the buttons
                const yesButton = messageDiv.querySelector('.ticket-yes-btn');
                const noButton = messageDiv.querySelector('.ticket-no-btn');

                yesButton.addEventListener('click', () => {
                    // Remove the buttons to prevent multiple clicks
                    yesButton.remove();
                    noButton.remove();

                    // Start the ticket creation process
                    this.openTicketForm();
                });

                noButton.addEventListener('click', () => {
                    // Remove the buttons to prevent multiple clicks
                    yesButton.remove();
                    noButton.remove();

                    // Acknowledge the user's choice
                    this.displayMessage("Okay, let me know if you need anything else!", "bot");
                });

                // Add the message to the chat
                messages.appendChild(messageDiv);
                messages.scrollTop = messages.scrollHeight;
            },

            // Display a message in the chat
            displayMessage(message, type) {
                const messages = document.getElementById('chatbot-messages');
                const div = document.createElement('div');
                div.className = `chatbot-message ${type}`;
                div.textContent = message;
                messages.appendChild(div);
                messages.scrollTop = messages.scrollHeight;
            }
        };

        // Add event listeners
        document.getElementById('chatbot-toggle').addEventListener('click', () => window.chatbotWidget.toggle());
        document.getElementById('chatbot-send').addEventListener('click', () => window.chatbotWidget.send());
        document.querySelector('.chatbot-close-chat').addEventListener('click', () => window.chatbotWidget.toggle());

        // Dropdown menu functionality
        document.getElementById('chatbot-menu-button').addEventListener('click', () => {
            document.getElementById('chatbot-dropdown-menu').classList.toggle('show');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.chatbot-header-dropdown') &&
                document.getElementById('chatbot-dropdown-menu').classList.contains('show')) {
                document.getElementById('chatbot-dropdown-menu').classList.remove('show');
            }
        });

        // Menu item event listeners
        document.getElementById('chatbot-ticket-button').addEventListener('click', () => {
            document.getElementById('chatbot-dropdown-menu').classList.remove('show');
            window.chatbotWidget.openTicketForm();
        });

        document.getElementById('chatbot-feedback-button').addEventListener('click', () => {
            document.getElementById('chatbot-dropdown-menu').classList.remove('show');
            window.chatbotWidget.openFeedback();
        });

        document.getElementById('chatbot-lead-button').addEventListener('click', () => {
            document.getElementById('chatbot-dropdown-menu').classList.remove('show');
            window.chatbotWidget.openLeadForm();
        });

        // Sentiment buttons
        document.querySelector('.chatbot-sentiment-button.chatbot-sentiment-positive').addEventListener('click', () => window.chatbotWidget.submitSentiment(true));
        document.querySelector('.chatbot-sentiment-button.chatbot-sentiment-negative').addEventListener('click', () => window.chatbotWidget.submitSentiment(false));

        // Feedback form buttons
        document.querySelector('.chatbot-feedback-submit').addEventListener('click', () => window.chatbotWidget.submitFeedback());
        document.querySelector('.chatbot-feedback-cancel').addEventListener('click', () => window.chatbotWidget.closeFeedback());

        // Lead form buttons
        document.querySelector('.chatbot-lead-form .chatbot-ticket-submit').addEventListener('click', () => window.chatbotWidget.submitLeadForm());
        document.querySelector('.chatbot-lead-form .chatbot-ticket-cancel').addEventListener('click', () => window.chatbotWidget.closeLeadForm());

        // Input event listeners
        const input = document.getElementById('chatbot-input');
        const sendButton = document.getElementById('chatbot-send');

        input.addEventListener('input', () => {
            sendButton.disabled = !input.value.trim();
        });

        input.addEventListener('keypress', (event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                window.chatbotWidget.send();
            }
        });
    }

    // Initialize the widget when the DOM is fully loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeWidget);
    } else {
        initializeWidget();
    }
})();
