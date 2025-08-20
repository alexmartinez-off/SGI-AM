from flask import Blueprint

# Importar el blueprint de inventario
from .views import inventario_bp

# Exportar para que pueda ser registrado en la aplicación principal
__all__ = ['inventario_bp']
