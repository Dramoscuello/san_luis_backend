from app.models.sedes import Sedes
from app.models.user import User
from app.models.publicaciones import Publicacion
from app.models.areas import Area
from app.models.asignaturas import Asignatura
from app.models.docente_asignaturas import DocenteAsignatura
from app.models.grados import Grado
from app.models.grupos import Grupo
from app.models.docente_grupos import DocenteGrupo
from app.models.estudiantes import Estudiante
from app.models.periodos import Periodo
from app.models.planeaciones import Planeacion
from app.models.comentarios import Comentario
from app.models.planeaciones_destacadas import PlaneacionDestacada
from app.models.proyectos import Proyecto
from app.models.evidencias_proyecto import EvidenciaProyecto
from app.models.comentarios_proyecto import ComentarioProyecto
from app.models.observadores import Observador

__all__ = [
    "Sedes", "User", "Publicacion", "Area", "Asignatura", "DocenteAsignatura",
    "Grado", "Grupo", "DocenteGrupo", "Estudiante", "Periodo",
    "Planeacion", "Comentario", "PlaneacionDestacada",
    "Proyecto", "EvidenciaProyecto", "ComentarioProyecto", "Observador"
]
