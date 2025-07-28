from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField
from wtforms.validators import DataRequired, EqualTo, Length, InputRequired, Email, Optional, ValidationError

from src.accounts.models import User

# Formulario de registro de usuario
class RegisterForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(message="Este campo es obligatorio")])  # Nombre
    apellido = StringField("Apellido", validators=[DataRequired()])  # Apellido
    username = StringField(
        "Nombre de usuario",
        validators=[
            DataRequired(message="Este campo es obligatorio."),
            Length(min=6, max=40, message="Debe tener entre 6 y 40 caracteres."),
        ],
    )  # Nombre de usuario único
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()],
    )  # Correo electrónico único
    telefono = StringField("Teléfono (opcional)")  # Teléfono (opcional)
    rol = SelectField(
        "Rol",
        choices=[('usuario', 'Usuario'), ('admin', 'Administrador')],
        default='usuario',
        validators=[DataRequired()]
    )  # Rol del usuario
    password = PasswordField(
        "Contraseña",
        validators=[
            DataRequired(message="Este campo es obligatorio."),
            Length(min=6, max=25, message="Debe tener entre 6 y 25 caracteres."),
        ],
    )  # Contraseña
    confirm_password = PasswordField(
        "Confirmar contraseña",
        validators=[
            DataRequired(message="Este campo es obligatorio."),
            EqualTo("password", message="Las contraseñas deben coincidir."),
        ],
    )  # Confirmación de contraseña
    submit = SubmitField("Registrarse")  # Botón de registro

    def validate(self, extra_validators=None):
        """
        Validación personalizada para evitar usuarios y correos duplicados.
        """
        initial_validation = super().validate(extra_validators)
        if not initial_validation:
            return False
        user = User.query.filter_by(username=self.username.data).first()
        if user:
            self.username.errors.append("El nombre de usuario ya está registrado.")
            return False
        email_exists = User.query.filter_by(email=self.email.data).first()
        if email_exists:
            self.email.errors.append("Este correo electrónico ya está registrado.")
            return False
        return True

# Formulario para que un usuario edite su propio perfil
class UpdateProfileForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    apellido = StringField('Apellido', validators=[DataRequired()])
    username = StringField('Nombre de usuario', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    telefono = StringField('Teléfono')
    submit = SubmitField('Actualizar Perfil')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Ese nombre de usuario ya está en uso. Por favor, elige otro.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Ese correo electrónico ya está en uso. Por favor, elige otro.')


# Formulario de inicio de sesión
class LoginForm(FlaskForm):
    username = StringField("Nombre de usuario", validators=[DataRequired(message="Este campo es obligatorio.")])  # Usuario
    password = PasswordField("Contraseña", validators=[DataRequired(message="Este campo es obligatorio.")])  # Contraseña

# Formulario para ingresar el código OTP del 2FA
class TwoFactorForm(FlaskForm):
    otp = StringField(
        'Ingrese el código OTP',
        validators=[
            InputRequired(message="Este campo es obligatorio."),
            Length(min=6, max=6, message="El código debe tener 6 dígitos.")
        ]
    )  # Código OTP de 6 dígitos

# Formulario para solicitar recuperación de contraseña
class ForgotPasswordForm(FlaskForm):
    email = StringField(
        'Correo electrónico',
        validators=[DataRequired(message="Este campo es obligatorio."), Email(message="Correo inválido.")]
    )  # Email para recuperación
    submit = SubmitField('Enviar enlace de recuperación')  # Botón de envío

# Formulario para restablecer la contraseña
class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        'Nueva contraseña',
        validators=[
            DataRequired(message="Este campo es obligatorio."),
            Length(min=6, message="La contraseña debe tener al menos 6 caracteres.")
        ]
    )  # Nueva contraseña
    confirm_password = PasswordField(
        'Confirmar contraseña',
        validators=[
            DataRequired(message="Este campo es obligatorio."),
            EqualTo('password', message="Las contraseñas deben coincidir.")
        ]
    )  # Confirmación de nueva contraseña
    submit = SubmitField('Restablecer contraseña')

# Formulario específico para editar usuarios (admin)
class EditUserForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(message="Este campo es obligatorio")])
    apellido = StringField("Apellido", validators=[DataRequired()])
    username = StringField(
        "Nombre de usuario",
        validators=[
            DataRequired(message="Este campo es obligatorio."),
            Length(min=6, max=40, message="Debe tener entre 6 y 40 caracteres."),
        ],
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()],
    )
    telefono = StringField("Teléfono (opcional)")
    rol = SelectField(
        "Rol",
        choices=[('usuario', 'Usuario'), ('admin', 'Administrador')],
        validators=[DataRequired()]
    )
    password = PasswordField(
        "Nueva contraseña (opcional)",
        validators=[]  # Sin validadores automáticos
    )
    confirm_password = PasswordField(
        "Confirmar contraseña",
        validators=[]  # Sin validadores automáticos
    )
    submit = SubmitField("Guardar cambios")

    def __init__(self, original_user_id, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        self.original_user_id = original_user_id

    def validate(self, extra_validators=None):
        # Limpiar errores de contraseña si está vacía
        if not self.password.data or not self.password.data.strip():
            self.password.errors = []
            self.confirm_password.errors = []
        
        # Validar campos básicos (excluyendo contraseña temporalmente)
        # Guardar los validadores originales
        password_validators = self.password.validators
        confirm_password_validators = self.confirm_password.validators
        
        # Temporalmente quitar validadores si el campo está vacío
        if not self.password.data or not self.password.data.strip():
            self.password.validators = []
            self.confirm_password.validators = []
        
        # Ejecutar validación estándar
        initial_validation = super().validate(extra_validators)
        
        # Restaurar validadores
        self.password.validators = password_validators
        self.confirm_password.validators = confirm_password_validators
        
        # Variables de control
        is_valid = True
        
        # Validación condicional de contraseña SOLO si hay datos
        if self.password.data and self.password.data.strip():
            # Validar longitud mínima manualmente
            if len(self.password.data) < 6:
                self.password.errors.append("Debe tener entre 6 y 25 caracteres.")
                is_valid = False
            elif len(self.password.data) > 25:
                self.password.errors.append("Debe tener entre 6 y 25 caracteres.")
                is_valid = False
            
            # Validar confirmación
            if not self.confirm_password.data:
                self.confirm_password.errors.append("Debes confirmar la nueva contraseña.")
                is_valid = False
            elif self.password.data != self.confirm_password.data:
                self.confirm_password.errors.append("Las contraseñas deben coincidir.")
                is_valid = False
        
        # Verificar username duplicado
        user = User.query.filter_by(username=self.username.data).first()
        if user and user.id != self.original_user_id:
            self.username.errors.append("El nombre de usuario ya está registrado.")
            is_valid = False
            
        # Verificar email duplicado
        email_exists = User.query.filter_by(email=self.email.data).first()
        if email_exists and email_exists.id != self.original_user_id:
            self.email.errors.append("Este correo electrónico ya está registrado.")
            is_valid = False
        
        return initial_validation and is_valid

# Formulario para filtros de búsqueda de usuarios
class FiltroUsuariosForm(FlaskForm):
    buscar = StringField(
        'Buscar',
        validators=[Optional()],
        render_kw={'placeholder': 'Buscar por nombre, usuario o email...'}
    )
    rol = SelectField(
        'Filtrar por Rol',
        choices=[('', 'Todos los roles'), ('usuario', 'Usuarios'), ('admin', 'Administradores')],
        default='',
        validators=[Optional()]
    )
    estado_2fa = SelectField(
        'Estado 2FA',
        choices=[('', 'Todos'), ('activo', 'Activado'), ('inactivo', 'Desactivado')],
        default='',
        validators=[Optional()]
    )
    fecha_desde = DateField(
        'Registrado desde',
        validators=[Optional()],
        format='%Y-%m-%d'
    )
    fecha_hasta = DateField(
        'Registrado hasta', 
        validators=[Optional()],
        format='%Y-%m-%d'
    )
    submit = SubmitField('Filtrar')
    limpiar = SubmitField('Limpiar Filtros')