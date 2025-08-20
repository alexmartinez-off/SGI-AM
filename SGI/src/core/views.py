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
    
    # Estadísticas de inventario (si está disponible)
    total_productos = 0
    productos_en_bodega = 0
    productos_en_uso = 0
    ultimos_productos = []
    
    if Inventario:
        total_productos = Inventario.query.count()
        productos_en_bodega = Inventario.query.filter_by(estado='en_bodega').count()
        productos_en_uso = Inventario.query.filter_by(estado='en_uso').count()
        ultimos_productos = Inventario.query.order_by(desc(Inventario.fecha_registro)).limit(3).all()
    
    return render_template("core/index.html", 
                         total_usuarios=total_usuarios,
                         total_productos=total_productos,
                         productos_en_bodega=productos_en_bodega,
                         productos_en_uso=productos_en_uso,
                         ultimos_productos=ultimos_productos)