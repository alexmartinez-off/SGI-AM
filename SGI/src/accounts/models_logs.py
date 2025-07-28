from datetime import datetime
from src import db

class LogAccion(db.Model):
    """
    Modelo para registrar todas las acciones administrativas en el sistema
    """
    __tablename__ = "logs_acciones"
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Quien realizó la acción
    accion = db.Column(db.String(100), nullable=False)  # Tipo de acción (crear, editar, eliminar)
    tabla_afectada = db.Column(db.String(50), nullable=False)  # Tabla/módulo afectado
    registro_id = db.Column(db.Integer)  # ID del registro afectado
    datos_anteriores = db.Column(db.Text)  # JSON con datos antes del cambio
    datos_nuevos = db.Column(db.Text)  # JSON con datos después del cambio
    ip_address = db.Column(db.String(45))  # IP del usuario
    user_agent = db.Column(db.Text)  # Navegador/dispositivo
    fecha_hora = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    descripcion = db.Column(db.Text)  # Descripción legible de la acción
    
    # Relación con el usuario que realizó la acción
    usuario = db.relationship('User', backref=db.backref('logs_realizados', lazy=True))
    
    def __repr__(self):
        return f"<LogAccion {self.accion} por {self.usuario.username} en {self.fecha_hora}>"
    
    @staticmethod
    def registrar_accion(usuario_id, accion, tabla_afectada, registro_id=None, 
                        datos_anteriores=None, datos_nuevos=None, descripcion=None, 
                        request=None):
        """
        Método estático para registrar una acción en el log
        """
        import json
        from flask import request as flask_request
        
        if request is None:
            request = flask_request
            
        log = LogAccion(
            usuario_id=usuario_id,
            accion=accion,
            tabla_afectada=tabla_afectada,
            registro_id=registro_id,
            datos_anteriores=json.dumps(datos_anteriores) if datos_anteriores else None,
            datos_nuevos=json.dumps(datos_nuevos) if datos_nuevos else None,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent') if request else None,
            descripcion=descripcion
        )
        
        db.session.add(log)
        db.session.commit()
        return log
