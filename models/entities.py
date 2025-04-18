from sqlalchemy import Column, Integer, String, Date, Text, Enum, ForeignKey, Float, Boolean, DateTime, Time, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from config.db_config import SQLALCHEMY_DATABASE_URI

# Crear motor de conexion
engine = create_engine(SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class Proyecto(Base):
    __tablename__ = 'proyectos'

    id_proyecto = Column(Integer, primary_key=True, autoincrement=True)
    nombre_proyecto = Column(String(150), nullable=False)
    cliente = Column(String(100), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin_estimada = Column(Date, nullable=False)
    fecha_fin_real = Column(Date)
    estado = Column(Enum('Planificacion', 'En Progreso', 'Finalizado', 'Cancelado'),
                    default='Planificacion')
    descripcion = Column(Text)

    # Relaciones
    actividades = relationship("Actividad", back_populates="proyecto")


class Actividad(Base):
    __tablename__ = 'actividades'

    id_actividad = Column(Integer, primary_key=True, autoincrement=True)
    id_proyecto = Column(Integer, ForeignKey(
        'proyectos.id_proyecto', ondelete='CASCADE'), nullable=False)
    nombre_actividad = Column(String(150), nullable=False)
    descripcion = Column(Text)
    prioridad = Column(Enum('Baja', 'Media', 'Alta',
                       'Urgente'), default='Media')
    fecha_asignacion = Column(Date, nullable=False)
    fecha_limite = Column(Date, nullable=False)
    estado = Column(Enum('Pendiente', 'En Progreso', 'En Revision',
                    'Completada', 'Cancelada'), default='Pendiente')

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="actividades")
    asignaciones = relationship("Asignacion", back_populates="actividad")
    registros_tiempo = relationship(
        "RegistroTiempo", back_populates="actividad")
    entregables = relationship("Entregable", back_populates="actividad")


class Asignacion(Base):
    __tablename__ = 'asignaciones'

    id_asignacion = Column(Integer, primary_key=True, autoincrement=True)
    id_actividad = Column(Integer, ForeignKey(
        'actividades.id_actividad', ondelete='CASCADE'), nullable=False)
    id_empleado = Column(String(5), nullable=False)
    fecha_asignacion = Column(DateTime, nullable=False)

    # Relaciones
    actividad = relationship("Actividad", back_populates="asignaciones")


class CapturaTrabajo(Base):
    __tablename__ = 'capturas_trabajo'

    id_captura = Column(Integer, primary_key=True, autoincrement=True)
    id_empleado = Column(String(5), nullable=False)
    id_actividad = Column(Integer, ForeignKey('actividades.id_actividad'))
    tipo = Column(Enum('Inicio', 'Final'), nullable=False)
    ruta_imagen = Column(String(255), nullable=False)
    fecha_hora = Column(DateTime, nullable=False)
    hash_archivo = Column(String(64))


class RegistroAplicacion(Base):
    __tablename__ = 'registro_aplicaciones'

    id_registro_app = Column(Integer, primary_key=True, autoincrement=True)
    id_empleado = Column(String(5), nullable=False)
    id_actividad = Column(Integer, ForeignKey('actividades.id_actividad'))
    fecha = Column(Date, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time)
    nombre_aplicacion = Column(String(100), nullable=False)
    estado = Column(Enum('Activo', 'Inactivo'), default='Activo')


class RegistroTiempo(Base):
    __tablename__ = 'registro_tiempo'

    id_registro = Column(Integer, primary_key=True, autoincrement=True)
    id_empleado = Column(String(5), nullable=False)
    id_actividad = Column(Integer, ForeignKey(
        'actividades.id_actividad'), nullable=False)
    fecha = Column(Date, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    descripcion_actividad = Column(Text)
    ubicacion = Column(String(100))
    aplicaciones_usadas = Column(JSON)
    evidencia_captura_inicio = Column(
        Integer, ForeignKey('capturas_trabajo.id_captura'))
    evidencia_captura_fin = Column(
        Integer, ForeignKey('capturas_trabajo.id_captura'))

    # Relaciones
    actividad = relationship("Actividad", back_populates="registros_tiempo")


class TipoEntregable(Base):
    __tablename__ = 'tipos_entregables'

    id_tipo_entregable = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    parametros_calidad = Column(Text)

    # Relaciones
    entregables = relationship("Entregable", back_populates="tipo_entregable")


class Entregable(Base):
    __tablename__ = 'entregables'

    id_entregable = Column(Integer, primary_key=True, autoincrement=True)
    id_actividad = Column(Integer, ForeignKey(
        'actividades.id_actividad'), nullable=False)
    id_empleado = Column(String(5), nullable=False)
    id_tipo_entregable = Column(Integer, ForeignKey(
        'tipos_entregables.id_tipo_entregable'), nullable=False)
    nombre_archivo = Column(String(255), nullable=False)
    ruta_archivo = Column(String(255), nullable=False)
    fecha_entrega = Column(DateTime, nullable=False)
    version = Column(Integer, default=1)
    estado = Column(Enum('Pendiente Revision', 'En Revision',
                    'Aprobado', 'Rechazado'), default='Pendiente Revision')

    # Relaciones
    actividad = relationship("Actividad", back_populates="entregables")
    tipo_entregable = relationship(
        "TipoEntregable", back_populates="entregables")
    evaluaciones = relationship(
        "EvaluacionCalidad", back_populates="entregable")


class EvaluacionCalidad(Base):
    __tablename__ = 'evaluacion_calidad'

    id_evaluacion = Column(Integer, primary_key=True, autoincrement=True)
    id_entregable = Column(Integer, ForeignKey(
        'entregables.id_entregable'), nullable=False)
    id_evaluador = Column(String(5), nullable=False)
    fecha_evaluacion = Column(DateTime, nullable=False)
    cumple_formato = Column(Boolean, default=False)
    cumple_contenido = Column(Boolean, default=False)
    cumple_normativa = Column(Boolean, default=False)
    calificacion_general = Column(Integer)
    observaciones = Column(Text)
    acciones_correctivas = Column(Text)

    # Relaciones
    entregable = relationship("Entregable", back_populates="evaluaciones")


class MetricaProductividad(Base):
    __tablename__ = 'metricas_productividad'

    id_metrica = Column(Integer, primary_key=True, autoincrement=True)
    id_empleado = Column(String(5), nullable=False)
    id_proyecto = Column(Integer, ForeignKey(
        'proyectos.id_proyecto'), nullable=False)
    id_actividad = Column(Integer, ForeignKey(
        'actividades.id_actividad'), nullable=False)
    fecha_calculo = Column(Date, nullable=False)
    periodo_inicio = Column(Date, nullable=False)
    periodo_fin = Column(Date, nullable=False)
    horas_trabajadas = Column(Float(10, 2))
    tareas_completadas = Column(Integer)
    entregables_aprobados = Column(Integer)
    entregables_rechazados = Column(Integer)
    indice_productividad = Column(Float(5, 2))
    observaciones = Column(Text)

# La tabla empleados está en otra base de datos (gmadministracion)
# y se accede por referencia
