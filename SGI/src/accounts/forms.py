from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, InputRequired, Email

from src.accounts.models import User


class RegisterForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired()])
    apellido = StringField("Apellido", validators=[DataRequired()])
    username = StringField(
        "Nombre de usuario",
        validators=[
            DataRequired(message="Este campo es obligatorio."),
            Length(min=6, max=40, message="Debe tener entre 6 y 40 caracteres."),
        ],
    )
    email = StringField("Email", validators=[DataRequired(), Email()
        ],
    )
        
    telefono = StringField("Teléfono (opcional)")
    password = PasswordField(
        "Contraseña",
        validators=[
            DataRequired(message="Este campo es obligatorio."),
            Length(min=6, max=25, message="Debe tener entre 6 y 25 caracteres."),
        ],
    )
    confirm_password = PasswordField(
        "Confirmar contraseña",
        validators=[
            DataRequired(message="Este campo es obligatorio."),
            EqualTo("password", message="Las contraseñas deben coincidir."),
        ],
    )
    submit = SubmitField("Registrarse")

    def validate(self, extra_validators=None):
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


class LoginForm(FlaskForm):
    username = StringField("Nombre de usuario", validators=[DataRequired(message="Este campo es obligatorio.")])
    password = PasswordField("Contraseña", validators=[DataRequired(message="Este campo es obligatorio.")])

class TwoFactorForm(FlaskForm):
    otp = StringField('Ingrese el código OTP', validators=[InputRequired(message="Este campo es obligatorio."), Length(min=6, max=6, message="El código debe tener 6 dígitos.")])