document.addEventListener('DOMContentLoaded', function() {
  // Obtener todos los elementos de opción de categoría
  const categoryOptions = document.querySelectorAll('.category-option');
  const selectedCategorySpan = document.getElementById('selected-category');
  const messageInput = document.getElementById('messageInput');
  const sendButton = document.getElementById('sendButton');
  
  // Agregar evento click a cada opción
  categoryOptions.forEach(option => {
    option.addEventListener('click', function(e) {
      e.preventDefault();
      
      // 1. Obtener el texto de la opción seleccionada
      const selectedText = this.textContent;
      
      // 2. Actualizar el texto en el botón
      const selectedCategorySpan = document.getElementById('selected-category');
      selectedCategorySpan.textContent = selectedText;
      
      // 3. Cerrar el dropdown
      const dropdown = document.getElementById('dropdown');
      
      // Método 1: Usando la API de Flowbite (recomendado)
      if (window.Dropdown) {
        dropdown.classList.add('hidden');
      } 

      // Habilitar el input y cambiar el placeholder
      messageInput.disabled = false;
      messageInput.placeholder = "Pregunta algo...";
      sendButton.disabled = false;
    });
  });

  // Validar si intentan escribir sin seleccionar categoría
  messageInput.addEventListener('focus', function() {
    if (!selectedCategory) {
      // Mostrar alerta y quitar el foco del input
      alert('Por favor selecciona una categoría primero');
      this.blur();
    }
  });
});

/*
this.messagesContainer.innerHTML = `
    <div class="flex ...">
        ...
    </div>
`;
*/