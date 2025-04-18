from config.db_config import DB_CONFIG
from models.entities import Session, RegistroTiempo, CapturaTrabajo, Actividad, Proyecto
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, time
import os
import json
import hashlib
from werkzeug.utils import secure_filename

# Importar módulos del sistema de monitoreo
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
app.secret_key = 'gm_monitor_secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Rutas de la aplicación


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        employee_id = request.form['employee_id']
        # En un sistema real, verificaríamos credenciales
        # Por ahora, simplemente guardamos el ID
        session['user_id'] = employee_id
        flash('Inicio de sesión exitoso', 'success')
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route('/start_work', methods=['GET', 'POST'])
def start_work():
    if 'user_id' not in session:
        return redirect(url_for('login'))

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
def end_work():
    if 'user_id' not in session or 'time_record_id' not in session:
        return redirect(url_for('login'))

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
def tasks():
    if 'user_id' not in session:
        return redirect(url_for('login'))

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


if __name__ == '__main__':
    app.run(debug=True, port=5000)
