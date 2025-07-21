from decouple import config
import os

DATABASE_URI = config("DATABASE_URL")
if DATABASE_URI.startswith("postgres://"):
    DATABASE_URI = DATABASE_URI.replace("postgres://", "postgresql://", 1)


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = config("SECRET_KEY", default="guess-me")
    SQLALCHEMY_DATABASE_URI = config("DATABASE_URL")  
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BCRYPT_LOG_ROUNDS = 13
    WTF_CSRF_ENABLED = True
    DEBUG_TB_ENABLED = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    APP_NAME = config("APP_NAME", default="SGI")
    WTF_I18N_ENABLED = True
    LANGUAGES = ['es']

    MAIL_SERVER = config("MAIL_SERVER")
    MAIL_PORT = config("MAIL_PORT", cast=int)
    MAIL_USE_TLS = config("MAIL_USE_TLS", cast=bool)
    MAIL_USERNAME = config("MAIL_USERNAME")
    MAIL_PASSWORD = config("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = config("MAIL_DEFAULT_SENDER")


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    WTF_CSRF_ENABLED = False
    DEBUG_TB_ENABLED = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///testdb.sqlite"
    BCRYPT_LOG_ROUNDS = 1
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    DEBUG_TB_ENABLED = False