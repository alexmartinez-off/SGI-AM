from decouple import config
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import pymysql
from flask_mail import Mail
from config import DevelopmentConfig, ProductionConfig, TestingConfig

# Carga segura según entorno
env_config = config("APP_SETTINGS", default="DevelopmentConfig")

if env_config == "DevelopmentConfig":
    app_config = DevelopmentConfig
elif env_config == "ProductionConfig":
    app_config = ProductionConfig
elif env_config == "TestingConfig":
    app_config = TestingConfig
else:
    raise Exception("APP_SETTINGS no es válido. Usa: DevelopmentConfig, ProductionConfig o TestingConfig")

# Crear la app y aplicar la configuración
app = Flask(__name__)
app.config.from_object(app_config)

# Para compatibilidad con MySQL
pymysql.install_as_MySQLdb()

# Inicializar extensiones
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "accounts.login"
login_manager.login_message_category = "danger"

# Importar modelos (necesario para Flask-Login y migraciones)
from src.accounts.models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Registrar blueprints
from src.accounts.views import accounts_bp
from src.core.views import core_bp

app.register_blueprint(accounts_bp)
app.register_blueprint(core_bp)
