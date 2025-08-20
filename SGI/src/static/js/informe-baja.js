/**
 * Scripts para el formulario de informe de baja de productos
 */

// Habilitar botón solo cuando se confirme
function initConfirmacionBaja() {
    const confirmarCheckbox = document.getElementById('confirmarBaja');
    const btnDarBaja = document.getElementById('btnDarBaja');
    
    if (confirmarCheckbox && btnDarBaja) {
        confirmarCheckbox.addEventListener('change', function() {
            btnDarBaja.disabled = !this.checked;
        });
    }
}

// Validación final antes del envío
function initValidacionFormulario() {
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const motivo = document.getElementById('descripcion_detallada');
            const documento = document.getElementById('documento_respaldo');
            
            if (motivo && motivo.value.trim().length < 20) {
                e.preventDefault();
                alert('La descripción detallada debe tener al menos 20 caracteres.');
                return false;
            }
            
            if (documento && documento.files.length === 0) {
                e.preventDefault();
                alert('Debe subir al menos un documento de respaldo para procesar la baja.');
                return false;
            }
            
            if (!confirm('¿ESTÁ COMPLETAMENTE SEGURO que desea dar de baja este producto? Esta acción es IRREVERSIBLE.')) {
                e.preventDefault();
                return false;
            }
            
            // Mostrar loading
            const btn = document.getElementById('btnDarBaja');
            if (btn) {
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando Baja...';
                btn.disabled = true;
            }
        });
    }
}

// Calcular valor residual automáticamente si está vacío
function calcularValorResidual(valorAdquisicion, fechaAdquisicion, vidaUtil) {
    const valorResidualField = document.getElementById('valor_residual');
    
    if (valorResidualField && valorAdquisicion > 0 && valorResidualField.value === '') {
        const ahora = new Date();
        const fechaAdq = new Date(fechaAdquisicion);
        const anosTranscurridos = (ahora - fechaAdq) / (1000 * 60 * 60 * 24 * 365);
        const depreciacion = Math.min(anosTranscurridos / vidaUtil, 1);
        const valorResidual = valorAdquisicion * (1 - depreciacion);
        
        valorResidualField.value = Math.max(0, valorResidual).toFixed(2);
    }
}

// Función para inicializar el cálculo automático del valor residual
function initCalculoValorResidual() {
    // Esta función será llamada desde el HTML pasando los valores del producto
    window.initValorResidual = function(valorAdquisicion, fechaAdquisicion, vidaUtil) {
        calcularValorResidual(valorAdquisicion, fechaAdquisicion, vidaUtil);
    };
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    initConfirmacionBaja();
    initValidacionFormulario();
    initCalculoValorResidual();
});
