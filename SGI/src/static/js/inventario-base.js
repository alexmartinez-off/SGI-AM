/**
 * Scripts base para inventario
 * Funciones comunes para gestión de inventario
 */

// Función para confirmar eliminación
function confirmarEliminacion(nombre) {
    return confirm(`¿Está seguro de que desea eliminar "${nombre}"?\n\nEsta acción no se puede deshacer.`);
}

// Función para toggle de filtros
function toggleFiltros() {
    const filtrosContainer = document.getElementById('filtros-container');
    const toggleBtn = document.querySelector('[data-bs-toggle="collapse"]');
    
    if (filtrosContainer) {
        if (filtrosContainer.classList.contains('show')) {
            filtrosContainer.classList.remove('show');
            if (toggleBtn) toggleBtn.setAttribute('aria-expanded', 'false');
        } else {
            filtrosContainer.classList.add('show');
            if (toggleBtn) toggleBtn.setAttribute('aria-expanded', 'true');
        }
    }
}

// Función para limpiar filtros
function limpiarFiltros() {
    const form = document.getElementById('filtros-form');
    if (form) {
        // Limpiar todos los inputs
        const inputs = form.querySelectorAll('input, select');
        inputs.forEach(input => {
            if (input.type === 'checkbox' || input.type === 'radio') {
                input.checked = false;
            } else {
                input.value = '';
            }
        });
        
        // Enviar formulario para aplicar filtros vacíos
        form.submit();
    }
}

// Funciones de utilidad para tabla
function initDataTable(tableId, options = {}) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    // Configuración por defecto
    const defaultOptions = {
        responsive: true,
        pageLength: 25,
        language: {
            url: '//cdn.datatables.net/plug-ins/1.11.5/i18n/Spanish.json'
        }
    };
    
    // Mezclar opciones
    const finalOptions = Object.assign(defaultOptions, options);
    
    // Inicializar DataTable si está disponible
    if (typeof $ !== 'undefined' && $.fn.DataTable) {
        $(table).DataTable(finalOptions);
    }
}

// Función para manejo de alertas
function showAlert(message, type = 'info', duration = 5000) {
    const alertContainer = document.getElementById('alert-container') || document.body;
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alertDiv);
    
    // Auto-remover después del tiempo especificado
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, duration);
}

// Función para validar formularios
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Hacer funciones disponibles globalmente
window.confirmarEliminacion = confirmarEliminacion;
window.toggleFiltros = toggleFiltros;
window.limpiarFiltros = limpiarFiltros;
window.initDataTable = initDataTable;
window.showAlert = showAlert;
window.validateForm = validateForm;

// Inicialización al cargar el DOM
document.addEventListener('DOMContentLoaded', function() {
    console.log('Inventario base JavaScript cargado');
    
    // Inicializar tooltips de Bootstrap si están disponibles
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});
