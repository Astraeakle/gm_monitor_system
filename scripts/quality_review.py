# quality_review.py - Sistema de revisión de calidad integrado

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.entities import Session, Entregable, EvaluacionCalidad, Actividad, Proyecto, TipoEntregable
from sqlalchemy import and_, or_
from datetime import datetime
import os
from werkzeug.utils import secure_filename

# Crear blueprint para las rutas de revisión
quality_bp = Blueprint('quality', __name__, url_prefix='/quality')

# Configuración de carga de archivos
UPLOAD_FOLDER = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'static/deliverables')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx',
                      'ppt', 'pptx', 'zip', 'rar', 'dwg', 'dxf', 'rvt'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@quality_bp.route('/deliverables', methods=['GET'])
def deliverables_list():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db_session = Session()
    try:
        # Obtener los entregables del usuario actual
        deliverables = db_session.query(Entregable, Actividad, Proyecto, TipoEntregable)\
            .join(Actividad, Entregable.id_actividad == Actividad.id_actividad)\
            .join(Proyecto, Actividad.id_proyecto == Proyecto.id_proyecto)\
            .join(TipoEntregable, Entregable.id_tipo_entregable == TipoEntregable.id_tipo_entregable)\
            .filter(Entregable.id_empleado == session['user_id'])\
            .all()

        return render_template('quality/deliverables_list.html', deliverables=deliverables)
    finally:
        db_session.close()


@quality_bp.route('/upload', methods=['GET', 'POST'])
def upload_deliverable():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db_session = Session()
    try:
        if request.method == 'POST':
            # Validar datos del formulario
            activity_id = request.form.get('activity_id')
            deliverable_type = request.form.get('deliverable_type')

            if not activity_id or not deliverable_type:
                flash('Por favor complete todos los campos requeridos', 'danger')
                return redirect(url_for('quality.upload_deliverable'))

            # Verificar archivo
            if 'file' not in request.files:
                flash('No se seleccionó ningún archivo', 'danger')
                return redirect(url_for('quality.upload_deliverable'))

            file = request.files['file']
            if file.filename == '':
                flash('No se seleccionó ningún archivo', 'danger')
                return redirect(url_for('quality.upload_deliverable'))

            if file and allowed_file(file.filename):
                # Procesar carga de archivo
                filename = secure_filename(
                    f"{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file
