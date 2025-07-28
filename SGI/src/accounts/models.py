from datetime import datetime
import pyotp
from flask_login import UserMixin
from src import db, bcrypt
from config import Config
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

# Importar el modelo de logs
from .models_logs import LogAccion

# Modelo de usuario para la autenticación y gestión de cuentas
class User(UserMixin, db.Model):
    __tablename__ = "users"  # Nombre de la tabla en la base de datos

    # Campos de la tabla
    id = db.Column(db.Integer, primary_key=True)  # ID único del usuario
    nombre = db.Column(db.String(100), nullable=False)  # Nombre del usuario
    apellido = db.Column(db.String(100), nullable=False)  # Apellido del usuario
    username = db.Column(db.String(150), unique=True, nullable=False)  # Nombre de usuario único para iniciar sesión
    email = db.Column(db.String(255), unique=True, nullable=False)  # Email único
    telefono = db.Column(db.String(20))  # Teléfono del usuario (opcional)
    password = db.Column(db.String(255), nullable=False)  # Contraseña hasheada
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Fecha de creación
    is_two_factor_authentication_enabled = db.Column(db.Boolean, default=False)  # ¿Tiene 2FA activado?
    secret_token = db.Column(db.String(255), unique=True)  # Token secreto para 2FA
    rol = db.Column(db.String(50), default='usuario')  # Rol del usuario (admin, usuario)

    def __init__(self, nombre, apellido, username, email, telefono, password, rol='usuario'):
        # Constructor: inicializa los campos y genera el hash de la contraseña y el token secreto 2FA
        self.nombre = nombre
        self.apellido = apellido
        self.username = username
        self.email = email
        self.telefono = telefono
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
        self.secret_token = pyotp.random_base32()
        self.rol = rol

    def get_authentication_setup_uri(self):
        """
        Devuelve el URI para configurar la app de autenticación (Google Authenticator, etc).
        """
        return pyotp.totp.TOTP(self.secret_token).provisioning_uri(
            name=self.username, issuer_name=Config.APP_NAME)

    def is_otp_valid(self, user_otp):
        """
        Verifica si el OTP ingresado por el usuario es válido.
        """
        totp = pyotp.parse_uri(self.get_authentication_setup_uri())
        return totp.verify(user_otp)

    def get_reset_token(self, expires_sec=1800):
        """
        Genera un token seguro para recuperación de contraseña, válido por 30 minutos por defecto.
        """
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        """
        Verifica y decodifica el token de recuperación de contraseña.
        Devuelve el usuario si es válido, o None si es inválido o expiró.
        """
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except Exception:
            return None
        return User.query.get(user_id)

    def is_admin(self):
        """
        Verifica si el usuario tiene rol de administrador.
        """
        return self.rol == 'admin'

    def __repr__(self):
        # Representación legible del usuario (útil para debugging)
        return f"<User {self.username}>"
