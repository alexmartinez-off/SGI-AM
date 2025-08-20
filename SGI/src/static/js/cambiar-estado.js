/**
 * Scripts para cambiar estado de productos
 */

// Función para manejar el cambio de estado
function initCambioEstado() {
    const nuevoEstadoSelect = document.getElementById('nuevo_estado');
    
    if (nuevoEstadoSelect) {
        nuevoEstadoSelect.addEventListener('change', function() {
            const nuevoEstado = this.value;
            const alertMantenimiento = document.getElementById('alertMantenimiento');
            const alertBaja = document.getElementById('alertBaja');
            const camposBaja = document.getElementById('camposBaja');
            const btnCambiar = document.getElementById('btnCambiarEstado');
            
            // Ocultar todas las alertas primero
            if (alertMantenimiento) alertMantenimiento.classList.add('d-none');
            if (alertBaja) alertBaja.classList.add('d-none');
            if (camposBaja) camposBaja.classList.add('d-none');
            
            // Mostrar alertas según el estado seleccionado
            if (nuevoEstado === 'mantenimiento' && alertMantenimiento && btnCambiar) {
                alertMantenimiento.classList.remove('d-none');
                btnCambiar.className = 'btn btn-warning';
                btnCambiar.innerHTML = '<i class="fas fa-tools"></i> Enviar a Mantenimiento';
            } else if (nuevoEstado === 'dado_de_baja' && alertBaja && camposBaja && btnCambiar) {
                alertBaja.classList.remove('d-none');
                camposBaja.classList.remove('d-none');
                btnCambiar.className = 'btn btn-danger';
                btnCambiar.innerHTML = '<i class="fas fa-times-circle"></i> Dar de Baja';
            } else if (nuevoEstado === 'disponible' && btnCambiar) {
                btnCambiar.className = 'btn btn-success';
                btnCambiar.innerHTML = '<i class="fas fa-check-circle"></i> Marcar como Disponible';
            } else if (btnCambiar) {
                btnCambiar.className = 'btn btn-primary';
                btnCambiar.innerHTML = '<i class="fas fa-exchange-alt"></i> Cambiar Estado';
            }
        });
    }
}

// Validación para baja
function initValidacionCambioEstado() {
    const form = document.getElementById('formCambiarEstado');
    
    if (form) {
        form.addEventListener('submit', function(e) {
            const nuevoEstado = document.getElementById('nuevo_estado');
            
            if (nuevoEstado && nuevoEstado.value === 'dado_de_baja') {
                const motivo = document.getElementById('motivo');
                if (motivo && motivo.value.trim().length < 10) {
                    e.preventDefault();
                    alert('Para dar de baja un producto, debe proporcionar un motivo detallado (mínimo 10 caracteres).');
                    return false;
                }
                
                if (!confirm('¿Está seguro que desea dar de baja este producto? Esta acción marcará el producto como no disponible para uso.')) {
                    e.preventDefault();
                    return false;
                }
            } else if (nuevoEstado && nuevoEstado.value === 'mantenimiento') {
                if (!confirm('¿Está seguro que desea enviar este producto a mantenimiento?')) {
                    e.preventDefault();
                    return false;
                }
            }
        });
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    initCambioEstado();
    initValidacionCambioEstado();
});
