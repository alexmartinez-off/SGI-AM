import uuid
from datetime import datetime
from sqlalchemy.dialects.mysql import JSON, ENUM
from src import db


# Modelo para las categorías de inventario
class Categoria(db.Model):
    __tablename__ = 'categoria'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Categoria {self.nombre}>'

# Modelo para los productos en inventario
class Inventario(db.Model):
    __tablename__ = 'inventario'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    nombre = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)
    estado = db.Column(ENUM('en_bodega', 'en_uso', 'daniado', 'dado_de_baja'), default='en_bodega')
    info_adicional = db.Column(JSON)  # Campos dinámicos por tipo de producto
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_asignado_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    fecha_asignacion = db.Column(db.DateTime)
    cantidad = db.Column(db.Integer, default=1)
    precio = db.Column(db.Numeric(10, 2), default=0)  # Precio del artículo
    ubicacion = db.Column(db.String(255))  # Ubicación física del producto
    # codigo_barras = db.Column(db.String(100), unique=True)  # Código de barras opcional
    # valor_adquisicion = db.Column(db.Numeric(10, 2))  # Valor de compra
    # proveedor = db.Column(db.String(255))  # Proveedor del producto
    marca = db.Column(db.String(100))      
    modelo = db.Column(db.String(100))     

    
    # Relaciones
    categoria = db.relationship('Categoria', backref='productos')
    usuario_asignado = db.relationship('User', backref='productos_asignados')

    def __repr__(self):
        return f'<Inventario {self.nombre} - {self.uuid}>'

    @property
    def estado_display(self):
        estados = {
            'en_bodega': 'En Bodega',
            'en_uso': 'En Uso',
            'daniado': 'Dañado',
            'dado_de_baja': 'Dado de Baja'
        }
        return estados.get(self.estado, self.estado)

# Modelo para el historial de acciones sobre el inventario
class Historial(db.Model):
    __tablename__ = 'historial'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('inventario.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    accion = db.Column(db.String(50), nullable=False)  # 'creado', 'editado', 'asignado', 'cambio_estado'
    cantidad = db.Column(db.Integer, default=0)
    estado_anterior = db.Column(ENUM('en_bodega', 'en_uso', 'daniado', 'dado_de_baja'))
    estado_nuevo = db.Column(ENUM('en_bodega', 'en_uso', 'daniado', 'dado_de_baja'))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    descripcion = db.Column(db.Text)
    detalles_adicionales = db.Column(JSON)  # Para información extra

    # Relaciones
    producto = db.relationship('Inventario', backref='historial')
    usuario = db.relationship('User', backref='acciones_inventario')

    def __repr__(self):
        return f'<Historial {self.accion} - {self.producto_id}>'

# Modelo para informes de baja de productos
class InformeBaja(db.Model):
    __tablename__ = 'informes_baja'
    id = db.Column(db.Integer, primary_key=True)
    # Hacer nullable para permitir conservar el informe cuando el producto sea eliminado
    producto_id = db.Column(db.Integer, db.ForeignKey('inventario.id'), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    usuario = db.relationship('User', foreign_keys=[usuario_id])
    motivo = db.Column(db.String(100), nullable=False)  # 'deterioro', 'obsolescencia', 'perdida', 'robo', 'otro'
    descripcion_detallada = db.Column(db.Text, nullable=False)
    fecha_baja = db.Column(db.DateTime, default=datetime.utcnow)
    valor_residual = db.Column(db.Numeric(10, 2))
    documento_adjunto = db.Column(db.String(255))  # Ruta del documento justificante
    aprobado_por = db.Column(db.Integer, db.ForeignKey('users.id'))  # Admin que aprueba la baja
    fecha_aprobacion = db.Column(db.DateTime)
    estado_informe = db.Column(db.String(20), default='pendiente')  # 'pendiente', 'aprobado', 'rechazado'
    aprobado = db.Column(db.Boolean, default=False)  # True si el informe fue aprobado
    comentarios_aprobacion = db.Column(db.Text)
    estado_previo = db.Column(db.String(50))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Campos snapshot del producto al momento de la aprobación (para conservar historial)
    # Relaciones
    producto = db.relationship('Inventario', backref='informes_baja')
    usuario = db.relationship('User', foreign_keys=[usuario_id], backref='informes_baja_creados')
    aprobador = db.relationship('User', foreign_keys=[aprobado_por], backref='informes_baja_aprobados')

    def __repr__(self):
        return f'<InformeBaja {self.producto_id} - {self.motivo}>'

# Modelo para asignaciones de productos originales
""""
class Asignacion(db.Model):
    __tablename__ = 'asignaciones'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('inventario.id'), nullable=False)
    usuario_asignado_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    asignado_por = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    fecha_asignacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_devolucion_esperada = db.Column(db.DateTime)
    fecha_devolucion_real = db.Column(db.DateTime)
    motivo_asignacion = db.Column(db.String(255), nullable=False)
    condiciones_uso = db.Column(db.Text)
    estado_asignacion = db.Column(ENUM('activa', 'devuelta', 'vencida'), default='activa')
    observaciones = db.Column(db.Text) """

"""prueba temporal para el funcionamiento de guardar en crear producto (inventario ) 
#quea comentado el original en las lineas de arriba de la linea 108 hasta la linea 120"""

class Asignacion(db.Model):
    __tablename__ = 'asignaciones'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('inventario.id'), nullable=False)
    usuario_asignado_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    asignado_por = db.Column(db.Integer, db.ForeignKey('users.id'))
    fecha_asignacion = db.Column(db.DateTime)
    fecha_devolucion_esperada = db.Column(db.Date)
    motivo_asignacion = db.Column(db.Text)
    condiciones_uso = db.Column(db.Text)
    empleado_nombre = db.Column(db.String(255))
    empleado_telefono = db.Column(db.String(50))
    observaciones = db.Column(db.Text)
    activa = db.Column(db.Boolean, default=True)
    fecha_devolucion_real = db.Column(db.DateTime)


    # Relaciones
    producto = db.relationship('Inventario', backref='asignaciones')
    usuario_asignado = db.relationship('User', foreign_keys=[usuario_asignado_id], backref='asignaciones_recibidas')
    asignador = db.relationship('User', foreign_keys=[asignado_por], backref='asignaciones_realizadas')

    def __repr__(self):
        return f'<Asignacion {self.producto_id} -> {self.usuario_asignado_id}>'
