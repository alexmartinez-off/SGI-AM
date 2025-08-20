/**
 * Scripts para gestionar categorías
 */

// Función para editar categoría
function editarCategoria(id, nombre, descripcion, activa) {
    const categoriaIdInput = document.getElementById('categoria_id');
    const nombreInput = document.getElementById('nombre');
    const descripcionInput = document.getElementById('descripcion');
    const activaInput = document.getElementById('activa');
    const modalLabel = document.getElementById('modalCategoriaLabel');
    const btnGuardar = document.getElementById('btnGuardarCategoria');
    
    if (categoriaIdInput) categoriaIdInput.value = id;
    if (nombreInput) nombreInput.value = nombre;
    if (descripcionInput) descripcionInput.value = descripcion;
    if (activaInput) activaInput.checked = activa;
    if (modalLabel) modalLabel.textContent = 'Editar Categoría';
    if (btnGuardar) btnGuardar.innerHTML = '<i class="fas fa-save"></i> Actualizar Categoría';
    
    // Mostrar modal
    const modal = document.getElementById('modalCategoria');
    if (modal && typeof bootstrap !== 'undefined') {
        new bootstrap.Modal(modal).show();
    }
}

// Función para nueva categoría
function nuevaCategoria() {
    const form = document.getElementById('formCategoria');
    const categoriaIdInput = document.getElementById('categoria_id');
    const modalLabel = document.getElementById('modalCategoriaLabel');
    const btnGuardar = document.getElementById('btnGuardarCategoria');
    
    if (form) form.reset();
    if (categoriaIdInput) categoriaIdInput.value = '';
    if (modalLabel) modalLabel.textContent = 'Nueva Categoría';
    if (btnGuardar) btnGuardar.innerHTML = '<i class="fas fa-save"></i> Guardar Categoría';
}

// Función para eliminar categoría
function eliminarCategoria(id, nombre) {
    const categoriaIdInput = document.getElementById('categoriaIdEliminar');
    const nombreSpan = document.getElementById('nombreCategoriaEliminar');
    
    if (categoriaIdInput) categoriaIdInput.value = id;
    if (nombreSpan) nombreSpan.textContent = nombre;
    
    // Mostrar modal
    const modal = document.getElementById('modalEliminar');
    if (modal && typeof bootstrap !== 'undefined') {
        new bootstrap.Modal(modal).show();
    }
}

// Función para cambiar estado de categoría
function cambiarEstadoCategoria(id, nuevoEstado) {
    const accion = nuevoEstado ? 'activar' : 'desactivar';
    
    // Usar la URL global definida en la plantilla
    fetch(window.cambiarEstadoCategoriaUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            // Si usas CSRF, asegúrate de incluir el token
            // 'X-CSRFToken': '{{ csrf_token() }}'
        },
        body: JSON.stringify({
            categoria_id: id,
            nuevo_estado: nuevoEstado
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Opcional: mostrar una notificación de éxito (ej. con Toastr o SweetAlert)
            // alert(data.message);
            window.location.reload(); // Recargar la página para ver los cambios
        } else {
            // Opcional: mostrar una notificación de error
            alert('Error: ' + (data.message || 'No se pudo cambiar el estado.'));
        }
    })
    .catch(error => {
        console.error('Error en la petición:', error);
        alert('Ocurrió un error de red. Por favor, inténtelo de nuevo.');
    });
}
    

// Inicializar eventos cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Limpiar el modal cuando se cierre
    const modalCategoria = document.getElementById('modalCategoria');
    if (modalCategoria) {
        modalCategoria.addEventListener('hidden.bs.modal', function () {
            nuevaCategoria();
        });
    }
    
    // Hacer funciones globales para que puedan ser llamadas desde HTML
    window.editarCategoria = editarCategoria;
    window.nuevaCategoria = nuevaCategoria;
    window.eliminarCategoria = eliminarCategoria;
    window.cambiarEstadoCategoria = cambiarEstadoCategoria;
});
