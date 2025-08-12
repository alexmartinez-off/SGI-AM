from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, IntegerField, DecimalField, DateTimeField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from wtforms.widgets import TextArea
from src.inventario.models import Categoria

class ProductoForm(FlaskForm):
    """Formulario para crear/editar productos"""
    nombre = StringField('Nombre del Producto', validators=[
        DataRequired(message="El nombre es obligatorio"),
        Length(min=3, max=255, message="El nombre debe tener entre 3 y 255 caracteres")
    ])
    
    descripcion = TextAreaField('Descripción', validators=[
        DataRequired(message="La descripción es obligatoria"),
        Length(min=10, max=1000, message="La descripción debe tener entre 10 y 1000 caracteres")
    ], widget=TextArea())
    
    categoria_id = SelectField('Categoría', validators=[DataRequired()], coerce=int)
    
    cantidad = IntegerField('Cantidad', validators=[
        DataRequired(message="La cantidad es obligatoria"),
        NumberRange(min=1, message="La cantidad debe ser mayor a 0")
    ], default=1)
    
    ubicacion = StringField('Ubicación', validators=[
        Optional(),
        Length(max=255, message="La ubicación no puede exceder 255 caracteres")
    ])
    
    codigo_barras = StringField('Código de Barras (uuid)', validators=[
        Optional(),
        Length(max=100, message="El código de barras no puede exceder 100 caracteres")
    ])
    
    valor_adquisicion = DecimalField('Valor de Adquisición', validators=[
        Optional(),
        NumberRange(min=0, message="El valor debe ser mayor o igual a 0")
    ], places=2)
    
    proveedor = StringField('Proveedor', validators=[
        Optional(),
        Length(max=255, message="El proveedor no puede exceder 255 caracteres")
    ])
    
    marca = StringField('Marca', validators=[
        DataRequired(message="La marca es obligatoria"),
        Length(max=100, message="La marca no puede exceder 100 caracteres")
    ])
    
    modelo = StringField('Modelo', validators=[
        DataRequired(message="El modelo es obligatorio"),
        Length(max=100, message="El modelo no puede exceder 100 caracteres")
    ])
    
    submit = SubmitField('Guardar Producto')

    def __init__(self, *args, **kwargs):
        super(ProductoForm, self).__init__(*args, **kwargs)
        # Cargar categorías dinámicamente
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

    def __init__(self, *args, **kwargs):
        super(AsignacionForm, self).__init__(*args, **kwargs)
        # Cargar usuarios dinámicamente (excluyendo admins si es necesario)
        from src.accounts.models import User
        self.usuario_asignado_id.choices = [(u.id, f"{u.nombre} {u.apellido} ({u.username})") 
                                          for u in User.query.all()]

class InformeBajaForm(FlaskForm):
    """Formulario para reportar baja de productos"""
    motivo = SelectField('Motivo de Baja', validators=[DataRequired()], choices=[
        ('deterioro', 'Deterioro'),
        ('obsolescencia', 'Obsolescencia'),
        ('perdida', 'Pérdida'),
        ('robo', 'Robo'),
        ('otro', 'Otro')
    ])
    
    descripcion_detallada = TextAreaField('Descripción Detallada', validators=[
        DataRequired(message="La descripción detallada es obligatoria"),
        Length(min=20, max=2000, message="La descripción debe tener entre 20 y 2000 caracteres")
    ], widget=TextArea())
    
    valor_residual = DecimalField('Valor Residual Estimado', validators=[
        Optional(),
        NumberRange(min=0, message="El valor debe ser mayor o igual a 0")
    ], places=2)
    
    documento_adjunto = FileField('Documento Justificante', validators=[
        Optional(),
        FileAllowed(['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'], 
                   'Solo se permiten archivos PDF, DOC, DOCX, JPG, JPEG, PNG')
    ])
    
    submit = SubmitField('Enviar Informe de Baja')

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
