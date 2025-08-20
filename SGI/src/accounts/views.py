from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_user, logout_user, login_required
from src.accounts.forms import RegisterForm, LoginForm, TwoFactorForm, ForgotPasswordForm, ResetPasswordForm, EditUserForm, FiltroUsuariosForm, UpdateProfileForm
from src.accounts.models import User
from src.accounts.models_logs import LogAccion
from src import db, bcrypt
from src.utils import get_b64encoded_qr_image
from functools import wraps
from flask import session, current_app
from flask_mail import Message

# Se crea un Blueprint para el módulo de cuentas (accounts)
accounts_bp = Blueprint("accounts", __name__)

# Constantes para las rutas principales del módulo
HOME_URL = "accounts.profile"
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

# Decorador para requerir permisos de administrador
def admin_required(func):
    """
    Decorador que verifica si el usuario tiene permisos de administrador.
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash("No tienes permisos para acceder a esta página.", "danger")
            return redirect(url_for(HOME_URL))
        return func(*args, **kwargs)
    return decorated_function

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
                password=form.password.data,
               
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

# Ruta para listar usuarios (CRUD) - Solo administradores
@accounts_bp.route("/usuarios", methods=["GET", "POST"])
@login_required
@admin_required
def listar_usuarios():
    """
    Muestra la lista de usuarios registrados con filtros de búsqueda. Solo accesible para administradores.
    """
    from sqlalchemy import or_, and_
    from datetime import datetime
    
    form = FiltroUsuariosForm()
    
    # Construir consulta base
    query = User.query
    
    # Aplicar filtros si el formulario fue enviado
    if form.validate_on_submit():
        # Filtro de búsqueda por texto
        if form.buscar.data:
            search_term = f"%{form.buscar.data}%"
            query = query.filter(
                or_(
                    User.nombre.ilike(search_term),
                    User.apellido.ilike(search_term),
                    User.username.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )
        
        # Filtro por rol
        if form.rol.data:
            query = query.filter(User.rol == form.rol.data)
        
        # Filtro por estado 2FA
        if form.estado_2fa.data:
            if form.estado_2fa.data == 'activo':
                query = query.filter(User.is_two_factor_authentication_enabled == True)
            elif form.estado_2fa.data == 'inactivo':
                query = query.filter(User.is_two_factor_authentication_enabled == False)
        
        # Filtro por fecha de registro
        if form.fecha_desde.data:
            query = query.filter(User.created_at >= form.fecha_desde.data)
        
        if form.fecha_hasta.data:
            # Agregar 23:59:59 al día seleccionado
            fecha_hasta = datetime.combine(form.fecha_hasta.data, datetime.max.time())
            query = query.filter(User.created_at <= fecha_hasta)
    
    # Obtener usuarios ordenados por fecha de creación (más recientes primero)
    usuarios = query.order_by(User.created_at.desc()).all()
    
    # Registrar acceso al módulo de gestión de usuarios
    LogAccion.registrar_accion(
        usuario_id=current_user.id,
        accion='consultar',
        tabla_afectada='users',
        descripcion=f'Consultó la lista de usuarios (total: {len(usuarios)})'
    )
    
    return render_template("accounts/crud_users.html", usuarios=usuarios, form=form)

# Ruta para crear un nuevo usuario desde el panel de administración
@accounts_bp.route("/usuarios/crear", methods=["GET", "POST"])
@login_required
@admin_required
def crear_usuario():
    """
    Permite a un administrador crear un nuevo usuario.
    """
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            user = User(
                nombre=form.nombre.data,
                apellido=form.apellido.data,
                username=form.username.data,
                email=form.email.data,
                telefono=form.telefono.data,
                password=form.password.data,
                rol=form.rol.data
            )
            db.session.add(user)
            db.session.commit()
            
            # Registrar la acción de creación
            LogAccion.registrar_accion(
                usuario_id=current_user.id,
                accion='crear',
                tabla_afectada='users',
                registro_id=user.id,
                datos_nuevos={
                    'nombre': user.nombre,
                    'apellido': user.apellido,
                    'username': user.username,
                    'email': user.email,
                    'rol': user.rol
                },
                descripcion=f'Creó el usuario {user.username} ({user.nombre} {user.apellido})'
            )
            
            flash("Usuario creado exitosamente.", "success")
            return redirect(url_for("accounts.listar_usuarios"))
        except Exception as e:
            db.session.rollback()
            flash("Error al crear el usuario. Inténtalo de nuevo.", "danger")
    return render_template("accounts/crear_usuario.html", form=form)

# Ruta para editar un usuario - Solo administradores
@accounts_bp.route("/usuarios/editar/<int:user_id>", methods=["GET", "POST"])
@login_required
@admin_required
def editar_usuario(user_id):
    """
    Permite editar los datos de un usuario. Solo accesible para administradores.
    """
    usuario = User.query.get_or_404(user_id)
    form = EditUserForm(original_user_id=user_id, obj=usuario)
    
    if request.method == 'POST' and form.validate():
        # Guardar datos anteriores para el log
        datos_anteriores = {
            'nombre': usuario.nombre,
            'apellido': usuario.apellido,
            'username': usuario.username,
            'email': usuario.email,
            'telefono': usuario.telefono,
            'rol': usuario.rol
        }
        
        # Actualizar datos
        usuario.nombre = form.nombre.data
        usuario.apellido = form.apellido.data
        usuario.username = form.username.data
        usuario.email = form.email.data
        usuario.telefono = form.telefono.data
        usuario.rol = form.rol.data
        
        # Solo actualizar contraseña si se proporcionó una nueva
        if form.password.data and form.password.data.strip():
            usuario.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        db.session.commit()
        
        # Datos nuevos para el log
        datos_nuevos = {
            'nombre': usuario.nombre,
            'apellido': usuario.apellido,
            'username': usuario.username,
            'email': usuario.email,
            'telefono': usuario.telefono,
            'rol': usuario.rol
        }
        
        # Registrar la acción de edición
        LogAccion.registrar_accion(
            usuario_id=current_user.id,
            accion='editar',
            tabla_afectada='users',
            registro_id=usuario.id,
            datos_anteriores=datos_anteriores,
            datos_nuevos=datos_nuevos,
            descripcion=f'Editó el usuario {usuario.username} ({usuario.nombre} {usuario.apellido})'
        )
        
        flash("Usuario actualizado correctamente.", "success")
        return redirect(url_for("accounts.listar_usuarios"))
    
    return render_template("accounts/editar_usuario.html", form=form, usuario=usuario)

# Ruta para eliminar un usuario - Solo administradores
@accounts_bp.route("/usuarios/eliminar/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def eliminar_usuario(user_id):
    """
    Elimina un usuario de la base de datos. Solo accesible para administradores.
    """
    usuario = User.query.get_or_404(user_id)
    # Prevenir que un administrador se elimine a sí mismo
    if usuario.id == current_user.id:
        flash("No puedes eliminar tu propia cuenta.", "warning")
        return redirect(url_for("accounts.listar_usuarios"))
    
    # Guardar datos del usuario para el log antes de eliminarlo
    datos_eliminados = {
        'nombre': usuario.nombre,
        'apellido': usuario.apellido,
        'username': usuario.username,
        'email': usuario.email,
        'telefono': usuario.telefono,
        'rol': usuario.rol,
        'fecha_creacion': usuario.created_at.isoformat() if usuario.created_at else None
    }
    
    usuario_eliminado_info = f"{usuario.username} ({usuario.nombre} {usuario.apellido})"
    
    db.session.delete(usuario)
    db.session.commit()
    
    # Registrar la acción de eliminación
    LogAccion.registrar_accion(
        usuario_id=current_user.id,
        accion='eliminar',
        tabla_afectada='users',
        registro_id=user_id,
        datos_anteriores=datos_eliminados,
        descripcion=f'Eliminó el usuario {usuario_eliminado_info}'
    )
    
    flash("Usuario eliminado correctamente.", "success")
    return redirect(url_for("accounts.listar_usuarios"))

# Ruta para ver los logs de acciones - Solo administradores
@accounts_bp.route("/logs", methods=["GET"])
@login_required
@admin_required
def ver_logs():
    """
    Muestra el historial de acciones administrativas.
    """
    # Obtener parámetros de filtrado
    accion_filtro = request.args.get('accion', '')
    usuario_filtro = request.args.get('usuario', '')
    fecha_desde = request.args.get('fecha_desde', '')
    fecha_hasta = request.args.get('fecha_hasta', '')
    
    # Construir consulta
    query = LogAccion.query
    
    if accion_filtro:
        query = query.filter(LogAccion.accion == accion_filtro)
    
    if usuario_filtro:
        query = query.join(User).filter(User.username.ilike(f'%{usuario_filtro}%'))
    
    if fecha_desde:
        try:
            from datetime import datetime
            fecha = datetime.strptime(fecha_desde, '%Y-%m-%d')
            query = query.filter(LogAccion.fecha_hora >= fecha)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            from datetime import datetime
            fecha = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            # Incluir todo el día
            fecha_fin = fecha.replace(hour=23, minute=59, second=59)
            query = query.filter(LogAccion.fecha_hora <= fecha_fin)
        except ValueError:
            pass
    
    # Obtener logs ordenados por fecha (más recientes primero)
    logs = query.order_by(LogAccion.fecha_hora.desc()).limit(500).all()
    
    # Obtener listas para filtros
    acciones_disponibles = db.session.query(LogAccion.accion).distinct().all()
    acciones_disponibles = [accion[0] for accion in acciones_disponibles]
    
    # Registrar que se consultaron los logs
    LogAccion.registrar_accion(
        usuario_id=current_user.id,
        accion='consultar',
        tabla_afectada='logs_acciones',
        descripcion='Consultó el historial de logs de acciones'
    )
    
    return render_template("accounts/logs_acciones.html", 
                         logs=logs, 
                         acciones_disponibles=acciones_disponibles,
                         filtros={
                             'accion': accion_filtro,
                             'usuario': usuario_filtro,
                             'fecha_desde': fecha_desde,
                             'fecha_hasta': fecha_hasta
                         })

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

# Ruta para "Mi Perfil"
@accounts_bp.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    """
    Permite al usuario ver y editar su propio perfil.
    """
    form = UpdateProfileForm()
    if form.validate_on_submit():
        current_user.nombre = form.nombre.data
        current_user.apellido = form.apellido.data
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.telefono = form.telefono.data
        db.session.commit()
        flash('Tu perfil ha sido actualizado.', 'success')
        return redirect(url_for('accounts.profile'))
    elif request.method == 'GET':
        form.nombre.data = current_user.nombre
        form.apellido.data = current_user.apellido
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.telefono.data = current_user.telefono
    return render_template('accounts/profile.html', title='Mi Perfil', form=form)


