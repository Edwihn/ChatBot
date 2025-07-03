let selectedCategory = null;
let isTyping = false;

const messagesContainer = document.getElementById('messagesContainer');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const clearChatButton = document.getElementById('clearChat');
const selectedCategorySpan = document.getElementById('selected-category');
const categoryOptions = document.querySelectorAll('.category-option');

document.addEventListener('DOMContentLoaded', function() {
    initializeChatbot();
});

function initializeChatbot() {

    // CATEGORY SELECTION
    categoryOptions.forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            selectCategory(this.textContent);
        });
    });

    // SEND THE MESSAGE
    sendButton.addEventListener('click', function(e) {
        e.preventDefault();
        sendMessage();
    });

    // CLEAR THE CHAT
    clearChatButton.addEventListener('click', function() {
        clearChat();
    });

    messageInput.addEventListener('input', function (e) {
    if (e.target !== messageInput) return; // ONLY VALID IF IS THE CORRECT MESSAGE

    const texto = e.target.value;
    const permitido = /[^\w\s¿?.,'"+áéíóúüÁÉÍÓÚÜñÑ]/g;
    const limpio = texto.replace(permitido, '');
    
    // Evita sobrescribir si no hubo cambios
    if (texto !== limpio) {
        const cursorPos = messageInput.selectionStart;
        e.target.value = limpio;

        // Restaurar posición del cursor para no afectar la escritura
        messageInput.setSelectionRange(cursorPos - 1, cursorPos - 1);
    }
});
}

// Función para seleccionar categoría
function selectCategory(category) {
    selectedCategory = category;
    selectedCategorySpan.textContent = category;
    
    // Habilitar input y botón
    messageInput.disabled = false;
    sendButton.disabled = false;
    messageInput.placeholder = `Escribe tu mensaje sobre ${category}...`;
    messageInput.focus();
    
    // Cerrar dropdown (si usas Flowbite)
    const dropdown = document.getElementById('dropdown');
    if (dropdown) {
        dropdown.classList.add('hidden');
    }
}

// Función para enviar mensaje
async function sendMessage() {
    const message = messageInput.value.trim();
    
    if (!message || !selectedCategory || isTyping) {
        return;
    }

    // Deshabilitar input mientras se procesa
    setInputState(false);
    
    // Mostrar mensaje del usuario
    addUserMessage(message);
    
    // Limpiar input
    messageInput.value = '';
    
    // Mostrar indicador de escritura
    showTypingIndicator();
    
    try {
        // Realizar petición al servidor
        const response = await fetch('/input', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                category: selectedCategory
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // Ocultar indicador de escritura
        hideTypingIndicator();
        
        // Mostrar respuesta del bot
        addBotMessage(data.response);
        
    } catch (error) {
        console.error('Error al enviar mensaje:', error);
        hideTypingIndicator();
    } finally {
        // Rehabilitar input
        setInputState(true);
    }
}

// Función para añadir mensaje del usuario
function addUserMessage(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'flex items-start space-x-3 justify-end';
    
    messageDiv.innerHTML = `
        <div class="bg-blue-600 rounded-lg p-3 max-w-md">
            <p class="text-white">${escapeHtml(message)}</p>
            <span class="text-xs text-blue-200 mt-1 block">${getCurrentTime()}</span>
        </div>
        <div class="flex text-blue-400 text-2xl items-center justify-center flex-shrink-0 mt-1">
            <i class="fa-solid fa-user"></i>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

// Función para añadir mensaje del bot
function addBotMessage(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'flex items-start space-x-3';
    
    messageDiv.innerHTML = `
        <div class="flex text-blue-600 text-3xl items-center justify-center flex-shrink-0 mt-1">
            <i class="fa-solid fa-robot"></i>
        </div>
        <div class="bg-gray-800 rounded-lg p-3 max-w-md">
            <p class="text-white">${escapeHtml(message)}</p>
            <span class="text-xs text-gray-400 mt-1 block">${getCurrentTime()}</span>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

// FUNCTION TO DISPLAY WRITING INDICATOR
function showTypingIndicator() {
    if (document.getElementById('typing-indicator')) return;
    
    isTyping = true;
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typing-indicator';
    typingDiv.className = 'flex items-start space-x-3';
    
    typingDiv.innerHTML = `
        <div class="flex text-blue-600 text-3xl items-center justify-center flex-shrink-0 mt-1">
            <i class="fa-solid fa-robot"></i>
        </div>
        <div class="bg-gray-800 rounded-lg p-3">
            <div class="flex gap-1">
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style="animation-delay: 0.2s"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style="animation-delay: 0.4s"></div>
            </div>
        </div>
    `;
    
    messagesContainer.appendChild(typingDiv);
    scrollToBottom();
}

// FUNCTION TO HIDE WRITING INDICATOR
function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
    isTyping = false;
}

// FUNCTION TO ENABLE/DISABLE INPUT
function setInputState(enabled) {
    messageInput.disabled = !enabled;
    sendButton.disabled = !enabled;
    
    if (enabled) {
        messageInput.focus();
    }
}

// FUNTION TO CLEAR THE CHAT
function clearChat() {
    // Remover todos los mensajes excepto el mensaje de bienvenida
    const messages = messagesContainer.querySelectorAll('div.flex:not(:first-child)');
    messages.forEach(message => message.remove());
    
    // Resetear categoría
    selectedCategory = null;
    selectedCategorySpan.textContent = 'Categorias';
    messageInput.value = null;
    messageInput.placeholder = 'Seleccione una categoria';
    setInputState(false);
}

// FUNTION TO SCROLL TO THE BOTTOM
function scrollToBottom() {
    setTimeout(() => {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }, 100);
}

// FUNCTION TO OBTAIN CURRENT TIME
function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString('es-ES', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

// FUNCTION TO ESCAPE HTML AND PREVENT XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}