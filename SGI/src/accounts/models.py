
from datetime import datetime
import pyotp
from flask_login import UserMixin
from src import db, bcrypt
from config import Config
from itsdangerous import URLSafeTimedSerializer
from src import db, bcrypt
from flask_login import UserMixin
import pyotp
from config import Config
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from datetime import datetime

# Modelo de Dependencia
class Dependencia(db.Model):
    __tablename__ = 'dependencias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usuarios = db.relationship('User', back_populates='dependencia', lazy='dynamic')

# Modelo de usuario para la autenticación y gestión de cuentas
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    telefono = db.Column(db.String(20))
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_two_factor_authentication_enabled = db.Column(db.Boolean, default=False)
    secret_token = db.Column(db.String(255), unique=True)
    rol = db.Column(db.String(50), default='usuario')
    id_dependencia = db.Column(db.Integer, db.ForeignKey('dependencias.id'))
    dependencia = db.relationship('Dependencia', back_populates='usuarios')

    def __init__(self, nombre, apellido, username, email, telefono, password, rol='usuario', id_dependencia=None):
        self.nombre = nombre
        self.apellido = apellido
        self.username = username
        self.email = email
        self.telefono = telefono
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
        self.secret_token = pyotp.random_base32()
        self.rol = rol
        self.id_dependencia = id_dependencia

    def get_authentication_setup_uri(self):
        return pyotp.totp.TOTP(self.secret_token).provisioning_uri(
            name=self.username, issuer_name=Config.APP_NAME)

    def is_otp_valid(self, user_otp):
        totp = pyotp.parse_uri(self.get_authentication_setup_uri())
        return totp.verify(user_otp)

    def get_reset_token(self, expires_sec=1800):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except Exception:
            return None
        return User.query.get(user_id)

    def is_admin(self):
        return self.rol == 'admin'

    def __repr__(self):
        return f"<User {self.username}>"

