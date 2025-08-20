// Inicializar dashboard con datos del servidor
// Este script fue extraído de dashboard.html para evitar errores de JS inline

document.addEventListener('DOMContentLoaded', function() {
    const estadisticas = window.dashboardEstadisticas || {
        total: 0,
        disponibles: 0,
        asignados: 0,
        mantenimiento: 0,
        dados_baja: 0
    };
    const categorias = window.dashboardCategorias || [];
    window.estadisticasApiUrl = window.estadisticasApiUrl || '';
    if (window.initDashboardInventario) {
        window.initDashboardInventario(estadisticas, categorias);
    }
});
