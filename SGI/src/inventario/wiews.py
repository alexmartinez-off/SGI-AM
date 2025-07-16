import uuid
from sqlalchemy.dialects.mysql import JSON, ENUM
from src import db

from src.inventario.models import Inventario, Categoria, Historial

class Categoria(db.Model):
    __tablename__ = 'categoria'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)

class Inventario(db.Model):
    __tablename__ = 'inventario'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    nombre = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'))
    estado = db.Column(ENUM('en_bodega', 'en_uso', 'daniado', 'dado_de_baja'), default='en_bodega')
    info_adicional = db.Column(JSON)
    fecha_registro = db.Column(db.DateTime, server_default=db.func.now())
    usuario_asignado_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    fecha_asignacion = db.Column(db.DateTime)

class Historial(db.Model):
    __tablename__ = 'historial'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('inventario.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    accion = db.Column(db.String(50), nullable=False)
    cantidad = db.Column(db.Integer, default=0)
    estado_anterior = db.Column(ENUM('en_bodega', 'en_uso', 'daniado', 'dado_de_baja'))
    estado_nuevo = db.Column(ENUM('en_bodega', 'en_uso', 'daniado', 'dado_de_baja'))
    fecha = db.Column(db.DateTime, server_default=db.func.now())
    descripcion = db.Column(db.Text)
import uuid
from sqlalchemy.dialects.mysql import JSON, ENUM
from src import db

class Categoria(db.Model):
    __tablename__ = 'categoria'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)

class Inventario(db.Model):
    __tablename__ = 'inventario'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    nombre = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'))
    estado = db.Column(ENUM('en_bodega', 'en_uso', 'daniado', 'dado_de_baja'), default='en_bodega')
    info_adicional = db.Column(JSON)
    fecha_registro = db.Column(db.DateTime, server_default=db.func.now())
    usuario_asignado_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    fecha_asignacion = db.Column(db.DateTime)

class Historial(db.Model):
    __tablename__ = 'historial'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('inventario.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    accion = db.Column(db.String(50), nullable=False)
    cantidad = db.Column(db.Integer, default=0)
    estado_anterior = db.Column(ENUM('en_bodega', 'en_uso', 'daniado', 'dado_de_baja'))
    estado_nuevo = db.Column(ENUM('en_bodega', 'en_uso', 'daniado', 'dado_de_baja'))
    fecha = db.Column(db.DateTime, server_default=db.func.now())
    descripcion = db.Column(db.Text)