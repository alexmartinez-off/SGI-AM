/**
 * Scripts para editar usuario
 * Funciones para validación de contraseñas y gestión de formularios
 */

// Función para limpiar errores de contraseña
function clearPasswordErrors() {
    const errorElements = document.querySelectorAll('.password-error');
    errorElements.forEach(element => {
        element.style.display = 'none';
    });
    
    const passwordField = document.getElementById('password');
    const confirmField = document.getElementById('confirm_password');
    
    if (passwordField) passwordField.classList.remove('is-invalid');
    if (confirmField) confirmField.classList.remove('is-invalid');
}

// Función para actualizar estado del campo de confirmación
function updateConfirmPasswordState() {
    const passwordField = document.getElementById('password');
    const confirmField = document.getElementById('confirm_password');
    const confirmGroup = document.getElementById('confirm-password-group');
    
    if (!passwordField || !confirmField || !confirmGroup) return;
    
    const passwordValue = passwordField.value;
    
    if (passwordValue.length > 0) {
        confirmGroup.style.display = 'block';
        confirmField.required = true;
    } else {
        confirmGroup.style.display = 'none';
        confirmField.required = false;
        confirmField.value = '';
        clearPasswordErrors();
    }
}

// Función para validar confirmación de contraseña
function validatePasswordConfirmation() {
    const passwordField = document.getElementById('password');
    const confirmField = document.getElementById('confirm_password');
    
    if (!passwordField || !confirmField) return true;
    
    const password = passwordField.value;
    const confirmPassword = confirmField.value;
    
    if (password && confirmPassword && password !== confirmPassword) {
        confirmField.classList.add('is-invalid');
        showPasswordError('Las contraseñas no coinciden');
        return false;
    } else {
        confirmField.classList.remove('is-invalid');
        clearPasswordErrors();
        return true;
    }
}

// Función para mostrar errores de contraseña
function showPasswordError(message) {
    const errorContainer = document.getElementById('password-error-container');
    if (errorContainer) {
        errorContainer.innerHTML = `<div class="alert alert-danger password-error">${message}</div>`;
    }
}

// Función para inicializar validación de usuarios
function initUserEditValidation() {
    const passwordField = document.getElementById('password');
    const confirmField = document.getElementById('confirm_password');
    const form = document.querySelector('form');
    
    if (passwordField) {
        // Actualizar estado al escribir en contraseña
        passwordField.addEventListener('input', updateConfirmPasswordState);
        
        // Limpiar errores al enfocar
        passwordField.addEventListener('focus', clearPasswordErrors);
    }
    
    if (confirmField) {
        // Validar al escribir en confirmación
        confirmField.addEventListener('input', validatePasswordConfirmation);
        
        // Validar al perder foco
        confirmField.addEventListener('blur', validatePasswordConfirmation);
    }
    
    if (form) {
        // Validar antes de enviar
        form.addEventListener('submit', function(e) {
            if (!validatePasswordConfirmation()) {
                e.preventDefault();
                return false;
            }
        });
    }
}

// Función para alternar visibilidad de contraseña
function togglePasswordVisibility(fieldId) {
    const field = document.getElementById(fieldId);
    const toggleBtn = document.querySelector(`[data-target="${fieldId}"]`);
    
    if (!field || !toggleBtn) return;
    
    if (field.type === 'password') {
        field.type = 'text';
        toggleBtn.innerHTML = '<i class="fas fa-eye-slash"></i>';
    } else {
        field.type = 'password';
        toggleBtn.innerHTML = '<i class="fas fa-eye"></i>';
    }
}

// Hacer funciones disponibles globalmente
window.clearPasswordErrors = clearPasswordErrors;
window.updateConfirmPasswordState = updateConfirmPasswordState;
window.validatePasswordConfirmation = validatePasswordConfirmation;
window.initUserEditValidation = initUserEditValidation;
window.togglePasswordVisibility = togglePasswordVisibility;

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('User edit JavaScript cargado');
    initUserEditValidation();
});
