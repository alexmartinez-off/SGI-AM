/**
 * Scripts para el Dashboard de Inventario
 * Gráficos con Chart.js
 */

// Función para inicializar gráficos del dashboard de inventario
function initInventarioDashboard(data) {
    // Gráfico de productos por categoría
    if (data.productos_por_categoria && data.productos_por_categoria.length > 0) {
        const ctx1 = document.getElementById('categoriasChart');
        if (ctx1) {
            new Chart(ctx1.getContext('2d'), {
                type: 'pie',
                data: {
                    labels: data.productos_por_categoria.map(cat => cat.nombre),
                    datasets: [{
                        data: data.productos_por_categoria.map(cat => cat.cantidad),
                        backgroundColor: [
                            '#FF6384',
                            '#36A2EB',
                            '#FFCE56',
                            '#4BC0C0',
                            '#9966FF',
                            '#FF9F40',
                            '#FF9999',
                            '#87CEEB'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return context.label + ': ' + context.parsed + ' productos';
                                }
                            }
                        }
                    }
                }
            });
        }
    }

    // Gráfico de estado de productos
    const ctx2 = document.getElementById('estadosChart');
    if (ctx2) {
        new Chart(ctx2.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['En Bodega', 'En Uso', 'Dañados', 'Dados de Baja'],
                datasets: [{
                    data: [
                        data.productos_en_bodega || 0,
                        data.productos_en_uso || 0,
                        data.productos_daniados || 0,
                        data.productos_dados_baja || 0
                    ],
                    backgroundColor: [
                        '#28a745',
                        '#ffc107',
                        '#dc3545',
                        '#6c757d'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.parsed + ' productos';
                            }
                        }
                    }
                },
                cutout: '60%'
            }
        });
    }
}

// Función para actualizar estadísticas en tiempo real (opcional)
function actualizarEstadisticas() {
    fetch('/api/estadisticas')
        .then(response => response.json())
        .then(data => {
            // Actualizar números en las tarjetas
            document.querySelector('[data-stat="total"]').textContent = data.total_productos;
            document.querySelector('[data-stat="bodega"]').textContent = data.por_estado.en_bodega;
            document.querySelector('[data-stat="uso"]').textContent = data.por_estado.en_uso;
            document.querySelector('[data-stat="daniados"]').textContent = data.por_estado.daniado;
        })
        .catch(error => {
            console.error('Error al actualizar estadísticas:', error);
        });
}

// Inicializar cuando el documento esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Los datos se pasarán desde la plantilla
    console.log('Dashboard de inventario inicializado');
});
