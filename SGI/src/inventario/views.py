from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from urllib.parse import urlencode
from flask_login import login_required, current_user
from sqlalchemy import func, desc, or_
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation

from src import db
from src.inventario.models import Inventario, Categoria, Historial, InformeBaja, Asignacion
from src.inventario.forms import (ProductoForm, CategoriaForm, AsignacionForm, 
                                InformeBajaForm, CambiarEstadoForm, FiltroInventarioForm,
                                OrdenEntradaForm)
from src.accounts.views import admin_required
from src.accounts.models import User

# Crear el blueprint para inventario
inventario_bp = Blueprint('inventario', __name__)
@inventario_bp.route('/orden-entrada/nueva', methods=['GET', 'POST'])
@login_required
def crear_orden_entrada():
    """Formulario tipo planilla para registrar una Orden de Entrada.
    Crea productos (Inventario) por cada fila con cantidad > 0.
    """
    form = OrdenEntradaForm()
    # Permitir ajustar dinámicamente la cantidad de filas (items)
    filas = request.args.get('filas', type=int)
    if filas and 1 <= filas <= 50:
        # Asegurar que FieldList tenga 'filas' entradas
        actual = len(form.items)
        if filas > actual:
            for _ in range(filas - actual):
                form.items.append_entry()
    # Re-forzar las opciones de categoría en todos los renglones (incluidos los recién añadidos)
    categorias = [(0, 'Seleccione categoría')] + [(c.id, c.nombre) for c in Categoria.query.filter_by(activo=True).all()]
    for item in form.items:
        try:
            item.form.categoria_id.choices = categorias
        except Exception:
            pass
    if form.validate_on_submit():
        total_creados = 0
        for item_form in form.items:
            detalle = item_form.form.detalle.data
            cantidad = item_form.form.cantidad.data or 0
            precio_unit = item_form.form.precio_unitario.data or 0
            categoria_id = item_form.form.categoria_id.data or None
            if cantidad and cantidad > 0 and detalle:
                for _ in range(cantidad):
                    prod = Inventario(
                        nombre=detalle,
                        descripcion=f"Orden #{form.numero_orden.data or ''} - {form.senor.data or ''}",
                        categoria_id=categoria_id,
                        precio=precio_unit,
                        estado='en_bodega',
                        fecha_registro=datetime.utcnow(),
                        ubicacion='Bodega'
                    )
                    db.session.add(prod)
                    db.session.flush()
                    registrar_accion_historial(
                        prod.id,
                        'creado',
                        f'Entrada por orden: {form.numero_orden.data or "N/A"}'
                    )
                    total_creados += 1
        db.session.commit()
        flash(f'Orden registrada. Productos creados: {total_creados}', 'success')
        return redirect(url_for('inventario.listar_productos'))
    return render_template('inventario/orden_entrada.html', form=form)

@inventario_bp.route('/producto/<int:id>/cambiar_estado', methods=['GET', 'POST'])
@login_required
def cambiar_estado_producto(id):
    producto = Inventario.query.get_or_404(id)
    form = CambiarEstadoForm()
    if form.validate_on_submit():
        estado_anterior = producto.estado
        estado_nuevo = form.estado_nuevo.data
        if estado_anterior != estado_nuevo:
            producto.estado = estado_nuevo
            informe_generado = None
            if estado_nuevo == 'dado_de_baja':
                informe_generado = InformeBaja(
                    producto_id=id,
                    usuario_id=current_user.id,
                    motivo='otro',
                    descripcion_detallada=form.descripcion.data,
                    fecha_baja=datetime.utcnow(),
                    estado_informe='pendiente',
                    aprobado=False
                )
                documento_guardado = guardar_documento_informe(form.documento_baja.data)
                if documento_guardado:
                    informe_generado.documento_adjunto = documento_guardado
                if form.observaciones_baja.data:
                    informe_generado.comentarios_aprobacion = form.observaciones_baja.data
                db.session.add(informe_generado)
            registrar_accion_historial(
                producto.id,
                'cambio_estado',
                form.descripcion.data,
                estado_anterior=estado_anterior,
                estado_nuevo=estado_nuevo
            )
            db.session.commit()
            if informe_generado:
                flash('Producto marcado como dado de baja y se generó un informe pendiente de aprobación.', 'info')
            else:
                flash(f'Estado del producto cambiado de "{producto.estado_display}" a "{form.estado_nuevo.data}"', 'success')
            return redirect(url_for('inventario.ver_producto', id=producto.id))
        else:
            flash('El estado seleccionado es el mismo que el actual', 'warning')
    return render_template('inventario/cambiar_estado.html', form=form, producto=producto)
def registrar_accion_historial(producto_id, accion, descripcion, estado_anterior=None, estado_nuevo=None):
    """Función auxiliar para registrar acciones en el historial"""
    historial = Historial(
        producto_id=producto_id,
        usuario_id=current_user.id,
        accion=accion,
        descripcion=descripcion,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo
    )
    db.session.add(historial)

def guardar_documento_informe(archivo):
    if not archivo or not hasattr(archivo, 'filename') or not archivo.filename:
        return None
    filename = secure_filename(archivo.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{filename}"
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'informes_baja')
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, filename)
    archivo.save(file_path)
    return filename

@inventario_bp.route('/producto/<int:id>')
@login_required
def ver_producto(id):
    producto = Inventario.query.get_or_404(id)
    historial = Historial.query.filter_by(producto_id=id).order_by(desc(Historial.fecha)).all()
    asignaciones = Asignacion.query.filter_by(producto_id=id).order_by(desc(Asignacion.fecha_asignacion)).all()
    ultima_asignacion = asignaciones[0] if asignaciones else None
    return render_template(
        'inventario/ver_producto.html',
        producto=producto,
        historial=historial,
        asignaciones=asignaciones,
        ultima_asignacion=ultima_asignacion
    )

@inventario_bp.route('/dashboard_inventario')
@login_required
def dashboard_inventario():
    try:
        estadisticas = {
            "total": Inventario.query.count(),
            "disponibles": Inventario.query.filter_by(estado='en_bodega').count(),
            "asignados": Inventario.query.filter_by(estado='en_uso').count(),
            "mantenimiento": Inventario.query.filter_by(estado='daniado').count(),
            "nuevos_mes": Inventario.query.filter(
                Inventario.fecha_registro >= datetime.utcnow().replace(day=1)
            ).count(),
            "asignaciones_mes": Historial.query.filter(
                Historial.accion == 'asignado',
                Historial.fecha >= datetime.utcnow().replace(day=1)
            ).count(),
            "mantenimientos_mes": Historial.query.filter(
                Historial.accion == 'mantenimiento',
                Historial.fecha >= datetime.utcnow().replace(day=1)
            ).count(),
            "bajas_mes": Historial.query.filter(
                Historial.accion == 'dado_de_baja',
                Historial.fecha >= datetime.utcnow().replace(day=1)
            ).count(),
            "por_categoria": [
                {
                    "nombre": cat.nombre,
                    "cantidad": cat.cantidad
                } for cat in db.session.query(
                    Categoria.nombre,
                    func.count(Inventario.id).label('cantidad')
                ).outerjoin(Inventario).group_by(Categoria.id, Categoria.nombre).all()
            ]
        }
    except Exception as e:
        estadisticas = {
            "total": 0,
            "disponibles": 0,
            "asignados": 0,
            "mantenimiento": 0,
            "nuevos_mes": 0,
            "asignaciones_mes": 0,
            "mantenimientos_mes": 0,
            "bajas_mes": 0,
            "por_categoria": []
        }
        flash(f'Error cargando estadísticas: {str(e)}', 'danger')

    actividad_reciente = Historial.query.order_by(Historial.fecha.desc()).limit(10).all() if 'Historial' in globals() else []

    return render_template(
        'inventario/dashboard.html',
        estadisticas=estadisticas,
        actividad_reciente=actividad_reciente
    )

@inventario_bp.route('/productos')
@login_required
def listar_productos():
    """Lista todos los productos con filtros"""
    form = FiltroInventarioForm()
    
    # Construir query base (outerjoin para tolerar productos sin categoría asignada)
    query = Inventario.query.outerjoin(Categoria)

    # Aplicar filtros si existen (con casteo y validaciones)
    nombre = request.args.get('nombre', type=str)
    if nombre:
        query = query.filter(Inventario.nombre.contains(nombre))

    categoria_id = request.args.get('categoria_id', type=int)
    if categoria_id and categoria_id > 0:
        query = query.filter(Inventario.categoria_id == categoria_id)

    estado = request.args.get('estado', type=str)
    estados_validos = {'en_bodega', 'en_uso', 'daniado', 'dado_de_baja'}
    if estado in estados_validos:
        query = query.filter(Inventario.estado == estado)
    
    if request.args.get('usuario_asignado'):
        from src.accounts.models import User
        usuarios = User.query.filter(or_(
            User.nombre.contains(request.args.get('usuario_asignado')),
            User.apellido.contains(request.args.get('usuario_asignado')),
            User.username.contains(request.args.get('usuario_asignado'))
        )).all()
        if usuarios:
            usuario_ids = [u.id for u in usuarios]
            query = query.filter(Inventario.usuario_asignado_id.in_(usuario_ids))
    
    page = request.args.get('page', 1, type=int)
    productos = query.order_by(desc(Inventario.fecha_registro)).paginate(page=page, per_page=20)

    # Querystring seguro para paginación (excluye 'page')
    base_args = request.args.to_dict(flat=True)
    base_args.pop('page', None)
    qs = urlencode(base_args)
    
    # Obtener categorías para los filtros y la vista
    categorias = Categoria.query.filter_by(activo=True).all()
    
    # Calcula las estadísticas
    estadisticas = {
        "total": Inventario.query.count(),
        "disponibles": Inventario.query.filter_by(estado='en_bodega').count(),
        "asignados": Inventario.query.filter_by(estado='en_uso').count(),
        "mantenimiento": Inventario.query.filter_by(estado='daniado').count(),
    }

    return render_template(
        'inventario/listar_productos.html',
        productos=productos,
        categorias=categorias,
        estadisticas=estadisticas,
    form=form,
    qs=qs
    )

@inventario_bp.route('/producto/nuevo', methods=['GET', 'POST'])
@login_required
def crear_producto():
    form = ProductoForm()
    if form.validate_on_submit():
        # Crear una o varias unidades según cantidad
        cantidad = form.cantidad.data or 1
        for _ in range(cantidad):
            producto = Inventario(
                nombre=form.nombre.data,
                descripcion=form.descripcion.data,
                categoria_id=form.categoria_id.data,
                precio=form.precio.data,
                estado='en_bodega',
                fecha_registro=datetime.utcnow(),
                ubicacion=form.ubicacion.data,
                marca=form.marca.data,
                modelo=form.modelo.data,
                cantidad=1
            )
            db.session.add(producto)
            db.session.flush()
            registrar_accion_historial(
                producto.id,
                'creado',
                f'Producto creado: {producto.nombre}'
            )
        db.session.commit()
        flash('Producto(s) creado(s) exitosamente', 'success')
        return redirect(url_for('inventario.listar_productos'))
    return render_template('inventario/crear_producto.html', form=form, producto=None)


@inventario_bp.route('/producto/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_producto(id):
    producto = Inventario.query.get_or_404(id)
    if producto.estado == 'dado_de_baja':
        flash('No se puede editar un producto que ya fue dado de baja.', 'warning')
        return redirect(url_for('inventario.ver_producto', id=producto.id))
    form = ProductoForm(obj=producto)
    form.cantidad.data = producto.cantidad or 1
    try:
        precio_valido = Decimal(str(producto.precio)) if producto.precio is not None else None
    except (InvalidOperation, TypeError):
        precio_valido = None
    form.precio.data = precio_valido

    if form.validate_on_submit():
        # Registrar cambios en historial
        cambios = []
        if producto.nombre != form.nombre.data:
            cambios.append(f"Nombre: {producto.nombre} → {form.nombre.data}")
        if producto.categoria_id != form.categoria_id.data:
            cambios.append('Categoría actualizada')
        if producto.precio != form.precio.data:
            cambios.append(f"Precio: {producto.precio} → {form.precio.data}")
        if producto.descripcion != form.descripcion.data:
            cambios.append('Descripción actualizada')
        if producto.ubicacion != form.ubicacion.data:
            cambios.append('Ubicación actualizada')
        if producto.marca != form.marca.data:
            cambios.append('Marca actualizada')
        if producto.modelo != form.modelo.data:
            cambios.append('Modelo actualizado')
        if producto.cantidad != form.cantidad.data:
            cambios.append(f"Cantidad: {producto.cantidad} → {form.cantidad.data}")

        form.populate_obj(producto)
        producto.cantidad = form.cantidad.data

        if cambios:
            registrar_accion_historial(
                producto.id,
                'editado',
                'Producto editado. ' + ' '.join(cambios)
            )

        db.session.commit()
        flash('Producto actualizado exitosamente', 'success')
        return redirect(url_for('inventario.ver_producto', id=producto.id))

    return render_template('inventario/crear_producto.html', form=form, producto=producto)

@inventario_bp.route('/producto/<int:id>/asignar', methods=['GET', 'POST'])
@login_required
@admin_required
def asignar_producto(id):
    """Asignar una unidad específica de producto a un usuario"""
    producto = Inventario.query.get_or_404(id)
    form = AsignacionForm(producto_id=id)
    asignaciones_previas = Asignacion.query.filter_by(producto_id=id).order_by(desc(Asignacion.fecha_asignacion)).limit(5).all()
    ahora = datetime.utcnow()

    if not form.uuid_unidad.choices:
        flash('No hay unidades disponibles para asignar en este momento.', 'warning')
        return redirect(url_for('inventario.ver_producto', id=producto.id))

    if form.validate_on_submit():
        unidad = Inventario.query.filter_by(uuid=form.uuid_unidad.data).first()
        if not unidad:
            flash('La unidad seleccionada ya no está disponible.', 'danger')
            return redirect(url_for('inventario.ver_producto', id=producto.id))

        Asignacion.query.filter_by(producto_id=unidad.id, activa=True).update({"activa": False}, synchronize_session=False)
        asignacion = Asignacion(
            producto_id=unidad.id,
            usuario_asignado_id=form.usuario_asignado_id.data,
            asignado_por=current_user.id,
            motivo_asignacion=form.motivo_asignacion.data,
            fecha_devolucion_esperada=form.fecha_devolucion_esperada.data,
            condiciones_uso=form.condiciones_uso.data,
            fecha_asignacion=datetime.utcnow(),
            empleado_nombre=form.empleado_nombre.data,
            empleado_telefono=form.empleado_telefono.data,
            observaciones=form.observaciones.data,
            activa=True
        )

        unidad.usuario_asignado_id = form.usuario_asignado_id.data
        unidad.fecha_asignacion = datetime.utcnow()
        unidad.estado = 'en_uso'

        db.session.add(asignacion)

        from src.accounts.models import User
        usuario = User.query.get(form.usuario_asignado_id.data)
        registrar_accion_historial(
            unidad.id,
            'asignado',
            f'Unidad asignada a {usuario.nombre} {usuario.apellido} ({usuario.username}). Motivo: {form.motivo_asignacion.data}'
        )

        db.session.commit()
        flash('Unidad asignada exitosamente', 'success')
        return redirect(url_for('inventario.ver_producto', id=unidad.id))


    return render_template(
        'inventario/asignar_producto.html',
        form=form,
        producto=producto,
        asignaciones_previas=asignaciones_previas,
        ahora=ahora
    )

@inventario_bp.route('/producto/<int:id>/informe_baja', methods=['GET', 'POST'])
@login_required
def crear_informe_baja(id):
    """Crear informe de baja para un producto"""
    producto = Inventario.query.get_or_404(id)
    form = InformeBajaForm(producto_id=id)
    if form.validate_on_submit():
        # Lógica de validación de informe: siempre pendiente para revisión
        estado_informe = 'pendiente'
        motivo_final = form.motivo_otro.data if form.motivo.data == 'otro' and form.motivo_otro.data else form.motivo.data
        informe = InformeBaja(
            producto_id=id,
            usuario_id=current_user.id,
            motivo=motivo_final,
            descripcion_detallada=form.descripcion_detallada.data,
            fecha_baja=form.fecha_baja.data,
            valor_residual=form.valor_residual.data,
            estado_informe=estado_informe,
            estado_previo=producto.estado
        )
        # Manejar archivo adjunto si existe
        documento_guardado = guardar_documento_informe(form.documento_adjunto.data)
        if documento_guardado:
            informe.documento_adjunto = documento_guardado
        db.session.add(informe)
        db.session.commit()
        flash('Informe de baja creado y enviado para revisión de un administrador.', 'info')
        return redirect(url_for('inventario.ver_producto', id=producto.id))
    return render_template('inventario/informe_baja.html', form=form, producto=producto)

@inventario_bp.route('/categorias', methods=['GET', 'POST'])
@login_required
def listar_categorias():
    """Lista todas las categorías y permite crear/editar desde el modal"""
    if request.method == 'POST':
        categoria_id = request.form.get('categoria_id')
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        activa_input = request.form.get('activa')
        activa = activa_input in ('on', 'true', '1', 'True')

        if not nombre:
            flash('El nombre de la categoría es obligatorio.', 'warning')
            return redirect(url_for('inventario.listar_categorias'))

        if categoria_id:
            categoria = Categoria.query.get(categoria_id)
            if not categoria:
                flash('Categoría no encontrada.', 'warning')
                return redirect(url_for('inventario.listar_categorias'))
            categoria.nombre = nombre
            categoria.descripcion = descripcion
            categoria.activo = activa
            mensaje = 'Categoría actualizada exitosamente.'
        else:
            categoria = Categoria(nombre=nombre, descripcion=descripcion, activo=activa)
            db.session.add(categoria)
            mensaje = 'Categoría creada correctamente.'

        try:
            db.session.commit()
            flash(mensaje, 'success')
        except IntegrityError:
            db.session.rollback()
            flash('Ya existe una categoría con ese nombre.', 'danger')
        except Exception as exc:
            db.session.rollback()
            current_app.logger.exception(exc)
            flash('Ocurrió un error al guardar la categoría.', 'danger')
        return redirect(url_for('inventario.listar_categorias'))

    categorias = Categoria.query.order_by(Categoria.nombre).all()
    total_productos = Inventario.query.count()
    return render_template(
        'inventario/listar_categorias.html',
        categorias=categorias,
        total_productos=total_productos
    )


@inventario_bp.route('/categoria/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_categoria():
    categoria_id = request.form.get('categoria_id')
    if not categoria_id:
        flash('No se especificó la categoría a eliminar.', 'warning')
        return redirect(url_for('inventario.listar_categorias'))

    categoria = Categoria.query.get_or_404(categoria_id)
    if categoria.productos:
        flash('No se puede eliminar una categoría con productos asociados.', 'warning')
        return redirect(url_for('inventario.listar_categorias'))

    db.session.delete(categoria)
    db.session.commit()
    flash('Categoría eliminada correctamente.', 'success')
    return redirect(url_for('inventario.listar_categorias'))


@inventario_bp.route('/categoria/cambiar_estado', methods=['POST'])
@login_required
@admin_required
def cambiar_estado_categoria():
    payload = request.get_json(silent=True) or {}
    categoria_id = payload.get('categoria_id')
    nuevo_estado = payload.get('nuevo_estado')

    if categoria_id is None or nuevo_estado is None:
        return jsonify(success=False, message='Datos incompletos.'), 400

    if isinstance(nuevo_estado, str):
        nuevo_estado = nuevo_estado.lower() == 'true'

    categoria = Categoria.query.get(categoria_id)
    if not categoria:
        return jsonify(success=False, message='Categoría no encontrada.'), 404

    categoria.activo = bool(nuevo_estado)
    db.session.commit()
    return jsonify(success=True, activo=categoria.activo, categoria_id=categoria.id)

@inventario_bp.route('/categoria/nueva', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_categoria():
    """Crear nueva categoría"""
    form = CategoriaForm()
    
    if form.validate_on_submit():
        categoria = Categoria(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data
        )
        
        db.session.add(categoria)
        db.session.commit()
        flash('Categoría creada exitosamente', 'success')
        return redirect(url_for('inventario.listar_categorias'))
    
    return render_template('inventario/crear_categoria.html', form=form)

@inventario_bp.route('/informes_baja')
@login_required
@admin_required
def listar_informes_baja():
    """Lista todos los informes de baja pendientes de aprobación"""
    informes_pendientes = InformeBaja.query.filter_by(estado_informe='pendiente').order_by(InformeBaja.fecha_creacion.desc()).all()
    informes_aprobados = InformeBaja.query.filter_by(estado_informe='aprobado').order_by(InformeBaja.fecha_creacion.desc()).all()
    informes_rechazados = InformeBaja.query.filter_by(estado_informe='rechazado').order_by(InformeBaja.fecha_creacion.desc()).all()
    return render_template('inventario/listar_informes_baja.html',
        informes_pendientes=informes_pendientes,
        informes_aprobados=informes_aprobados,
        informes_rechazados=informes_rechazados)

@inventario_bp.route('/api/estadisticas')
@login_required
def api_estadisticas():
    """API para obtener estadísticas del inventario en formato JSON"""
    try:
        primer_dia_mes = datetime.utcnow().replace(day=1)
        por_categoria = [
            {
                'nombre': cat.nombre,
                'cantidad': cat.cantidad
            } for cat in db.session.query(
                Categoria.nombre,
                func.count(Inventario.id).label('cantidad')
            ).outerjoin(Inventario).group_by(Categoria.id, Categoria.nombre).all()
        ]

        estadisticas = {
            'total_productos': Inventario.query.count(),
            'disponibles': Inventario.query.filter_by(estado='en_bodega').count(),
            'asignados': Inventario.query.filter_by(estado='en_uso').count(),
            'daniados': Inventario.query.filter_by(estado='daniado').count(),
            'dado_de_baja': Inventario.query.filter_by(estado='dado_de_baja').count(),
            'nuevos_mes': Inventario.query.filter(Inventario.fecha_registro >= primer_dia_mes).count(),
            'por_estado': {
                'en_bodega': Inventario.query.filter_by(estado='en_bodega').count(),
                'en_uso': Inventario.query.filter_by(estado='en_uso').count(),
                'daniado': Inventario.query.filter_by(estado='daniado').count(),
                'dado_de_baja': Inventario.query.filter_by(estado='dado_de_baja').count()
            },
            'por_categoria': por_categoria,
            'asignaciones_mes': Historial.query.filter(
                Historial.accion == 'asignado',
                Historial.fecha >= primer_dia_mes
            ).count(),
            'mantenimientos_mes': Historial.query.filter(
                Historial.accion == 'mantenimiento',
                Historial.fecha >= primer_dia_mes
            ).count(),
            'bajas_mes': Historial.query.filter(
                Historial.accion == 'dado_de_baja',
                Historial.fecha >= primer_dia_mes
            ).count()
        }

    except Exception as exc:
        current_app.logger.error(f'Error calculando estadísticas: {exc}')
        estadisticas = {
            'total_productos': 0,
            'disponibles': 0,
            'asignados': 0,
            'daniados': 0,
            'dado_de_baja': 0,
            'nuevos_mes': 0,
            'por_estado': {},
            'por_categoria': [],
            'asignaciones_mes': 0,
            'mantenimientos_mes': 0,
            'bajas_mes': 0
        }

    return jsonify(estadisticas)


# Nuevo flujo inteligente para eliminar productos
@inventario_bp.route('/producto/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_producto(id):
    """
    Elimina un producto solo si ya está dado de baja.
    Si no, redirige al formulario de informe de baja.
    """
    producto = Inventario.query.get_or_404(id)
    if producto.estado != 'dado_de_baja':
        flash('Debes realizar primero el informe de baja antes de eliminar el producto.', 'warning')
        return redirect(url_for('inventario.crear_informe_baja', id=producto.id))
    db.session.delete(producto)
    db.session.commit()
    flash('Producto eliminado exitosamente', 'success')
    return redirect(url_for('inventario.listar_productos'))

@inventario_bp.route('/producto/<int:id>/historial')
@login_required
def ver_historial(id):
    producto = Inventario.query.get_or_404(id)
    historial_query = Historial.query.filter_by(producto_id=id)

    accion_filtro = request.args.get('accion')
    if accion_filtro:
        historial_query = historial_query.filter(Historial.accion == accion_filtro)

    usuario_filtro = request.args.get('usuario', type=int)
    if usuario_filtro:
        historial_query = historial_query.filter(Historial.usuario_id == usuario_filtro)

    fecha_desde = request.args.get('fecha_desde')
    if fecha_desde:
        try:
            desde = datetime.strptime(fecha_desde, '%Y-%m-%d')
            historial_query = historial_query.filter(Historial.fecha >= desde)
        except ValueError:
            pass

    fecha_hasta = request.args.get('fecha_hasta')
    if fecha_hasta:
        try:
            hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            hasta = hasta.replace(hour=23, minute=59, second=59)
            historial_query = historial_query.filter(Historial.fecha <= hasta)
        except ValueError:
            pass

    page = request.args.get('page', 1, type=int)
    historial = historial_query.order_by(desc(Historial.fecha)).paginate(page=page, per_page=12, error_out=False)

    usuarios_historial = User.query.join(Historial, Historial.usuario_id == User.id)
    usuarios_historial = usuarios_historial.filter(Historial.producto_id == id).distinct(User.id).all()

    estadisticas_historial = {
        'total': Historial.query.filter_by(producto_id=id).count(),
        'asignaciones': Historial.query.filter_by(producto_id=id, accion='ASIGNACION').count(),
        'modificaciones': Historial.query.filter_by(producto_id=id, accion='MODIFICACION').count(),
        'usuarios_unicos': db.session.query(func.count(func.distinct(Historial.usuario_id))).filter(Historial.producto_id == id).scalar() or 0
    }

    return render_template(
        'inventario/ver_historial.html',
        producto=producto,
        historial=historial,
        usuarios_historial=usuarios_historial,
        estadisticas_historial=estadisticas_historial
    )

@inventario_bp.route('/informe_baja/<int:id>')
@login_required
def ver_informe_baja(id):
    informe = InformeBaja.query.get_or_404(id)
    producto = Inventario.query.get(informe.producto_id) if informe.producto_id else None
    return render_template('inventario/ver_informe_baja.html', informe=informe, producto=producto)



@inventario_bp.route('/informe_baja/<int:id>/aprobar', methods=['POST', 'GET'])
@login_required
@admin_required
def aprobar_informe_baja(id):
    informe = InformeBaja.query.get_or_404(id)
    unidad = Inventario.query.get(informe.producto_id) if informe.producto_id else None
    if unidad:
        unidad_uuid = unidad.uuid
        # Registrar en historial y actualizar estado de la unidad
        registrar_accion_historial(
            unidad.id,
            'dado_de_baja',
            f'Unidad dada de baja por informe aprobado. UUID: {unidad.uuid}'
        )

        # Marcar informe como aprobado
        informe.estado_informe = 'aprobado'
        informe.aprobado = True
        informe.aprobado_por = current_user.id
        informe.fecha_aprobacion = datetime.utcnow()

        # Actualizar la unidad pero conservar el registro para mantener historial intacto
        unidad.estado = 'dado_de_baja'
        unidad.usuario_asignado_id = None
        unidad.fecha_asignacion = None
        db.session.commit()
        flash(f'Unidad {unidad_uuid} marcada como dada de baja y conservada para historial.', 'success')
    else:
        # Si por alguna razón la unidad ya no existe, solo actualizar el estado del informe
        informe.estado_informe = 'aprobado'
        informe.aprobado = True
        informe.aprobado_por = current_user.id
        informe.fecha_aprobacion = datetime.utcnow()
        db.session.commit()
        flash('Informe aprobado. La unidad ya no existe en inventario.', 'warning')
    return redirect(url_for('inventario.listar_informes_baja'))

@inventario_bp.route('/informe_baja/<int:id>/rechazar', methods=['POST', 'GET'])
@login_required
@admin_required
def rechazar_informe_baja(id):
    informe = InformeBaja.query.get_or_404(id)
    informe.estado_informe = 'rechazado'
    informe.aprobado = False
    informe.aprobado_por = current_user.id
    informe.fecha_aprobacion = datetime.utcnow()
    producto = Inventario.query.get(informe.producto_id) if informe.producto_id else None
    if producto:
        producto.estado = informe.estado_previo or 'en_bodega'
        metadata = producto.info_adicional or {}
        rechazos = metadata.get('rechazos_informe', [])
        mensaje_rechazo = f"Baja rechazada por {current_user.nombre} {current_user.apellido} el {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}"
        rechazos.append(mensaje_rechazo)
        metadata['rechazos_informe'] = rechazos
        producto.info_adicional = metadata
        registrar_accion_historial(
            producto.id,
            'rechazado',
            f'Informe de baja rechazado; unidad restaurada a {producto.estado_display}.'
        )
    db.session.commit()
    flash('Informe de baja rechazado y producto restaurado.', 'info')
    return redirect(url_for('inventario.listar_informes_baja'))

