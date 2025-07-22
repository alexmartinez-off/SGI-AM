from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_user, logout_user, login_required
from src.accounts.forms import RegisterForm, LoginForm, TwoFactorForm, ForgotPasswordForm, ResetPasswordForm
from src.accounts.models import User
from src import db, bcrypt
from src.utils import get_b64encoded_qr_image
from functools import wraps
from flask import session, current_app
from flask_mail import Message

# Se crea un Blueprint para el módulo de cuentas (accounts)
accounts_bp = Blueprint("accounts", __name__)

# Constantes para las rutas principales del módulo
HOME_URL = "accounts.home"
SETUP_2FA_URL = "accounts.setup_two_factor_auth"
VERIFY_2FA_URL = "accounts.verify_two_factor_auth"

# Decorador para requerir autenticación de dos factores
def two_factor_required(func):
    """
    Decorador que obliga a que el usuario haya pasado por el 2FA
    antes de acceder a la vista protegida.
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("accounts.login"))
        if not current_user.is_two_factor_authentication_enabled:
            flash("Debes configurar la autenticación en dos pasos.", "warning")
            return redirect(url_for("accounts.setup_two_factor_auth"))
        if not session.get("otp_verified"):
            flash("Debes verificar el OTP antes de continuar.", "warning")
            return redirect(url_for("accounts.verify_two_factor_auth"))
        return func(*args, **kwargs)
    return decorated_view

# Ruta para registrar un nuevo usuario
@accounts_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Registro de usuario. Si ya está autenticado, lo redirige.
    Si no tiene 2FA, lo obliga a configurarlo.
    """
    if current_user.is_authenticated:
        if current_user.is_two_factor_authentication_enabled:
            flash("Ya estás registrado.", "info")
            return redirect(url_for(HOME_URL))
        else:
            flash(
                "No has activado la autenticación en dos pasos. Por favor actívala antes de iniciar sesión. ",
                "info",
            )
            return redirect(url_for(SETUP_2FA_URL))
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        try:
            user = User(
                nombre=form.nombre.data,
                apellido=form.apellido.data,
                username=form.username.data,
                email=form.email.data,
                telefono=form.telefono.data,
                password=form.password.data
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash(
                "Registro exitoso. Debes activar la autenticación en dos pasos antes de continuar. ",
                "success",
            )
            return redirect(url_for(SETUP_2FA_URL))
        except Exception:
            db.session.rollback()
            flash("El registro falló. Por favor intenta de nuevo. ", "danger")
    return render_template("accounts/register.html", form=form)

# Ruta para iniciar sesión
@accounts_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Login de usuario. Si ya está autenticado y tiene 2FA, lo redirige.
    Si no tiene 2FA, lo obliga a configurarlo.
    """
    if current_user.is_authenticated:
        if current_user.is_two_factor_authentication_enabled:
            flash("Ya has iniciado sesión.", "info")
            return redirect(url_for(HOME_URL))
        else:
            flash("No has activado la autenticación en dos pasos. Por favor actívala antes de iniciar sesión. ", "info")
            return redirect(url_for(SETUP_2FA_URL))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            if not current_user.is_two_factor_authentication_enabled:
                flash("No has activado la autenticación en dos pasos. Por favor actívala antes de continuar. ", "info")
                return redirect(url_for(SETUP_2FA_URL))
            return redirect(url_for(VERIFY_2FA_URL))
        elif not user:
            flash("Usuario no registrado. Por favor regístrate. ", "danger")
        else:
            flash("Usuario y/o contraseña incorrectos.", "danger")
    return render_template("accounts/login.html", form=form)

# Ruta para cerrar sesión
@accounts_bp.route("/logout")
@login_required
def logout():
    """
    Cierra la sesión del usuario y elimina la verificación OTP de la sesión.
    """
    logout_user()
    session.pop("otp_verified", None)
    flash("Has cerrado sesión correctamente.", "success")
    return redirect(url_for("accounts.login"))

# Ruta para configurar el 2FA
@accounts_bp.route("/setup-2fa")
@login_required
def setup_two_factor_auth():
    """
    Muestra el QR y el token secreto para configurar la autenticación en dos pasos.
    """
    secret = current_user.secret_token
    uri = current_user.get_authentication_setup_uri()
    base64_qr_image = get_b64encoded_qr_image(uri)
    return render_template(
        "accounts/setup-2fa.html", secret=secret, qr_image=base64_qr_image
    )

# Ruta para verificar el OTP del 2FA
@accounts_bp.route("/verify-2fa", methods=["GET", "POST"])
@login_required
def verify_two_factor_auth():
    """
    Verifica el código OTP ingresado por el usuario.
    Si es correcto, marca la sesión como verificada.
    """
    form = TwoFactorForm(request.form)
    if form.validate_on_submit() and current_user.is_otp_valid(form.otp.data):
        # Marca que ya pasó el 2FA en esta sesión
        session["otp_verified"] = True

        if not current_user.is_two_factor_authentication_enabled:
            current_user.is_two_factor_authentication_enabled = True
            db.session.commit()

        flash("¡Verificación 2FA exitosa! Has iniciado sesión.", "success")
        return redirect(url_for(HOME_URL))

    if form.validate_on_submit():
        flash("OTP inválido. Por favor intenta de nuevo.", "danger")
        return redirect(url_for(VERIFY_2FA_URL))

    if not current_user.is_two_factor_authentication_enabled:
        flash("No has activado la autenticación en dos pasos. Por favor actívala primero.", "info")
    return render_template("accounts/verify-2fa.html", form=form)

# Ruta para listar usuarios (CRUD)
@accounts_bp.route("/usuarios")
@login_required
def listar_usuarios():
    """
    Muestra la lista de usuarios registrados.
    """
    usuarios = User.query.all()
    return render_template("accounts/crud_users.html", usuarios=usuarios)

# Ruta para editar un usuario
@accounts_bp.route("/usuarios/editar/<int:user_id>", methods=["GET", "POST"])
@login_required
def editar_usuario(user_id):
    """
    Permite editar los datos de un usuario.
    """
    usuario = User.query.get_or_404(user_id)
    form = RegisterForm(obj=usuario)
    if form.validate_on_submit():
        usuario.username = form.username.data
        if form.password.data:
            usuario.password = bcrypt.generate_password_hash(form.password.data)
        db.session.commit()
        flash("Usuario actualizado correctamente. ", "success")
        return redirect(url_for("accounts.crud_users"))
    return render_template("accounts/editar_user.html", form=form, usuario=usuario)

# Ruta para eliminar un usuario
@accounts_bp.route("/usuarios/eliminar/<int:user_id>", methods=["POST"])
@login_required
def eliminar_usuario(user_id):
    """
    Elimina un usuario de la base de datos.
    """
    usuario = User.query.get_or_404(user_id)
    db.session.delete(usuario)
    db.session.commit()
    flash("Usuario eliminado correctamente. ", "success")
    return redirect(url_for("accounts.crud_users"))

# Ruta principal (home) protegida por login y 2FA
@accounts_bp.route("/")
@login_required
@two_factor_required
def home():
    """
    Página principal del sistema, solo accesible si el usuario está autenticado y pasó el 2FA.
    """
    return render_template("core/index.html")

# Función para enviar correo de recuperación de contraseña
def send_reset_email(user):
    """
    Envía un correo con el enlace para restablecer la contraseña.
    """
    mail = current_app.extensions['mail']
    token = user.get_reset_token()
    msg = Message(
        "Recuperación de contraseña - SGI",
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email]
    )
    msg.body = f'''Para restablecer tu contraseña, haz clic en el siguiente enlace:
{url_for('accounts.reset_password', token=token, _external=True)}

Si no solicitaste este cambio, ignora este correo.
'''
    mail.send(msg)

# Ruta para solicitar recuperación de contraseña
@accounts_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """
    Permite al usuario solicitar un enlace de recuperación de contraseña.
    """
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
            flash('Se ha enviado un enlace de recuperación a tu correo.', 'info')
        else:
            flash('No existe una cuenta con ese correo electrónico.', 'warning')
        return redirect(url_for('accounts.login'))
    return render_template('accounts/forgot_password.html', form=form)

# Ruta para restablecer la contraseña usando el token recibido por correo
@accounts_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Permite al usuario restablecer su contraseña usando el token enviado por correo.
    """
    user = User.verify_reset_token(token)
    if not user:
        flash('El enlace es inválido o ha expirado.', 'warning')
        return redirect(url_for('accounts.forgot_password'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        db.session.commit()
        flash('Tu contraseña ha sido actualizada. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('accounts.login'))
    return render_template('accounts/reset_password.html', form=form)

