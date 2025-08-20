from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, IntegerField, DecimalField, DateTimeField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from wtforms.widgets import TextArea
from src.inventario.models import Categoria
from src import db

class ProductoForm(FlaskForm):
    """Formulario para crear/editar productos"""
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=255)])
    descripcion = TextAreaField('Descripción', validators=[DataRequired()])
    categoria_id = SelectField('Categoría', coerce=int, validators=[DataRequired()])
    cantidad = IntegerField('Cantidad', validators=[DataRequired(), NumberRange(min=1)])
    ubicacion = StringField('Ubicación', validators=[Length(max=255)])
    # codigo_barras = StringField('Código de Barras', validators=[Length(max=100)])  # Opcional
    # valor_adquisicion = DecimalField('Valor de Adquisición', validators=[Optional()])
    # proveedor = StringField('Proveedor', validators=[Length(max=255)])
    marca = StringField('Marca', validators=[Length(max=100)])
    modelo = StringField('Modelo', validators=[Length(max=100)])
    submit = SubmitField('Guardar Producto')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cargar categorías activas para el select
        self.categoria_id.choices = [(c.id, c.nombre) for c in Categoria.query.filter_by(activo=True).all()]
        
class CategoriaForm(FlaskForm):
    """Formulario para crear/editar categorías"""
    nombre = StringField('Nombre de la Categoría', validators=[
        DataRequired(message="El nombre es obligatorio"),
        Length(min=3, max=100, message="El nombre debe tener entre 3 y 100 caracteres")
    ])
    
    descripcion = TextAreaField('Descripción', validators=[
        Optional(),
        Length(max=500, message="La descripción no puede exceder 500 caracteres")
    ])
    
    submit = SubmitField('Guardar Categoría')

class AsignacionForm(FlaskForm):
    """Formulario para asignar productos a usuarios"""
    uuid_unidad = SelectField('Unidad a asignar (UUID)', validators=[DataRequired()])
    usuario_asignado_id = SelectField('Usuario a Asignar', validators=[DataRequired()], coerce=int)
    
    motivo_asignacion = StringField('Motivo de Asignación', validators=[
        DataRequired(message="El motivo es obligatorio"),
        Length(min=10, max=255, message="El motivo debe tener entre 10 y 255 caracteres")
    ])
    
    fecha_devolucion_esperada = DateTimeField('Fecha de Devolución Esperada', validators=[Optional()])
    
    condiciones_uso = TextAreaField('Condiciones de Uso', validators=[
        Optional(),
        Length(max=1000, message="Las condiciones no pueden exceder 1000 caracteres")
    ])
    
    submit = SubmitField('Asignar Producto')

    def __init__(self, producto_id=None, *args, **kwargs):
        super(AsignacionForm, self).__init__(*args, **kwargs)
        from src.accounts.models import User
        self.usuario_asignado_id.choices = [(u.id, f"{u.nombre} {u.apellido} ({u.username})") 
                                          for u in User.query.all()]
        from src.inventario.models import Inventario
        if producto_id:
            unidades = Inventario.query.filter_by(id=producto_id, estado='en_bodega').all()
            self.uuid_unidad.choices = [(u.uuid, f"{u.uuid} - {u.nombre}") for u in unidades]

class InformeBajaForm(FlaskForm):
    """Formulario para reportar baja de productos"""
    uuid_unidad = SelectField('Unidad a dar de baja (UUID)', validators=[DataRequired()])
    def __init__(self, producto_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from src.inventario.models import Inventario
        if producto_id:
            unidades = Inventario.query.filter_by(id=producto_id, estado='en_bodega').all()
            self.uuid_unidad.choices = [(u.uuid, f"{u.uuid} - {u.nombre}") for u in unidades]
    motivo_otro = StringField('Especifique el motivo', validators=[Length(max=100)], render_kw={"placeholder": "Si selecciona 'Otro', escriba el motivo"})
    descripcion_detallada = TextAreaField('Descripción Detallada', validators=[DataRequired()])
    fecha_baja = DateField('Fecha de Baja', validators=[DataRequired()])  # Selector de fecha
    valor_residual = DecimalField('Valor Residual', validators=[Optional()])
    documento_adjunto = FileField('Documento Adjunto', validators=[
        FileAllowed(['pdf', 'jpg', 'png', 'jpeg'], 'Solo PDF o imagen')
    ])
    submit = SubmitField('Enviar Informe')

class CambiarEstadoForm(FlaskForm):
    """Formulario para cambiar el estado de un producto"""
    estado_nuevo = SelectField('Nuevo Estado', validators=[DataRequired()], choices=[
        ('en_bodega', 'En Bodega'),
        ('en_uso', 'En Uso'),
        ('daniado', 'Dañado'),
        ('dado_de_baja', 'Dado de Baja')
    ])
    
    descripcion = TextAreaField('Motivo del Cambio', validators=[
        DataRequired(message="El motivo del cambio es obligatorio"),
        Length(min=10, max=500, message="El motivo debe tener entre 10 y 500 caracteres")
    ])
    
    submit = SubmitField('Cambiar Estado')

class FiltroInventarioForm(FlaskForm):
    """Formulario para filtrar el inventario"""
    nombre = StringField('Nombre del Producto')
    categoria_id = SelectField('Categoría', coerce=int)
    estado = SelectField('Estado', choices=[
        ('', 'Todos los estados'),
        ('en_bodega', 'En Bodega'),
        ('en_uso', 'En Uso'),
        ('daniado', 'Dañado'),
        ('dado_de_baja', 'Dado de Baja')
    ])
    usuario_asignado = StringField('Asignado a')
    
    submit = SubmitField('Filtrar')

    def __init__(self, *args, **kwargs):
        super(FiltroInventarioForm, self).__init__(*args, **kwargs)
        # Cargar categorías dinámicamente
        categorias = [('', 'Todas las categorías')] + [(c.id, c.nombre) for c in Categoria.query.filter_by(activo=True).all()]
        self.categoria_id.choices = categorias



