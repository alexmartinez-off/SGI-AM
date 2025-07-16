from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_user, logout_user, login_required
from src.accounts.forms import RegisterForm, LoginForm, TwoFactorForm
from src.accounts.models import User
from src import db, bcrypt
from src.utils import get_b64encoded_qr_image

accounts_bp = Blueprint("accounts", __name__)

HOME_URL = "core.home"
SETUP_2FA_URL = "accounts.setup_two_factor_auth"
VERIFY_2FA_URL = "accounts.verify_two_factor_auth"


@accounts_bp.route("/register", methods=["GET", "POST"])
def register():
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









@accounts_bp.route("/login", methods=["GET", "POST"])
def login():
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


@accounts_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesión correctamente. ", "success")
    return redirect(url_for("accounts.login"))


@accounts_bp.route("/setup-2fa")
@login_required
def setup_two_factor_auth():
    secret = current_user.secret_token
    uri = current_user.get_authentication_setup_uri()
    base64_qr_image = get_b64encoded_qr_image(uri)
    return render_template(
        "accounts/setup-2fa.html", secret=secret, qr_image=base64_qr_image
    )


@accounts_bp.route("/verify-2fa", methods=["GET", "POST"])
@login_required
def verify_two_factor_auth():
    form = TwoFactorForm(request.form)
    if form.validate_on_submit():
        if current_user.is_otp_valid(form.otp.data):
            if current_user.is_two_factor_authentication_enabled:
                flash("¡Verificación 2FA exitosa! Has iniciado sesión. " , "success")
                return redirect(url_for(HOME_URL))
            else:
                try:
                    current_user.is_two_factor_authentication_enabled = True
                    db.session.commit()
                    flash("¡Configuración de 2FA exitosa! Has iniciado sesión. ", "success")
                    return redirect(url_for(HOME_URL))
                except Exception:
                    db.session.rollback()
                    flash("La configuración de 2FA falló. Por favor intenta de nuevo. ", "danger")
                    return redirect(url_for(VERIFY_2FA_URL))
        else:
            flash("OTP inválido. Por favor intenta de nuevo.", "danger")
            return redirect(url_for(VERIFY_2FA_URL))
    else:
        if not current_user.is_two_factor_authentication_enabled:
            flash(
                "No has activado la autenticación en dos pasos. Por favor actívala primero. ",
                "info",
            )
        return render_template("accounts/verify-2fa.html", form=form)

@accounts_bp.route("/usuarios")
@login_required
def listar_usuarios():
    usuarios = User.query.all()
    return render_template("accounts/crud_users.html", usuarios=usuarios)

@accounts_bp.route("/usuarios/editar/<int:user_id>", methods=["GET", "POST"])
@login_required
def editar_usuario(user_id):
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

@accounts_bp.route("/usuarios/eliminar/<int:user_id>", methods=["POST"])
@login_required
def eliminar_usuario(user_id):
    usuario = User.query.get_or_404(user_id)
    db.session.delete(usuario)
    db.session.commit()
    flash("Usuario eliminado correctamente. ", "success")
    return redirect(url_for("accounts.crud_users"))