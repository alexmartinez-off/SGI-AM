from datetime import datetime

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, TextAreaField, SelectField, IntegerField, DecimalField,
    DateField, SubmitField, FieldList, FormField
)
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError
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
    precio = DecimalField('Precio', validators=[DataRequired(), NumberRange(min=0)], places=2, default=0)
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


# ---------- Orden de Entrada (estilo planilla) ----------
class OrdenEntradaItemForm(FlaskForm):
    detalle = StringField('Detalle', validators=[Optional(), Length(max=255)])
    categoria_id = SelectField('Categoría', coerce=int, validators=[Optional()])
    cantidad = IntegerField('Cantidad', validators=[Optional(), NumberRange(min=1)], default=1)
    precio_unitario = DecimalField('Vr. Unitario', validators=[Optional(), NumberRange(min=0)], places=2, default=0)
    valor_total = DecimalField('Valor Total', validators=[Optional(), NumberRange(min=0)], places=2, default=0)


class OrdenEntradaForm(FlaskForm):
    numero_orden = StringField('Orden de Entrada No.', validators=[Optional(), Length(max=50)])
    fecha = DateField('Fecha', validators=[DataRequired()])
    con_cargo_a = StringField('Con cargo a', validators=[Optional(), Length(max=255)])
    senor = StringField('Señor', validators=[Optional(), Length(max=255)])
    items = FieldList(FormField(OrdenEntradaItemForm), min_entries=1, max_entries=50)
    submit = SubmitField('Registrar Orden de Entrada')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cargar categorías activas para cada item, con opción inicial neutra
        categorias = [(0, 'Seleccione categoría')] + [(c.id, c.nombre) for c in Categoria.query.filter_by(activo=True).all()]
        for item in self.items:
            try:
                item.form.categoria_id.choices = categorias
            except Exception:
                # Algunos items pueden no estar inicializados aún; ignorar silenciosamente
                pass

def validar_fecha_es(form, field):
    if field.raw_data and not field.data:
        raise ValidationError('Ingresá una fecha válida en formato AAAA-MM-DD.')


class AsignacionForm(FlaskForm):
    """Formulario para asignar productos a usuarios"""
    uuid_unidad = SelectField('Unidad a asignar (UUID)', validators=[DataRequired()])
    usuario_asignado_id = SelectField('Usuario encargado de entregar', validators=[DataRequired()], coerce=int)
    
    motivo_asignacion = StringField('Motivo de Asignación', validators=[
        DataRequired(message="El motivo es obligatorio"),
        Length(min=10, max=255, message="El motivo debe tener entre 10 y 255 caracteres")
    ])
    
    fecha_devolucion_esperada = DateField(
        'Fecha de Devolución Esperada',
        format='%Y-%m-%d',
        validators=[Optional(), validar_fecha_es],
        render_kw={'placeholder': 'aaaa-mm-dd', 'lang': 'es'}
    )
    
    condiciones_uso = TextAreaField('Condiciones de Uso', validators=[
        Optional(),
        Length(max=1000, message="Las condiciones no pueden exceder 1000 caracteres")
    ])

    empleado_nombre = StringField('Nombre del empleado receptor', validators=[
        DataRequired(message="El nombre del empleado es obligatorio"),
        Length(min=3, max=255, message="El nombre debe tener entre 3 y 255 caracteres")
    ])

    empleado_telefono = StringField('Teléfono del empleado', validators=[
        Optional(),
        Length(max=50, message="El teléfono no puede exceder 50 caracteres")
    ])

    observaciones = TextAreaField('Observaciones', validators=[
        Optional(),
        Length(max=1000, message="Las observaciones no pueden exceder 1000 caracteres")
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
    motivo = SelectField('Motivo', choices=[
        ('obsoleto', 'Obsoleto'),
        ('daniado', 'Dañado'),
        ('extraviado', 'Extraviado'),
        ('otro', 'Otro')
    ], validators=[DataRequired()])
    motivo_otro = StringField('Especifique el motivo', validators=[Length(max=100)], render_kw={"placeholder": "Si selecciona 'Otro', escriba el motivo"})
    descripcion_detallada = TextAreaField('Descripción Detallada', validators=[DataRequired()])
    fecha_baja = DateField('Fecha de Baja', validators=[DataRequired()])  # Selector de fecha
    valor_residual = DecimalField('Valor Residual', validators=[Optional()])
    documento_adjunto = FileField('Documento Adjunto', validators=[
        FileAllowed(['pdf', 'jpg', 'png', 'jpeg'], 'Solo PDF o imagen')
    ])
    submit = SubmitField('Enviar Informe')

    def __init__(self, producto_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from src.inventario.models import Inventario
        if producto_id:
            unidades = Inventario.query.filter(
                Inventario.id == producto_id,
                Inventario.estado != 'dado_de_baja'
            ).all()
            self.uuid_unidad.choices = [(u.uuid, f"{u.uuid} - {u.nombre}") for u in unidades]

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

    documento_baja = FileField('Documento de Respaldo', validators=[
        FileAllowed(['pdf', 'jpg', 'png', 'jpeg', 'doc', 'docx'], 'Solo documentos PDF, DOC o imágenes')
    ])

    observaciones_baja = TextAreaField('Observaciones de Baja', validators=[
        Optional(),
        Length(max=1000, message="Las observaciones no pueden exceder 1000 caracteres")
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
        # Cargar categorías dinámicamente; primer valor 0 para compatibilidad con coerce=int
        categorias_activas = [(c.id, c.nombre) for c in Categoria.query.filter_by(activo=True).all()]
        self.categoria_id.choices = [(0, 'Todas las categorías')] + categorias_activas



