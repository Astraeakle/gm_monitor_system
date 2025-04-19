from models.entities import (Session, RegistroTiempo, CapturaTrabajo, Actividad, Proyecto,
                             Entregable, EvaluacionCalidad, TipoEntregable)
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime, time, timedelta
from werkzeug.utils import secure_filename
import json
import hashlib
from config.db_config import DB_CONFIG
import sys
import os
# Añadir el directorio principal al path para que Python pueda encontrar los módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


app = Flask(__name__)
app.secret_key = 'gm_monitor_secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Definir roles y permisos
ROLES = {
    'employee': ['start_work', 'end_work', 'tasks', 'submit_deliverable'],
    'supervisor': ['review_tasks', 'admin_dashboard', 'quality_review', 'reports'],
    'admin': ['start_work', 'end_work', 'tasks', 'submit_deliverable', 'review_tasks', 'admin_dashboard', 'quality_review', 'reports', 'user_management']
}

# Middleware para verificar permisos


def check_permission(permission):
    def decorator(f):
        def wrapper(*args, **kwargs):
            if 'user_id' not in session or 'role' not in session:
                flash('Por favor inicie sesión para continuar', 'warning')
                return redirect(url_for('login'))

            if permission not in ROLES.get(session['role'], []):
                flash('No tiene permisos para acceder a esta función', 'danger')
                return redirect(url_for('index'))

            return f(*args, **kwargs)
        return wrapper
    return decorator

# Rutas de la aplicación


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Obtener estadísticas básicas para mostrar en el dashboard
    db_session = Session()
    try:
        user_id = session['user_id']
        role = session.get('role', 'employee')

        # Para empleados: mostrar sus actividades pendientes
        if role == 'employee':
            pending_tasks = db_session.query(Actividad).filter(
                Actividad.estado.in_(['Pendiente', 'En Progreso']),
                Actividad.id_actividad.in_(
                    db_session.query(Asignacion.id_actividad).filter(
                        Asignacion.id_empleado == user_id
                    )
                )
            ).count()

            completed_tasks = db_session.query(Actividad).filter(
                Actividad.estado == 'Completada',
                Actividad.id_actividad.in_(
                    db_session.query(Asignacion.id_actividad).filter(
                        Asignacion.id_empleado == user_id
                    )
                )
            ).count()

            # Horas trabajadas esta semana
            today = datetime.now().date()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)

            worked_hours = db_session.query(RegistroTiempo).filter(
                RegistroTiempo.id_empleado == user_id,
                RegistroTiempo.fecha >= start_of_week,
                RegistroTiempo.fecha <= end_of_week
            ).all()

            total_hours = sum(
                (datetime.combine(record.fecha, record.hora_fin) -
                 datetime.combine(record.fecha, record.hora_inicio)).total_seconds() / 3600
                for record in worked_hours
            )

            stats = {
                'pending_tasks': pending_tasks,
                'completed_tasks': completed_tasks,
                'total_hours': round(total_hours, 2)
            }

        # Para supervisores: mostrar estadísticas generales
        else:
            active_employees = db_session.query(
                RegistroTiempo.id_empleado).distinct().count()
            pending_reviews = db_session.query(Actividad).filter(
                Actividad.estado == 'En Revision'
            ).count()

            # Entregables pendientes de evaluación
            pending_deliverables = db_session.query(Entregable).filter(
                Entregable.estado == 'Pendiente Revision'
            ).count()

            stats = {
                'active_employees': active_employees,
                'pending_reviews': pending_reviews,
                'pending_deliverables': pending_deliverables
            }

        return render_template('index.html', stats=stats, role=role)

    except Exception as e:
        flash(f'Error al cargar el dashboard: {str(e)}', 'danger')
        return render_template('index.html', stats={})
    finally:
        db_session.close()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        employee_id = request.form['employee_id']

        # En un sistema real, verificaríamos credenciales con la base de datos
        # Por ahora, usamos un sistema simple basado en prefijos
        if employee_id.startswith('SUP'):
            session['role'] = 'supervisor'
        elif employee_id.startswith('ADM'):
            session['role'] = 'admin'
        else:
            session['role'] = 'employee'

        session['user_id'] = employee_id
        flash('Inicio de sesión exitoso', 'success')
        return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    session.pop('time_record_id', None)
    return redirect(url_for('login'))


@app.route('/start_work', methods=['GET', 'POST'])
@check_permission('start_work')
def start_work():
    if request.method == 'POST':
        db_session = Session()
        try:
            # Obtener datos del formulario
            activity_id = int(request.form['activity_id'])
            description = request.form['description']
            location = request.form['location']

            # Crear registro de tiempo con hora de inicio
            current_time = datetime.now()
            time_record = RegistroTiempo(
                id_empleado=session['user_id'],
                id_actividad=activity_id,
                fecha=current_time.date(),
                hora_inicio=current_time.time(),
                # Valor temporal, se actualizará al finalizar
                hora_fin=time(18, 0),
                descripcion_actividad=description,
                ubicacion=location,
                aplicaciones_usadas=json.dumps({"apps": []})
            )

            # Procesar captura de pantalla si se proporcionó
            if 'screenshot' in request.files:
                file = request.files['screenshot']
                if file.filename != '':
                    filename = secure_filename(
                        f"{session['user_id']}_{current_time.strftime('%Y%m%d%H%M%S')}.png")
                    filepath = os.path.join(
                        app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)

                    # Calcular hash del archivo
                    file_hash = hashlib.sha256()
                    with open(filepath, 'rb') as f:
                        file_hash.update(f.read())

                    # Crear registro de captura
                    screenshot = CapturaTrabajo(
                        id_empleado=session['user_id'],
                        id_actividad=activity_id,
                        tipo='Inicio',
                        ruta_imagen=filepath,
                        fecha_hora=current_time,
                        hash_archivo=file_hash.hexdigest()
                    )

                    db_session.add(screenshot)
                    db_session.flush()

                    # Actualizar registro de tiempo con la referencia a la captura
                    time_record.evidencia_captura_inicio = screenshot.id_captura

            db_session.add(time_record)
            db_session.commit()

            session['time_record_id'] = time_record.id_registro
            flash('Inicio de jornada registrado correctamente', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            db_session.rollback()
            flash(f'Error al iniciar jornada: {str(e)}', 'danger')
        finally:
            db_session.close()

    # Si es GET, mostrar formulario con actividades disponibles
    db_session = Session()
    try:
        # Obtener actividades asignadas al empleado
        activities = db_session.query(Actividad, Proyecto)\
            .join(Proyecto, Actividad.id_proyecto == Proyecto.id_proyecto)\
            .filter(Actividad.estado.in_(['Pendiente', 'En Progreso']))\
            .all()

        return render_template('start_work.html', activities=activities)
    finally:
        db_session.close()


@app.route('/end_work', methods=['GET', 'POST'])
@check_permission('end_work')
def end_work():
    if 'time_record_id' not in session:
        flash('No hay una jornada iniciada', 'warning')
        return redirect(url_for('index'))

    if request.method == 'POST':
        db_session = Session()
        try:
            # Obtener registro de tiempo actual
            time_record_id = session['time_record_id']
            time_record = db_session.query(RegistroTiempo).filter_by(
                id_registro=time_record_id).first()

            if time_record:
                # Actualizar hora de fin
                current_time = datetime.now()
                time_record.hora_fin = current_time.time()

                # Actualizar aplicaciones usadas
                apps_used = request.form.getlist('apps_used')
                time_record.aplicaciones_usadas = json.dumps(
                    {"apps": apps_used})

                # Procesar captura de pantalla final
                if 'screenshot' in request.files:
                    file = request.files['screenshot']
                    if file.filename != '':
                        filename = secure_filename(
                            f"{session['user_id']}_{current_time.strftime('%Y%m%d%H%M%S')}_end.png")
                        filepath = os.path.join(
                            app.config['UPLOAD_FOLDER'], filename)
                        file.save(filepath)

                        # Calcular hash del archivo
                        file_hash = hashlib.sha256()
                        with open(filepath, 'rb') as f:
                            file_hash.update(f.read())

                        # Crear registro de captura
                        screenshot = CapturaTrabajo(
                            id_empleado=session['user_id'],
                            id_actividad=time_record.id_actividad,
                            tipo='Final',
                            ruta_imagen=filepath,
                            fecha_hora=current_time,
                            hash_archivo=file_hash.hexdigest()
                        )

                        db_session.add(screenshot)
                        db_session.flush()

                        # Actualizar registro de tiempo con la referencia a la captura
                        time_record.evidencia_captura_fin = screenshot.id_captura

                db_session.commit()
                session.pop('time_record_id', None)
                flash('Fin de jornada registrado correctamente', 'success')
            else:
                flash('No se encontró un registro de inicio de jornada', 'danger')

            return redirect(url_for('index'))

        except Exception as e:
            db_session.rollback()
            flash(f'Error al finalizar jornada: {str(e)}', 'danger')
        finally:
            db_session.close()

    # Si es GET, mostrar formulario
    return render_template('end_work.html')


@app.route('/tasks', methods=['GET', 'POST'])
@check_permission('tasks')
def tasks():
    db_session = Session()
    try:
        # Obtener todas las actividades asignadas al empleado
        activities = db_session.query(Actividad, Proyecto)\
            .join(Proyecto, Actividad.id_proyecto == Proyecto.id_proyecto)\
            .filter(Actividad.estado.in_(['Pendiente', 'En Progreso', 'En Revision']))\
            .all()

        if request.method == 'POST':
            activity_id = request.form.get('activity_id')
            new_status = request.form.get('new_status')

            activity = db_session.query(Actividad).filter_by(
                id_actividad=activity_id).first()

            if activity:
                activity.estado = new_status
                db_session.commit()
                flash('Estado de actividad actualizado correctamente', 'success')
            else:
                flash('No se encontró la actividad', 'danger')

            return redirect(url_for('tasks'))

        return render_template('tasks.html', activities=activities)
    finally:
        db_session.close()


@app.route('/submit_deliverable/<int:activity_id>', methods=['GET', 'POST'])
@check_permission('submit_deliverable')
def submit_deliverable(activity_id):
    db_session = Session()
    try:
        activity = db_session.query(Actividad).filter_by(
            id_actividad=activity_id).first()
        project = db_session.query(Proyecto).filter_by(
            id_proyecto=activity.id_proyecto).first()
        deliverable_types = db_session.query(TipoEntregable).all()

        if not activity:
            flash('Actividad no encontrada', 'danger')
            return redirect(url_for('tasks'))

        if request.method == 'POST':
            deliverable_type_id = request.form.get('deliverable_type')
            version = request.form.get('version', 1)

            if 'file' not in request.files:
                flash('No se seleccionó ningún archivo', 'danger')
                return redirect(request.url)

            file = request.files['file']
            if file.filename == '':
                flash('No se seleccionó ningún archivo', 'danger')
                return redirect(request.url)

            if file:
                # Crear directorios si no existen
                upload_dir = os.path.join(
                    app.config['UPLOAD_FOLDER'], f'project_{activity.id_proyecto}')
                os.makedirs(upload_dir, exist_ok=True)

                # Guardar archivo
                filename = secure_filename(file.filename)
                filepath = os.path.join(upload_dir, filename)
                file.save(filepath)

                # Registrar entregable
                new_deliverable = Entregable(
                    id_actividad=activity_id,
                    id_empleado=session['user_id'],
                    id_tipo_entregable=deliverable_type_id,
                    nombre_archivo=filename,
                    ruta_archivo=f"/entregables/proyecto_{activity.id_proyecto}/",
                    fecha_entrega=datetime.now(),
                    version=version,
                    estado='Pendiente Revision'
                )

                db_session.add(new_deliverable)
                db_session.commit()

                flash('Entregable cargado con éxito', 'success')
                return redirect(url_for('tasks'))

        return render_template('submit_deliverable.html',
                               activity=activity,
                               project=project,
                               deliverable_types=deliverable_types)
    except Exception as e:
        db_session.rollback()
        flash(f'Error al cargar entregable: {str(e)}', 'danger')
        return redirect(url_for('tasks'))
    finally:
        db_session.close()


@app.route('/review_tasks')
@check_permission('review_tasks')
def review_tasks():
    db_session = Session()
    try:
        pending_activities = db_session.query(Actividad, Proyecto)\
            .join(Proyecto, Actividad.id_proyecto == Proyecto.id_proyecto)\
            .filter(Actividad.estado == 'En Revision')\
            .all()

        return render_template('review_tasks.html', activities=pending_activities)
    finally:
        db_session.close()


@app.route('/quality_review/<int:activity_id>', methods=['GET', 'POST'])
@check_permission('quality_review')
def quality_review(activity_id):
    db_session = Session()
    try:
        activity = db_session.query(Actividad).filter_by(
            id_actividad=activity_id).first()
        project = db_session.query(Proyecto).filter_by(
            id_proyecto=activity.id_proyecto).first()

        # Obtener entregables pendientes de revisión para esta actividad
        deliverables = db_session.query(Entregable)\
            .filter(Entregable.id_actividad == activity_id,
                    Entregable.estado == 'Pendiente Revision')\
            .all()

        if request.method == 'POST':
            deliverable_id = request.form.get('deliverable_id')
            cumple_formato = 'cumple_formato' in request.form
            cumple_contenido = 'cumple_contenido' in request.form
            cumple_normativa = 'cumple_normativa' in request.form
            calificacion = int(request.form.get('calificacion', 1))
            observaciones = request.form.get('observaciones', '')
            acciones = request.form.get('acciones_correctivas', '')

            # Actualizar estado del entregable
            deliverable = db_session.query(Entregable).filter_by(
                id_entregable=deliverable_id).first()
            if deliverable:
                if cumple_formato and cumple_contenido and cumple_normativa and calificacion >= 3:
                    deliverable.estado = 'Aprobado'
                    activity.estado = 'Completada'
                else:
                    deliverable.estado = 'Rechazado'
                    activity.estado = 'En Progreso'

                # Registrar evaluación de calidad
                evaluation = EvaluacionCalidad(
                    id_entregable=deliverable_id,
                    id_evaluador=session['user_id'],
                    fecha_evaluacion=datetime.now(),
                    cumple_formato=cumple_formato,
                    cumple_contenido=cumple_contenido,
                    cumple_normativa=cumple_normativa,
                    calificacion_general=calificacion,
                    observaciones=observaciones,
                    acciones_correctivas=acciones
                )

                db_session.add(evaluation)
                db_session.commit()

                flash('Evaluación de calidad registrada correctamente', 'success')
                return redirect(url_for('review_tasks'))

        return render_template('quality_review.html',
                               activity=activity,
                               project=project,
                               deliverables=deliverables)
    except Exception as e:
        db_session.rollback()
        flash(f'Error al realizar evaluación de calidad: {str(e)}', 'danger')
        return redirect(url_for('review_tasks'))
    finally:
        db_session.close()


@app.route('/admin_dashboard')
@check_permission('admin_dashboard')
def admin_dashboard():
    db_session = Session()
    try:
        # Estadísticas generales
        total_employees = db_session.query(
            RegistroTiempo.id_empleado.distinct()).count()
        active_projects = db_session.query(Proyecto).filter(
            Proyecto.estado == 'En Progreso').count()

        # Top 5 empleados por horas trabajadas
        top_employees = db_session.execute("""
        SELECT id_empleado, SUM(TIME_TO_SEC(TIMEDIFF(hora_fin, hora_inicio))/3600) AS total_hours
        FROM registro_tiempo
        GROUP BY id_empleado
        ORDER BY total_hours DESC
        LIMIT 5
        """).fetchall()

        # Estadísticas de calidad
        quality_stats = db_session.execute("""
        SELECT 
            COUNT(CASE WHEN estado = 'Aprobado' THEN 1 END) AS approved,
            COUNT(CASE WHEN estado = 'Rechazado' THEN 1 END) AS rejected,
            COUNT(CASE WHEN estado = 'Pendiente Revision' THEN 1 END) AS pending
        FROM entregable
        """).fetchone()

        # Proyectos con más actividades pendientes
        pending_by_project = db_session.execute("""
        SELECT p.nombre_proyecto, COUNT(a.id_actividad) AS pending_count
        FROM actividad a
        JOIN proyecto p ON a.id_proyecto = p.id_proyecto
        WHERE a.estado IN ('Pendiente', 'En Progreso', 'En Revision')
        GROUP BY p.nombre_proyecto
        ORDER BY pending_count DESC
        LIMIT 5
        """).fetchall()

        return render_template('admin_dashboard.html',
                               total_employees=total_employees,
                               active_projects=active_projects,
                               top_employees=top_employees,
                               quality_stats=quality_stats,
                               pending_by_project=pending_by_project)
    finally:
        db_session.close()


@app.route('/reports')
@check_permission('reports')
def reports():
    return render_template('reports.html')


@app.route('/api/productivity_data')
@check_permission('reports')
def productivity_data():
    db_session = Session()
    try:
        # Datos para gráfico de productividad
        productivity_data = db_session.execute("""
        SELECT 
            DATE_FORMAT(rt.fecha, '%Y-%m-%d') AS work_date,
            SUM(TIME_TO_SEC(TIMEDIFF(rt.hora_fin, rt.hora_inicio))/3600) AS hours_worked
        FROM registro_tiempo rt
        WHERE rt.fecha >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY work_date
        ORDER BY work_date
        """).fetchall()

        # Convertir a formato adecuado para gráficos
        chart_data = [
            {
                'date': row[0],
                'hours': float(row[1])
            }
            for row in productivity_data
        ]

        return jsonify(chart_data)
    finally:
        db_session.close()


# Ejecutar la aplicación
if __name__ == '__main__':
    # Importación al final para evitar error circular
    from models.entities import Asignacion
    app.run(debug=True, port=5000)
