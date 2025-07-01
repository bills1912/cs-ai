// static/js/chat.js

class ChatApp {
    constructor() {
        this.sessionId = null;
        this.isTyping = false;
        this.currentRating = 0;
        this.messagesContainer = document.getElementById('messagesContainer');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.loadingScreen = document.getElementById('loadingScreen');
        
        this.init();
    }
    
    init() {
        console.log('🚚 FastDelivery Express Chatbot initializing...');
        this.setupEventListeners();
        this.setupRatingModal();
        this.hideLoadingScreen();
        this.fixInitialLayout();
    }
    
    fixInitialLayout() {
        // Pastikan modal tersembunyi
        const modal = document.getElementById('ratingModal');
        if (modal) {
            modal.classList.remove('show');
            modal.style.display = 'none';
        }
        
        // Fix body overflow
        document.body.style.overflow = '';
        
        // Center layout fixes
        const appContainer = document.querySelector('.app-container');
        if (appContainer) {
            appContainer.style.display = 'flex';
            appContainer.style.alignItems = 'center';
            appContainer.style.justifyContent = 'center';
            appContainer.style.minHeight = '100vh';
        }
        
        const chatWrapper = document.querySelector('.chat-wrapper');
        if (chatWrapper) {
            chatWrapper.style.margin = '0 auto';
            chatWrapper.style.maxWidth = '1400px';
        }
    }
    
    setupEventListeners() {
        // Send message on Enter key
        if (this.messageInput) {
            this.messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }
        
        // Send button click
        if (this.sendBtn) {
            this.sendBtn.addEventListener('click', () => this.sendMessage());
        }
        
        // ESC key untuk close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeRatingModal();
            }
        });
    }
    
    setupRatingModal() {
        const ratingStars = document.querySelectorAll('#ratingStars i');
        ratingStars.forEach((star, index) => {
            star.addEventListener('click', () => {
                this.currentRating = index + 1;
                this.updateRatingStars();
            });
            
            star.addEventListener('mouseenter', () => {
                this.highlightStars(index + 1);
            });
        });
        
        const ratingContainer = document.getElementById('ratingStars');
        if (ratingContainer) {
            ratingContainer.addEventListener('mouseleave', () => {
                this.updateRatingStars();
            });
        }
        
        // Close modal when clicking outside
        const modal = document.getElementById('ratingModal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeRatingModal();
                }
            });
        }
    }
    
    hideLoadingScreen() {
        if (this.loadingScreen) {
            setTimeout(() => {
                this.loadingScreen.style.opacity = '0';
                setTimeout(() => {
                    this.loadingScreen.style.display = 'none';
                }, 500);
            }, 1500);
        }
    }
    
    async sendMessage() {
        if (!this.messageInput || !this.messagesContainer) {
            console.error('❌ Required elements not found');
            return;
        }
        
        const message = this.messageInput.value.trim();
        if (!message || this.isTyping) return;
        
        console.log('📤 Sending message:', message);
        
        // Add user message to chat UI
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            const response = await fetch('/api/send-message/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId
                })
            });
            
            const data = await response.json();
            
            if (response.ok && data.status === 'success') {
                this.sessionId = data.session_id;
                
                // Realistic typing delay
                const typingDelay = Math.min(Math.max(data.response.length * 30, 1000), 3000);
                
                setTimeout(() => {
                    this.hideTypingIndicator();
                    this.addMessage(data.response, 'bot');
                    
                    // Check if response contains rating request - tapi jangan auto-show modal
                    if (data.response.toLowerCase().includes('rating') || 
                        data.response.toLowerCase().includes('bintang')) {
                        setTimeout(() => this.showRatingPrompt(), 1000);
                    }
                }, typingDelay);
                
                console.log('✅ Message sent successfully');
            } else {
                this.hideTypingIndicator();
                const errorMsg = data.error || 'Terjadi kesalahan. Silakan coba lagi.';
                const fallbackMsg = data.fallback_response || errorMsg;
                this.addMessage(fallbackMsg, 'bot');
                this.showToast('Error', errorMsg, 'error');
                console.error('❌ Server error:', data);
            }
        } catch (error) {
            this.hideTypingIndicator();
            console.error('❌ Network error:', error);
            
            const fallbackMessage = `🔌 **Koneksi Bermasalah**
            
Sepertinya ada masalah koneksi. Silakan:
1. 🔄 Periksa koneksi internet
2. 🔁 Refresh halaman  
3. 📞 Hubungi 1500-888 jika masalah berlanjut

Maaf atas ketidaknyamanan ini. 🙏`;
            
            this.addMessage(fallbackMessage, 'bot');
            this.showToast('Koneksi Error', 'Periksa koneksi internet Anda', 'error');
        }
    }
    
    addMessage(content, sender) {
        if (!this.messagesContainer) return;
        
        // Remove welcome message if exists
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage && sender === 'user') {
            welcomeMessage.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => welcomeMessage.remove(), 300);
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = sender === 'user' ? 
            '<i class="fas fa-user"></i>' : 
            '<i class="fas fa-robot"></i>';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Format message content
        const formattedContent = this.formatMessage(content);
        messageContent.innerHTML = formattedContent;
        
        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = new Date().toLocaleTimeString('id-ID', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        messageContent.appendChild(messageTime);
        
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Add entrance animation
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(20px)';
        setTimeout(() => {
            messageDiv.style.transition = 'all 0.3s ease';
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        }, 50);
    }
    
    formatMessage(content) {
        let formatted = content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
        
        // Format tracking numbers
        formatted = formatted.replace(/([A-Z]{2,3}[0-9]{8,12})/g, 
            '<span class="tracking-number">$1</span>');
        
        // Format phone numbers
        formatted = formatted.replace(/(1500-\d{3}|\d{4}-\d{3})/g, 
            '<span style="font-weight: bold; color: #667eea;">$1</span>');
        
        return formatted;
    }
    
    showTypingIndicator() {
        this.isTyping = true;
        if (this.typingIndicator) {
            this.typingIndicator.classList.add('show');
            this.scrollToBottom();
        }
    }
    
    hideTypingIndicator() {
        this.isTyping = false;
        if (this.typingIndicator) {
            this.typingIndicator.classList.remove('show');
        }
    }
    
    scrollToBottom() {
        if (this.messagesContainer) {
            setTimeout(() => {
                this.messagesContainer.scrollTo({
                    top: this.messagesContainer.scrollHeight,
                    behavior: 'smooth'
                });
            }, 100);
        }
    }
    
    showRatingPrompt() {
        // Show rating buttons in chat instead of modal popup
        const ratingPrompt = `⭐ **Berikan Rating Pelayanan**

Bagaimana pengalaman Anda dengan layanan kami?

<div class="inline-rating-buttons">
    <button onclick="chatApp.submitQuickRating(5)" class="rating-btn excellent">5⭐ Sangat Puas</button>
    <button onclick="chatApp.submitQuickRating(4)" class="rating-btn good">4⭐ Puas</button>
    <button onclick="chatApp.submitQuickRating(3)" class="rating-btn average">3⭐ Cukup</button>
    <button onclick="chatApp.submitQuickRating(2)" class="rating-btn poor">2⭐ Kurang</button>
    <button onclick="chatApp.submitQuickRating(1)" class="rating-btn bad">1⭐ Buruk</button>
</div>

Atau <button onclick="chatApp.showRatingModal()" class="text-link">buka form rating lengkap</button> untuk memberikan komentar.`;
        
        this.addMessage(ratingPrompt, 'bot');
    }
    
    showRatingModal() {
        const modal = document.getElementById('ratingModal');
        if (modal) {
            modal.style.display = 'flex';
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
            
            // Reset rating
            this.currentRating = 0;
            this.updateRatingStars();
            
            // Clear comment
            const comment = document.getElementById('ratingComment');
            if (comment) {
                comment.value = '';
            }
        }
    }
    
    closeRatingModal() {
        const modal = document.getElementById('ratingModal');
        if (modal) {
            modal.classList.remove('show');
            setTimeout(() => {
                modal.style.display = 'none';
            }, 300);
            document.body.style.overflow = '';
            this.currentRating = 0;
            this.updateRatingStars();
            
            const comment = document.getElementById('ratingComment');
            if (comment) {
                comment.value = '';
            }
        }
    }
    
    updateRatingStars() {
        const stars = document.querySelectorAll('#ratingStars i');
        stars.forEach((star, index) => {
            if (index < this.currentRating) {
                star.classList.add('active');
            } else {
                star.classList.remove('active');
            }
        });
    }
    
    highlightStars(rating) {
        const stars = document.querySelectorAll('#ratingStars i');
        stars.forEach((star, index) => {
            if (index < rating) {
                star.style.color = '#ffc107';
                star.style.transform = 'scale(1.2)';
            } else {
                star.style.color = '#ddd';
                star.style.transform = 'scale(1)';
            }
        });
    }
    
    async submitQuickRating(rating) {
        try {
            const response = await fetch('/api/submit-rating/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    rating: rating,
                    comment: '',
                    session_id: this.sessionId
                })
            });
            
            const data = await response.json();
            
            if (response.ok && data.status === 'success') {
                this.addMessage(data.response, 'bot');
                this.showToast('Terima Kasih!', `Rating ${rating} bintang telah dikirim`, 'success');
            } else {
                this.showToast('Error', 'Gagal mengirim rating', 'error');
            }
        } catch (error) {
            console.error('Rating submission error:', error);
            this.showToast('Error', 'Koneksi bermasalah', 'error');
        }
    }
    
    async submitRating() {
        if (this.currentRating === 0) {
            this.showToast('Peringatan', 'Silakan pilih rating terlebih dahulu', 'error');
            return;
        }
        
        const comment = document.getElementById('ratingComment');
        const commentText = comment ? comment.value : '';
        
        try {
            const response = await fetch('/api/submit-rating/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    rating: this.currentRating,
                    comment: commentText,
                    session_id: this.sessionId
                })
            });
            
            const data = await response.json();
            
            if (response.ok && data.status === 'success') {
                this.closeRatingModal();
                this.addMessage(data.response, 'bot');
                this.showToast('Terima Kasih!', `Rating ${this.currentRating} bintang telah dikirim`, 'success');
            } else {
                this.showToast('Error', 'Gagal mengirim rating', 'error');
            }
        } catch (error) {
            console.error('Rating submission error:', error);
            this.showToast('Error', 'Koneksi bermasalah', 'error');
        }
    }
    
    showToast(title, message, type = 'success') {
        const toastContainer = document.getElementById('toastContainer') || this.createToastContainer();
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = type === 'success' ? 'fa-check' : 'fa-exclamation-triangle';
        
        toast.innerHTML = `
            <div class="toast-icon">
                <i class="fas ${icon}"></i>
            </div>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Auto remove after 4 seconds
        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
    
    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1100;
        `;
        document.body.appendChild(container);
        return container;
    }
    
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
}


// Global functions for template
function sendQuickMessage(message) {
    if (window.chatApp && window.chatApp.messageInput) {
        window.chatApp.messageInput.value = message;
        window.chatApp.sendMessage();
    }
}

function insertSuggestion(text) {
    if (window.chatApp && window.chatApp.messageInput) {
        window.chatApp.messageInput.value = text;
        window.chatApp.messageInput.focus();
    }
}

function closeRatingModal() {
    if (window.chatApp) {
        window.chatApp.closeRatingModal();
    }
}

function submitRating() {
    if (window.chatApp) {
        window.chatApp.submitRating();
    }
}

// Initialize chat app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎉 DOM loaded, starting ChatApp...');
    window.chatApp = new ChatApp();
    
    // Add loading animations
    const elements = document.querySelectorAll('.chat-container, .side-panel');
    elements.forEach((el, index) => {
        if (el) {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            setTimeout(() => {
                el.style.transition = 'all 0.6s ease';
                el.style.opacity = '1';
                el.style.transform = 'translateY(0)';
            }, 1800 + (index * 200));
        }
    });
});

// Add CSS for special elements
const ratingButtonsCSS = `
.inline-rating-buttons {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin: 15px 0;
    align-items: center;
}

.rating-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 20px;
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.3s ease;
    font-weight: 500;
    min-width: 150px;
    text-align: center;
}

.rating-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
}

.rating-btn.excellent {
    background: linear-gradient(135deg, #4CAF50, #45a049);
}

.rating-btn.good {
    background: linear-gradient(135deg, #8BC34A, #689F38);
}

.rating-btn.average {
    background: linear-gradient(135deg, #FFC107, #FF8F00);
}

.rating-btn.poor {
    background: linear-gradient(135deg, #FF9800, #F57C00);
}

.rating-btn.bad {
    background: linear-gradient(135deg, #F44336, #D32F2F);
}

.text-link {
    background: none;
    border: none;
    color: #667eea;
    text-decoration: underline;
    cursor: pointer;
    font-size: inherit;
    padding: 0;
}

.text-link:hover {
    color: #764ba2;
}

@media (max-width: 480px) {
    .inline-rating-buttons {
        gap: 6px;
    }
    
    .rating-btn {
        font-size: 0.8rem;
        padding: 8px 16px;
        min-width: 130px;
    }
}
`;

const additionalCSS = `
.tracking-number {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    padding: 2px 8px;
    border-radius: 12px;
    font-weight: 600;
    font-family: 'Courier New', monospace;
    font-size: 0.85em;
}

.toast {
    background: white;
    border-radius: 12px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    padding: 15px 20px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 300px;
    animation: slideInRight 0.3s ease;
    border-left: 4px solid #4CAF50;
}

.toast.error {
    border-left-color: #F44336;
}

.toast-icon {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 0.8rem;
}

.toast.success .toast-icon {
    background: #4CAF50;
}

.toast.error .toast-icon {
    background: #F44336;
}

.toast-content {
    flex: 1;
}

.toast-title {
    font-weight: 600;
    font-size: 0.9rem;
    margin-bottom: 2px;
}

.toast-message {
    font-size: 0.8rem;
    color: #6c757d;
}

@keyframes slideInRight {
    from {
        opacity: 0;
        transform: translateX(100%);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes slideOutRight {
    to {
        opacity: 0;
        transform: translateX(100%);
    }
}

@keyframes fadeOut {
    to {
        opacity: 0;
        transform: translateY(-20px);
    }
}
`;

// Inject additional CSS
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalCSS;
document.head.appendChild(styleSheet);

const ratingStyleSheet = document.createElement('style');
ratingStyleSheet.textContent = ratingButtonsCSS;
document.head.appendChild(ratingStyleSheet);

document.addEventListener('DOMContentLoaded', function () {
    // Ensure modal is hidden on load
    const modal = document.getElementById('ratingModal');
    if (modal) {
        modal.classList.remove('show');
        modal.style.display = 'none';
    }

    // Fix body overflow
    document.body.style.overflow = '';
});

// Export for debugging
window.testChatApp = () => {
    console.log('🧪 Testing chat app...');
    console.log('ChatApp instance:', window.chatApp);
    console.log('Message input:', document.getElementById('messageInput'));
    console.log('Send button:', document.getElementById('sendBtn'));
    console.log('CSRF token:', window.chatApp?.getCSRFToken());
};

console.log('🚚 FastDelivery Express Chatbot script loaded!');