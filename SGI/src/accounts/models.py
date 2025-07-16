from datetime import datetime
import pyotp
from flask_login import UserMixin
from src import db, bcrypt
from config import Config


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

    def __init__(self, nombre, apellido, username, email, telefono, password):
        self.nombre = nombre
        self.apellido = apellido
        self.username = username
        self.email = email
        self.telefono = telefono
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
        self.secret_token = pyotp.random_base32()

    def get_authentication_setup_uri(self):
        return pyotp.totp.TOTP(self.secret_token).provisioning_uri(
            name=self.username, issuer_name=Config.APP_NAME)

    def is_otp_valid(self, user_otp):
        totp = pyotp.parse_uri(self.get_authentication_setup_uri())
        return totp.verify(user_otp)

    def __repr__(self):
        return f"<User {self.username}>"
