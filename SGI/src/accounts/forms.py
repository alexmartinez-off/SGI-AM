from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, InputRequired, Email

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