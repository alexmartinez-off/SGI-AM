/**
 * Scripts para configuración 2FA
 * Funciones para manejo de autenticación de dos factores
 */

// Función para copiar secreto 2FA al portapapeles
function copySecret() {
    const secretElement = document.getElementById('secret-key');
    if (!secretElement) return;
    
    const secretText = secretElement.textContent || secretElement.innerText;
    
    // Usar la API moderna del portapapeles si está disponible
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(secretText).then(function() {
            showCopySuccess();
        }).catch(function(err) {
            console.error('Error al copiar: ', err);
            fallbackCopyTextToClipboard(secretText);
        });
    } else {
        // Fallback para navegadores más antiguos
        fallbackCopyTextToClipboard(secretText);
    }
}

// Función fallback para copiar texto
function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    
    // Evitar scroll en iOS
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.position = "fixed";
    
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showCopySuccess();
        } else {
            showCopyError();
        }
    } catch (err) {
        console.error('Fallback: No se pudo copiar', err);
        showCopyError();
    }
    
    document.body.removeChild(textArea);
}

// Función para mostrar éxito al copiar
function showCopySuccess() {
    const button = document.querySelector('.copy-button');
    if (button) {
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check"></i> ¡Copiado!';
        button.classList.add('btn-success');
        button.classList.remove('btn-outline-secondary');
        
        setTimeout(function() {
            button.innerHTML = originalText;
            button.classList.remove('btn-success');
            button.classList.add('btn-outline-secondary');
        }, 2000);
    }
    
    // Mostrar alerta también
    showAlert('Secreto copiado al portapapeles', 'success', 3000);
}

// Función para mostrar error al copiar
function showCopyError() {
    showAlert('Error al copiar. Por favor, selecciona y copia manualmente.', 'warning', 5000);
}

// Función para validar código 2FA
function validateTOTPCode(code) {
    // Validar formato básico (6 dígitos)
    const codePattern = /^\d{6}$/;
    return codePattern.test(code);
}

// Función para formatear entrada de código 2FA
function formatTOTPInput(input) {
    // Remover caracteres no numéricos
    let value = input.value.replace(/\D/g, '');
    
    // Limitar a 6 dígitos
    if (value.length > 6) {
        value = value.substring(0, 6);
    }
    
    input.value = value;
    
    // Validar visualmente
    if (value.length === 6) {
        if (validateTOTPCode(value)) {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        } else {
            input.classList.add('is-invalid');
            input.classList.remove('is-valid');
        }
    } else {
        input.classList.remove('is-valid', 'is-invalid');
    }
}

// Función para inicializar configuración 2FA
function init2FASetup() {
    // Configurar botón de copiar
    const copyButton = document.querySelector('.copy-button');
    if (copyButton) {
        copyButton.addEventListener('click', copySecret);
    }
    
    // Configurar input de código TOTP
    const totpInput = document.getElementById('totp_code');
    if (totpInput) {
        totpInput.addEventListener('input', function() {
            formatTOTPInput(this);
        });
        
        // Enfocar automáticamente en el campo
        totpInput.focus();
    }
    
    // Configurar formulario
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const totpCode = document.getElementById('totp_code');
            if (totpCode && !validateTOTPCode(totpCode.value)) {
                e.preventDefault();
                showAlert('Por favor, ingresa un código válido de 6 dígitos', 'warning');
                totpCode.focus();
                return false;
            }
        });
    }
}

// Función de utilidad para mostrar alertas (si no está disponible globalmente)
function showAlert(message, type = 'info', duration = 5000) {
    if (window.showAlert) {
        window.showAlert(message, type, duration);
        return;
    }
    
    // Implementación básica si no hay función global
    const alertContainer = document.getElementById('alert-container') || document.body;
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alertDiv);
    
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, duration);
}

// Hacer funciones disponibles globalmente
window.copySecret = copySecret;
window.validateTOTPCode = validateTOTPCode;
window.formatTOTPInput = formatTOTPInput;
window.init2FASetup = init2FASetup;

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('2FA setup JavaScript cargado');
    init2FASetup();
});
