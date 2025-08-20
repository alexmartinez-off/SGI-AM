from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, desc, or_
from werkzeug.utils import secure_filename
import os
from datetime import datetime

from src import db
from src.inventario.models import Inventario, Categoria, Historial, InformeBaja, Asignacion
from src.inventario.forms import (ProductoForm, CategoriaForm, AsignacionForm, 
                                InformeBajaForm, CambiarEstadoForm, FiltroInventarioForm)
from src.accounts.views import admin_required

# Crear el blueprint para inventario
inventario_bp = Blueprint('inventario', __name__)

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
            # Si se da de baja, verificar que exista informe de baja
            if estado_nuevo == 'dado_de_baja':
                informe_baja = InformeBaja.query.filter_by(
                    producto_id=id,
                    estado_informe='aprobado'
                ).first()
                if not informe_baja:
                    flash('No se puede dar de baja el producto sin un informe de baja aprobado', 'error')
                    return render_template('inventario/cambiar_estado.html', form=form, producto=producto)
            registrar_accion_historial(
                producto.id,
                'cambio_estado',
                form.descripcion.data,
                estado_anterior=estado_anterior,
                estado_nuevo=estado_nuevo
            )
            db.session.commit()
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

@inventario_bp.route('/producto/<int:id>')
@login_required
def ver_producto(id):
    producto = Inventario.query.get_or_404(id)
    historial = Historial.query.filter_by(producto_id=id).order_by(desc(Historial.fecha)).all()
    asignaciones = Asignacion.query.filter_by(producto_id=id).order_by(desc(Asignacion.fecha_asignacion)).all()
    return render_template('inventario/ver_producto.html', producto=producto, historial=historial, asignaciones=asignaciones)

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
    
    # Construir query base
    query = Inventario.query.join(Categoria)
    
    # Aplicar filtros si existen
    if request.args.get('nombre'):
        query = query.filter(Inventario.nombre.contains(request.args.get('nombre')))
    
    if request.args.get('categoria_id'):
        query = query.filter(Inventario.categoria_id == request.args.get('categoria_id'))
    
    if request.args.get('estado'):
        query = query.filter(Inventario.estado == request.args.get('estado'))
    
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
        form=form
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
                estado='en_bodega',
                fecha_registro=datetime.utcnow()
            )
            db.session.add(producto)
            db.session.flush()  # Para obtener el ID
            registrar_accion_historial(
                producto.id,
                'creado',
                f'Producto creado: {producto.nombre}'
            )
        db.session.commit()
        flash('Producto(s) creado(s) exitosamente', 'success')
        return redirect(url_for('inventario.listar_productos'))
    return render_template('inventario/crear_producto.html', form=form)
    producto = Inventario.query.get_or_404(id)
    form = CambiarEstadoForm()
    if form.validate_on_submit():
        estado_anterior = producto.estado
        estado_nuevo = form.estado_nuevo.data
        if estado_anterior != estado_nuevo:
            producto.estado = estado_nuevo
            # Si se da de baja, verificar que exista informe de baja
            if estado_nuevo == 'dado_de_baja':
                informe_baja = InformeBaja.query.filter_by(
                    producto_id=id, 
                    estado_informe='aprobado'
                ).first()
                if not informe_baja:
                    flash('No se puede dar de baja el producto sin un informe de baja aprobado', 'error')
                    return render_template('inventario/cambiar_estado.html', form=form, producto=producto)
            registrar_accion_historial(
                producto.id,
                'cambio_estado',
                form.descripcion.data,
                estado_anterior=estado_anterior,
                estado_nuevo=estado_nuevo
            )
            db.session.commit()
            flash(f'Estado del producto cambiado de "{producto.estado_display}" a "{form.estado_nuevo.data}"', 'success')
            return redirect(url_for('inventario.ver_producto', id=producto.id))
        else:
            flash('El estado seleccionado es el mismo que el actual', 'warning')
    return render_template('inventario/cambiar_estado.html', form=form, producto=producto)
    """Ver detalles de un producto específico"""
    producto = Inventario.query.get_or_404(id)
    historial = Historial.query.filter_by(producto_id=id).order_by(desc(Historial.fecha)).all()
    asignaciones = Asignacion.query.filter_by(producto_id=id).order_by(desc(Asignacion.fecha_asignacion)).all()
    
    return render_template('inventario/ver_producto.html', 
                         producto=producto, historial=historial, asignaciones=asignaciones)

@inventario_bp.route('/producto/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_producto(id):
    """Editar un producto existente"""
    producto = Inventario.query.get_or_404(id)
    form = ProductoForm(obj=producto)
    
    if form.validate_on_submit():
        # Registrar cambios en historial
        cambios = []
        if producto.nombre != form.nombre.data:
            cambios.append(f"Nombre: {producto.nombre} → {form.nombre.data}")
        if producto.descripcion != form.descripcion.data:
            cambios.append("Descripción actualizada")
        if producto.cantidad != form.cantidad.data:
            cambios.append(f"Cantidad: {producto.cantidad} → {form.cantidad.data}")
        
        # Actualizar producto
        form.populate_obj(producto)
        
        if cambios:
            registrar_accion_historial(
                producto.id,
                'editado',
                f'Producto editado. Cambios: {", ".join(cambios)}'
            )
        
        db.session.commit()
        flash('Producto actualizado exitosamente', 'success')
        return redirect(url_for('inventario.ver_producto', id=producto.id))
    
    return render_template('inventario/editar_producto.html', form=form, producto=producto)

    form = CambiarEstadoForm()
    if form.validate_on_submit():
        estado_anterior = producto.estado
        estado_nuevo = form.estado_nuevo.data
        if estado_anterior != estado_nuevo:
            producto.estado = estado_nuevo
            # Si se da de baja, verificar que exista informe de baja
            if estado_nuevo == 'dado_de_baja':
                informe_baja = InformeBaja.query.filter_by(
                    producto_id=id, 
                    estado_informe='aprobado'
                ).first()
                if not informe_baja:
                    flash('No se puede dar de baja el producto sin un informe de baja aprobado', 'error')
                    return render_template('inventario/cambiar_estado.html', form=form, producto=producto)
            registrar_accion_historial(
                producto.id,
                'cambio_estado',
                form.descripcion.data,
                estado_anterior=estado_anterior,
                estado_nuevo=estado_nuevo
            )
            db.session.commit()
            flash(f'Estado del producto cambiado de "{producto.estado_display}" a "{form.estado_nuevo.data}"', 'success')
            return redirect(url_for('inventario.ver_producto', id=producto.id))
        else:
            flash('El estado seleccionado es el mismo que el actual', 'warning')
    return render_template('inventario/cambiar_estado.html', form=form, producto=producto)
    """Asignar una unidad de producto a un usuario"""
    producto = Inventario.query.get_or_404(id)
    form = AsignacionForm(producto_id=id)
    if form.validate_on_submit():
        unidad = Inventario.query.filter_by(uuid=form.uuid_unidad.data).first()
        asignacion = Asignacion(
            producto_id=unidad.id,
            usuario_asignado_id=form.usuario_asignado_id.data,
            asignado_por=current_user.id,
            motivo_asignacion=form.motivo_asignacion.data,
            fecha_devolucion_esperada=form.fecha_devolucion_esperada.data,
            condiciones_uso=form.condiciones_uso.data
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
    else:
        return render_template('inventario/asignar_producto.html', form=form, producto=producto)
            

@inventario_bp.route('/producto/<int:id>/asignar', methods=['GET', 'POST'])
@login_required
@admin_required
def asignar_producto(id):
    """Asignar un producto a un usuario"""
    producto = Inventario.query.get_or_404(id)
    form = AsignacionForm()
    
    if form.validate_on_submit():
        asignacion = Asignacion(
            producto_id=id,
            usuario_asignado_id=form.usuario_asignado_id.data,
            asignado_por=current_user.id,
            motivo_asignacion=form.motivo_asignacion.data,
            fecha_devolucion_esperada=form.fecha_devolucion_esperada.data,
            condiciones_uso=form.condiciones_uso.data
        )
        
        # Actualizar producto
        producto.usuario_asignado_id = form.usuario_asignado_id.data
        producto.fecha_asignacion = datetime.utcnow()
        producto.estado = 'en_uso'
        
        db.session.add(asignacion)
        
        # Registrar en historial
        from src.accounts.models import User
        usuario = User.query.get(form.usuario_asignado_id.data)
        registrar_accion_historial(
            producto.id,
            'asignado',
            f'Producto asignado a {usuario.nombre} {usuario.apellido} ({usuario.username}). Motivo: {form.motivo_asignacion.data}'
        )
        
        db.session.commit()
        flash('Producto asignado exitosamente', 'success')
        return redirect(url_for('inventario.ver_producto', id=producto.id))
    
    return render_template('inventario/asignar_producto.html', form=form, producto=producto)

@inventario_bp.route('/producto/<int:id>/informe_baja', methods=['GET', 'POST'])
@login_required
def crear_informe_baja(id):
    """Crear informe de baja para un producto"""
    producto = Inventario.query.get_or_404(id)
    form = InformeBajaForm(producto_id=id)
    if form.validate_on_submit():
        # Lógica de validación de informe
        estado_informe = 'aprobado' if current_user.rol == 'admin' else 'pendiente'
        motivo_final = form.motivo_otro.data if form.motivo.data == 'otro' and form.motivo_otro.data else form.motivo.data
        informe = InformeBaja(
            producto_id=id,
            usuario_id=current_user.id,
            motivo=motivo_final,
            descripcion_detallada=form.descripcion_detallada.data,
            fecha_baja=form.fecha_baja.data,
            valor_residual=form.valor_residual.data,
            estado_informe=estado_informe
        )
        # Manejar archivo adjunto si existe
        if form.documento_adjunto.data:
            file = form.documento_adjunto.data
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'informes_baja')
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            informe.documento_adjunto = filename
        db.session.add(informe)
        db.session.commit()
        if estado_informe == 'aprobado':
            flash('Informe de baja creado y aprobado automáticamente (admin).', 'success')
        else:
            flash('Informe de baja creado y enviado para revisión de un administrador.', 'info')
        return redirect(url_for('inventario.ver_producto', id=producto.id))
    return render_template('inventario/informe_baja.html', form=form, producto=producto)

@inventario_bp.route('/categorias')
@login_required
def listar_categorias():
    """Lista todas las categorías"""
    categorias = Categoria.query.filter_by(activo=True).all()
    return render_template('inventario/listar_categorias.html', categorias=categorias)

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
    
    estadisticas = {
        'total_productos': Inventario.query.count(),
        'por_estado': {
            'en_bodega': Inventario.query.filter_by(estado='en_bodega').count(),
            'en_uso': Inventario.query.filter_by(estado='en_uso').count(),
            'daniado': Inventario.query.filter_by(estado='daniado').count(),
            'dado_de_baja': Inventario.query.filter_by(estado='daniado').count()
        },
        'por_categoria': [
            {
                'nombre': cat.nombre,
                'cantidad': cat.cantidad
            } for cat in db.session.query(
                Categoria.nombre,
                func.count(Inventario.id).label('cantidad')
            ).outerjoin(Inventario).group_by(Categoria.id, Categoria.nombre).all()
        ]
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
    historial = Historial.query.filter_by(producto_id=id).order_by(Historial.fecha_accion.desc()).all()
    return render_template('inventario/ver_historial.html', producto=producto, historial=historial)

@inventario_bp.route('/informe_baja/<int:id>')
@login_required
def ver_informe_baja(id):
    informe = InformeBaja.query.get_or_404(id)
    producto = Inventario.query.get_or_404(informe.producto_id)
    return render_template('inventario/ver_informe_baja.html', informe=informe, producto=producto)



@inventario_bp.route('/informe_baja/<int:id>/aprobar', methods=['POST', 'GET'])
@login_required
@admin_required
def aprobar_informe_baja(id):
    informe = InformeBaja.query.get_or_404(id)
    unidad = Inventario.query.get_or_404(informe.producto_id)
    # Registrar en historial
    registrar_accion_historial(
        unidad.id,
        'dado_de_baja',
        f'Unidad dada de baja por informe aprobado. UUID: {unidad.uuid}'
    )
    db.session.delete(unidad)
    db.session.delete(informe)
    db.session.commit()
    flash(f'Unidad {unidad.uuid} dada de baja y eliminada del inventario.', 'success')
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
    db.session.commit()
    flash('Informe de baja rechazado.', 'info')
    return redirect(url_for('inventario.listar_informes_baja'))

