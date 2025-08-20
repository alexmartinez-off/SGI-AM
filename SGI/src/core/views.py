from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import desc
from src import db
from src.accounts.models import User
from src.accounts.views import two_factor_required

# Intentar importar los modelos de inventario, si no existen aún, usar valores por defecto
try:
    from src.inventario.models import Inventario, Categoria
except ImportError:
    Inventario = None
    Categoria = None

core_bp = Blueprint("core", __name__)


@core_bp.route("/")
@login_required
@two_factor_required
def index():
    """Dashboard principal con estadísticas básicas"""
    
    # Estadísticas de usuarios
    total_usuarios = User.query.count()

    estadisticas = {
        'total': 0,
        'disponibles': 0,
        'asignados': 0,
        'mantenimiento': 0,
        'baja': 0,
        'por_categoria': [],
        'nuevos_mes': 0,
        'asignaciones_mes': 0,
        'mantenimientos_mes': 0,
        'bajas_mes': 0
    }
    ultimos_productos = []

    if Inventario:
        estadisticas['total'] = Inventario.query.count()
        estadisticas['disponibles'] = Inventario.query.filter_by(estado='en_bodega').count()
        estadisticas['asignados'] = Inventario.query.filter_by(estado='en_uso').count()
        estadisticas['mantenimiento'] = Inventario.query.filter_by(estado='daniado').count()
        estadisticas['baja'] = Inventario.query.filter_by(estado='dado_de_baja').count()
        ultimos_productos = Inventario.query.order_by(desc(Inventario.fecha_registro)).limit(3).all()
        # Por categoría
        if Categoria:
            estadisticas['por_categoria'] = [
                {
                    'nombre': cat.nombre,
                    'cantidad': len(cat.productos)
                } for cat in Categoria.query.all()
            ]
        # Nuevos este mes
        from datetime import datetime
        from sqlalchemy import extract
        mes_actual = datetime.now().month
        anio_actual = datetime.now().year
        estadisticas['nuevos_mes'] = Inventario.query.filter(
            extract('month', Inventario.fecha_registro) == mes_actual,
            extract('year', Inventario.fecha_registro) == anio_actual
        ).count()
        # Asignaciones, mantenimientos y bajas del mes (requiere modelos y lógica extra)
        # Si tienes modelos de historial, puedes agregar aquí los conteos

    return render_template("core/index.html", 
                         estadisticas=estadisticas, 
                         total_usuarios=total_usuarios, 
                         ultimos_productos=ultimos_productos)