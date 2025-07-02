// Variables globales
let selectedCategory = null;
let isTyping = false;

// Referencias a elementos DOM
const messagesContainer = document.getElementById('messagesContainer');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const clearChatButton = document.getElementById('clearChat');
const selectedCategorySpan = document.getElementById('selected-category');
const categoryOptions = document.querySelectorAll('.category-option');



// Inicialización cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    initializeChatbot();
});


// Función de inicialización
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
    if (e.target !== messageInput) return; // ONLY VALID IF IS THE CORRECT INPUT

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
        addBotMessage('Lo siento, hubo un error al procesar tu mensaje. Por favor, inténtalo de nuevo.');
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

// Función para mostrar indicador de escritura
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
            <div class="flex space-x-1">
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style="animation-delay: 0.2s"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style="animation-delay: 0.4s"></div>
            </div>
        </div>
    `;
    
    messagesContainer.appendChild(typingDiv);
    scrollToBottom();
}

// Función para ocultar indicador de escritura
function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
    isTyping = false;
}

// Función para habilitar/deshabilitar input
function setInputState(enabled) {
    messageInput.disabled = !enabled;
    sendButton.disabled = !enabled;
    
    if (enabled) {
        messageInput.focus();
    }
}

// Función para limpiar el chat
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

// Función para hacer scroll al final
function scrollToBottom() {
    setTimeout(() => {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }, 100);
}

// Función para obtener hora actual
function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString('es-ES', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

// Función para escapar HTML y prevenir XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Función para manejar errores de conexión
function handleConnectionError() {
    addBotMessage('No se pudo conectar con el servidor. Por favor, verifica tu conexión a internet e inténtalo de nuevo.');
}

// Exportar funciones si es necesario (para testing o uso externo)
window.chatbot = {
    sendMessage,
    clearChat,
    selectCategory
};