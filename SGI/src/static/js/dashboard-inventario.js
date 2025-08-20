/**
 * Scripts para el dashboard de inventario con Chart.js
 */

// Configuración global de Chart.js
Chart.defaults.responsive = true;
Chart.defaults.maintainAspectRatio = false;

// Función para inicializar el gráfico de estados
function initChartEstados(estadisticas) {
    const ctx = document.getElementById('chartEstados');
    if (!ctx) return;
    
    const data = {
        labels: ['Disponibles', 'Asignados', 'En Mantenimiento', 'Dados de Baja'],
        datasets: [{
            data: [
                estadisticas.disponibles || 0,
                estadisticas.asignados || 0,
                estadisticas.mantenimiento || 0,
                estadisticas.dados_baja || 0
            ],
            backgroundColor: ['#28a745', '#ffc107', '#17a2b8', '#dc3545'],
            borderWidth: 2,
            borderColor: '#fff'
        }]
    };
    
    new Chart(ctx, {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Función para inicializar el gráfico de categorías
function initChartCategorias(categorias) {
    const ctx = document.getElementById('chartCategorias');
    if (!ctx || !categorias || categorias.length === 0) return;
    
    const labels = categorias.map(cat => cat.nombre);
    const data = categorias.map(cat => cat.cantidad);
    
    const chartData = {
        labels: labels,
        datasets: [{
            label: 'Productos',
            data: data,
            backgroundColor: [
                '#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1', 
                '#fd7e14', '#20c997', '#6c757d', '#e83e8c', '#17a2b8'
            ],
            borderWidth: 1
        }]
    };
    
    new Chart(ctx, {
        type: 'bar',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// Función para actualizar estadísticas
function actualizarEstadisticas() {
    const apiUrl = window.estadisticasApiUrl || '/inventario/api/estadisticas';
    
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error('Error en la respuesta del servidor');
            }
            return response.json();
        })
        .then(data => {
            // Actualizar elementos del DOM
            const elementosEstadisticas = {
                'total-productos': data.total,
                'productos-disponibles': data.disponibles,
                'productos-asignados': data.asignados,
                'productos-mantenimiento': data.mantenimiento
            };
            
            Object.entries(elementosEstadisticas).forEach(([id, valor]) => {
                const elemento = document.getElementById(id);
                if (elemento) {
                    elemento.textContent = valor || 0;
                }
            });
        })
        .catch(error => {
            console.log('Error al actualizar estadísticas:', error);
        });
}

// Función para inicializar todo el dashboard
function initDashboardInventario(estadisticas, categorias) {
    // Inicializar gráficos
    initChartEstados(estadisticas);
    initChartCategorias(categorias);
    
    // Configurar actualización automática cada 5 minutos
    setInterval(actualizarEstadisticas, 300000);
}

// Hacer funciones disponibles globalmente
window.initDashboardInventario = initDashboardInventario;
window.actualizarEstadisticas = actualizarEstadisticas;

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard de inventario JavaScript cargado');
});
