from flask import Blueprint, render_template
from flask_login import login_required
from src.core.models import Inventario

core_bp = Blueprint("core", __name__)


@core_bp.route("/")
@login_required
def home():
    inventario = Inventario.query.all()
    return render_template("core/index.html", inventario=inventario)