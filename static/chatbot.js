// ISRO Space Assistant Chat Interface
document.addEventListener('DOMContentLoaded', () => {
    const sendBtn = document.getElementById('send-btn');
    const micBtn = document.getElementById('mic-btn');
    const userInput = document.getElementById('user-input');
    const chatWindow = document.getElementById('chat-window');
    const chatForm = document.getElementById('chat-form');
    const clearChatBtn = document.querySelector('.clear-chat');
      let recognition = null;
    let wasVoiceQuery = false;
    let currentlySpeaking = false;
    let typingIndicator = document.querySelector('.typing-indicator');
    
    // Initialize speech synthesis
    const synthesis = window.speechSynthesis;
    let voiceList = [];
    
    // Get available voices
    function loadVoices() {
        voiceList = synthesis.getVoices();
    }
    
    if (synthesis.onvoiceschanged !== undefined) {
        synthesis.onvoiceschanged = loadVoices;
    }
    
    // Speak the response
    function speakResponse(text) {
        // Clean up the text for better speech
        const cleanText = text
            .replace(/-/g, '') // Remove bullet points
            .replace(/\n/g, '. ') // Replace newlines with periods
            .replace(/\s+/g, ' ') // Remove extra spaces
            .trim();
            
        const utterance = new SpeechSynthesisUtterance(cleanText);
        
        // Try to find an Indian English voice, fallback to any English voice
        let voice = voiceList.find(v => v.lang === 'en-IN') || 
                   voiceList.find(v => v.lang === 'en-GB') ||
                   voiceList.find(v => v.lang === 'en-US');
        
        if (voice) {
            utterance.voice = voice;
        }
        
        utterance.rate = 1;
        utterance.pitch = 1;
        
        utterance.onstart = () => {
            currentlySpeaking = true;
            micBtn.disabled = true;
        };
        
        utterance.onend = () => {
            currentlySpeaking = false;
            micBtn.disabled = false;
        };
        
        synthesis.speak(utterance);
    }
    
    // Initialize speech recognition
    try {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.lang = 'en-US';
        
        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            userInput.value = transcript;
            micBtn.classList.remove('listening');
            wasVoiceQuery = true;
            // Auto-submit after voice input
            chatForm.dispatchEvent(new Event('submit'));
        };
        
        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            micBtn.classList.remove('listening');
            wasVoiceQuery = false;
        };
        
        recognition.onend = () => {
            micBtn.classList.remove('listening');
            userInput.placeholder = 'Ask anything about ISRO and space exploration...';
        };
        
        // Enable mic button if speech recognition is available
        micBtn.disabled = false;
    } catch(e) {
        console.warn('Speech recognition not supported:', e);
        micBtn.disabled = true;
        micBtn.title = 'Speech recognition is not supported in your browser';
    }
    
    // Handle mic button click
    micBtn.addEventListener('click', () => {
        // Stop speaking if currently speaking
        if (currentlySpeaking) {
            synthesis.cancel();
            currentlySpeaking = false;
            micBtn.classList.remove('listening');
            return;
        }
        
        // Start listening
        if (recognition) {
            if (micBtn.classList.contains('listening')) {
                recognition.stop();
                micBtn.classList.remove('listening');
            } else {
                recognition.start();
                micBtn.classList.add('listening');
                userInput.placeholder = 'Listening...';
            }
        }
    });

    // Auto-resize textarea
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });    // Helper functions and components will be initialized later// Initialize chat interface immediately
    if (!chatWindow.querySelector('.chat-start')) {
        clearChatBtn.click();
    }

    // Format bot message content
    function formatBotMessage(content) {
        let formatted = content;
        // Convert markdown-style code blocks
        formatted = formatted.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
        // Convert inline code
        formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
        // Convert bullets
        formatted = formatted.replace(/^- (.+)$/gm, '• $1');
        // Convert URLs to links
        formatted = formatted.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
        // Add paragraph breaks
        formatted = formatted.split('\n').map(line => line.trim()).filter(line => line).join('</p><p>');
        return `<p>${formatted}</p>`;
    }

    // Add message to chat
    function addMessage(content, isUser = false) {
        // Remove welcome screen if present
        const welcomeScreen = chatWindow.querySelector('.chat-start');
        if (welcomeScreen) {
            welcomeScreen.remove();
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        
        const innerDiv = document.createElement('div');
        innerDiv.className = 'message-inner';
        
        const formattedContent = isUser ? content : formatBotMessage(content);
        innerDiv.innerHTML = `<div class="message-content">${formattedContent}</div>`;
        messageDiv.appendChild(innerDiv);
        
        chatWindow.appendChild(messageDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    // Show typing indicator
    function showTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = '<div class="message-inner"><div class="dots"><span></span><span></span><span></span></div></div>';
        chatWindow.appendChild(indicator);
        chatWindow.scrollTop = chatWindow.scrollHeight;
        return indicator;
    }

    // Add welcome screen
    function addWelcomeScreen() {
        const welcomeScreen = document.createElement('div');
        welcomeScreen.className = 'welcome-screen';
        welcomeScreen.innerHTML = `
            <img src="/static/isro_logo.svg" alt="ISRO Logo" class="welcome-logo">
            <h1>ISRO Space Assistant</h1>
            <p>Your guide to Indian space exploration. Ask me anything about ISRO, space missions, satellites, and more.</p>
        `;
        chatWindow.appendChild(welcomeScreen);
    }    // Handle message submission
    async function handleSubmit(e) {
        e.preventDefault();
        const message = userInput.value.trim();
        if (!message) return;

        // Add user message
        addMessage(message, true);
        
        // Clear input and reset height
        userInput.value = '';
        userInput.style.height = 'auto';
        
        // Show typing indicator
        typingIndicator.style.display = 'inline-flex';
        chatWindow.scrollTop = chatWindow.scrollHeight;

        // Stop any ongoing speech
        if (currentlySpeaking) {
            synthesis.cancel();
            currentlySpeaking = false;
        }

        // Show typing indicator
        const indicator = showTypingIndicator();        try {
            const response = await fetch('/stream_response', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message }),
            });

            if (!response.ok) throw new Error('Network response was not ok');

            // Create a message container for the streaming response            // Create message container and typing indicator
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message bot-message';
            const innerDiv = document.createElement('div');
            innerDiv.className = 'message-inner';
            
            // Add typing indicator inside the message
            const typingDiv = document.createElement('div');
            typingDiv.className = 'typing-indicator';
            for (let i = 0; i < 3; i++) {
                const dot = document.createElement('div');
                dot.className = 'typing-dot';
                typingDiv.appendChild(dot);
            }
            innerDiv.appendChild(typingDiv);
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.style.display = 'none'; // Hide content div initially
            innerDiv.appendChild(contentDiv);
            messageDiv.appendChild(innerDiv);
            chatWindow.appendChild(messageDiv);

            // Hide the global typing indicator
            typingIndicator.style.display = 'none';

            // Handle the streaming response
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let responseText = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const token = line.slice(6);
                        if (token && responseText === '') {
                            // When first token arrives, show content and hide typing
                            typingDiv.style.display = 'none';
                            contentDiv.style.display = 'block';
                        }
                        responseText += token;
                        contentDiv.innerHTML = formatBotMessage(responseText);
                    }
                }
                chatWindow.scrollTop = chatWindow.scrollHeight;
            }

            // Speak the response if it was a voice query
            if (wasVoiceQuery) {
                speakResponse(responseText);
                wasVoiceQuery = false;
            }        } catch (error) {
            console.error('Error:', error);
            typingIndicator.style.display = 'none';
            const errorMsg = 'Sorry, I encountered an error while processing your request. Please try again.';
            addMessage(errorMsg);
            if (wasVoiceQuery) {
                speakResponse(errorMsg);
                wasVoiceQuery = false;
            }
        }
    }    // Submit prompt function
    function submitPrompt(text) {
        userInput.value = text;
        const event = new Event('submit');
        chatForm.dispatchEvent(event);
    }
    window.submitPrompt = submitPrompt;


    // Handle form submission
    chatForm.addEventListener('submit', handleSubmit);
    
    // Handle Enter key
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    // Clear chat history
    clearChatBtn.addEventListener('click', () => {
        chatWindow.innerHTML = '';
        // Stop any ongoing speech
        if (currentlySpeaking) {
            synthesis.cancel();
            currentlySpeaking = false;
        }
        const welcomeHtml = `
            <div class="chat-start">
                <h1>ISRO Space Assistant</h1>
                <div class="example-prompts">
                    <div class="prompt-category">
                        <h3>Popular Topics</h3>
                        <div class="prompt-items">
                            <button class="prompt-btn" onclick="submitPrompt('Tell me about ISRO and its main objectives')">
                                <i class="bi bi-rocket-takeoff"></i>
                                <span>About ISRO</span>
                            </button>
                            <button class="prompt-btn" onclick="submitPrompt('What are ISROs major achievements?')">
                                <i class="bi bi-trophy"></i>
                                <span>Major Achievements</span>
                            </button>
                        </div>
                    </div>
                    <div class="prompt-category">
                        <h3>Current Missions</h3>
                        <div class="prompt-items">
                            <button class="prompt-btn" onclick="submitPrompt('Tell me about Chandrayaan-3 mission and its achievements')">
                                <i class="bi bi-moon-stars"></i>
                                <span>Chandrayaan-3 Mission</span>
                            </button>
                            <button class="prompt-btn" onclick="submitPrompt('What is Aditya L1 mission and its objectives?')">
                                <i class="bi bi-sun"></i>
                                <span>Aditya-L1 Solar Mission</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        chatWindow.innerHTML = welcomeHtml;
    });

    // Initialize with welcome screen
    if (!chatWindow.querySelector('.chat-start')) {
        clearChatBtn.click();
    }
});
