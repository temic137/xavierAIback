/**
 * Modern Chatbot Navbar Enhancement Script
 * This script enhances the chatbot navbar with modern styling and Font Awesome icons
 */

document.addEventListener('DOMContentLoaded', function() {
    // Function to enhance the dropdown menu with Font Awesome icons
    function enhanceChatbotNavbar() {
        // Wait for the chatbot widget to be fully loaded
        const checkInterval = setInterval(() => {
            const dropdownMenu = document.getElementById('chatbot-dropdown-menu');
            const menuButton = document.querySelector('.chatbot-header-actions-button');
            
            if (dropdownMenu && menuButton) {
                clearInterval(checkInterval);
                
                // Replace the menu button icon with a better Font Awesome icon
                if (menuButton.querySelector('svg')) {
                    menuButton.innerHTML = '<i class="fas fa-ellipsis-v"></i>';
                }
                
                // Update the dropdown menu items with Font Awesome icons
                const dropdownItems = dropdownMenu.querySelectorAll('.chatbot-dropdown-item');
                
                dropdownItems.forEach(item => {
                    const text = item.querySelector('span')?.textContent.trim();
                    
                    // Remove existing SVG or emoji
                    const svg = item.querySelector('svg');
                    if (svg) svg.remove();
                    
                    // Add appropriate Font Awesome icon based on the item text
                    if (text && text.includes('Ticket')) {
                        item.innerHTML = '<i class="fas fa-ticket-alt"></i><span>Create Ticket</span>';
                    } else if (text && text.includes('Feedback')) {
                        item.innerHTML = '<i class="fas fa-comment-dots"></i><span>Provide Feedback</span>';
                    } else if (text && text.includes('Information')) {
                        item.innerHTML = '<i class="fas fa-user-plus"></i><span>Request Information</span>';
                    } else if (text && text.includes('Escalate')) {
                        item.innerHTML = '<i class="fas fa-headset"></i><span>Escalate to Agent</span>';
                    }
                });
                
                // Replace the close button with a better icon
                const closeButton = document.querySelector('.chatbot-close-chat');
                if (closeButton) {
                    closeButton.innerHTML = '<i class="fas fa-times"></i>';
                }
            }
        }, 500);
    }

    // Initialize the enhancement
    enhanceChatbotNavbar();
    
    // Also run when the toggle button is clicked (in case the chatbot is loaded later)
    document.addEventListener('click', function(e) {
        if (e.target.closest('.chatbot-toggle')) {
            setTimeout(enhanceChatbotNavbar, 300);
        }
    });
});
