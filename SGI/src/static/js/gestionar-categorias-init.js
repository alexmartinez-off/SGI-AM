// Script extraído de gestionar_categorias.html para configuración de URL global
window.cambiarEstadoCategoriaUrl = window.cambiarEstadoCategoriaUrl || '';

document.addEventListener('DOMContentLoaded', function() {
    // Event listener para botones de editar
    document.querySelectorAll('.btn-edit-categoria').forEach(button => {
        button.addEventListener('click', function() {
            const id = this.dataset.id;
            // Los datos JSON en los atributos data-* deben ser parseados.
            // Se almacenan como strings, pero tojson|safe los formatea como un string JSON válido.
            const nombre = JSON.parse(this.dataset.nombre);
            const descripcion = JSON.parse(this.dataset.descripcion);
            const activa = this.dataset.activa === 'true';
            editarCategoria(id, nombre, descripcion, activa);
        });
    });

    // Event listener para botones de eliminar
    document.querySelectorAll('.btn-delete-categoria').forEach(button => {
        button.addEventListener('click', function() {
            const id = this.dataset.id;
            const nombre = JSON.parse(this.dataset.nombre);
            eliminarCategoria(id, nombre);
        });
    });

    // Event listener para botones de cambiar estado
    document.querySelectorAll('.btn-change-status').forEach(button => {
        button.addEventListener('click', function() {
            const id = this.dataset.id;
            const nuevoEstado = this.dataset.nuevoEstado === 'true';
            const accion = nuevoEstado ? 'activar' : 'desactivar';
            if (confirm(`¿Está seguro que desea ${accion} esta categoría?`)) {
                cambiarEstadoCategoria(id, nuevoEstado);
            }
        });
    });

    // Event listener para el botón de nueva categoría para limpiar el modal
    const btnNuevaCategoria = document.querySelector('button[data-bs-target="#modalCategoria"]');
    if (btnNuevaCategoria) {
        // Asegurarse de que al abrir el modal para una nueva categoría, se llame a la función.
        btnNuevaCategoria.addEventListener('click', nuevaCategoria);
    }
});
