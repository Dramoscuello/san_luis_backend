# 📚 SISTEMA DE GESTIÓN PEDAGÓGICA INTELIGENTE (SGPI)

## 🎯 VISIÓN GENERAL DEL PROYECTO

### Propósito
Sistema web integral diseñado para centralizar, organizar y optimizar la gestión pedagógica de una institución educativa rural colombiana con **50 docentes** distribuidos en **5 sedes**. El sistema elimina la dependencia de documentos físicos dispersos y proporciona visibilidad en tiempo real a coordinadores y rectoría sobre todas las actividades pedagógicas institucionales.

### Problema que Resuelve
**Situación Actual:**
- Coordinadores invierten ~8 horas semanales buscando y organizando documentos en papel
- Necesidad de desplazamientos físicos a 5 sedes para supervisión
- Pérdida y desorganización de documentos importantes
- Falta de visibilidad centralizada del trabajo docente
- Ausencia de mecanismo para compartir mejores prácticas
- Sin seguimiento estructurado del desempeño estudiantil

**Solución Propuesta:**
- Plataforma web centralizada multi-sede
- Sistema de retroalimentación estructurada
- Banco de mejores prácticas institucionales
- Dashboard analítico con métricas en tiempo real
- Seguimiento académico documentado de estudiantes
- Sistema de comunicación institucional

### ROI Esperado
- **Ahorro de tiempo:** 75% reducción en gestión administrativa (24 horas/mes recuperadas)
- **Reducción de costos:** Eliminación de desplazamientos físicos entre sedes
- **Mejora pedagógica:** Difusión de mejores prácticas
- **Trazabilidad completa:** Histórico institucional para análisis y certificación
- **Payback period:** Menos de 12 meses

---

## 🏛️ ARQUITECTURA DEL SISTEMA

### Arquitectura General

```
┌─────────────────────────────────────────────────────────┐
│                  FRONTEND (SPA)                         │
│                  Vue.js 3 + Tailwind                    │
│                  Vite + Pinia                           │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS / REST API
                     │ JSON / JWT
┌────────────────────▼────────────────────────────────────┐
│                  BACKEND API                            │
│                  FastAPI (Python)                       │
│                  + Celery Worker                        │
└────────┬───────────────────────┬────────────────────────┘
         │                       │
         │                       │
    ┌────▼─────┐          ┌─────▼──────┐
    │PostgreSQL│          │   Redis    │
    │  (15GB)  │          │  (Cache +  │
    │          │          │   Queue)   │
    └──────────┘          └────────────┘
         │
         │ Metadata only
         │
    ┌────▼──────────────────────────────┐
    │      Google Drive API             │
    │   (Almacenamiento Archivos)       │
    │         GRATIS 15GB               │
    └───────────────────────────────────┘
```

### Decisiones Arquitectónicas Clave

#### 1. **Monolito Modular Backend**
- **Razón:** Simplicidad operativa, bajo costo, suficiente para 50 usuarios concurrentes
- **FastAPI** como framework web por su rendimiento y tipado fuerte
- Todos los servicios en un solo VPS para minimizar costos

#### 2. **SPA (Single Page Application) Frontend**
- **Vue.js 3** con Composition API para reactividad óptima
- Separación clara entre presentación (frontend) y lógica (backend)
- Experiencia de usuario fluida sin recargas de página

#### 3. **PostgreSQL como Base de Datos Principal**
- Base de datos relacional robusta para integridad referencial
- Auto-gestionada en VPS (sin servicios managed) para reducir costos
- Almacena SOLO metadata, NO archivos

#### 4. **Google Drive para Almacenamiento**
- **Gratis** (15GB por cuenta, multi-cuenta si se llena)
- API oficial de Google para operaciones
- Visualización directa con iframes (sin descargar)
- Reduce drásticamente costos vs S3/Spaces

#### 5. **Celery + Redis para Procesamiento Asíncrono**
- Envío de emails en background
- Generación de reportes PDF sin afectar UX

---

## 📊 ESQUEMA DE BASE DE DATOS

### Visión General
**Total de tablas:** 24  
**Motor:** PostgreSQL 15+  
**Tamaño estimado:** 70 MB/año  
**Estrategia de índices:** Optimizado para consultas frecuentes por sede, docente y fecha  

### Estructura de Entidades por Dominio

#### 🏫 **DOMINIO: ESTRUCTURA ACADÉMICA**

##### Tabla: `areas`
Áreas académicas de la institución.
```sql
CREATE TABLE areas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,        -- "Matemáticas", "Ciencias Naturales"
    descripcion TEXT,
    activa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```
**Relaciones:** 1:N con `asignaturas`  
**Índices:** `idx_areas_activa`  

##### Tabla: `sedes`
Ubicaciones físicas de la institución (5 sedes).
```sql
CREATE TABLE sedes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,              -- "Sede Principal", "Sede Norte"
    codigo VARCHAR(20) UNIQUE,                 -- "SP001", "SN002"
    direccion TEXT,
    telefono VARCHAR(20),
    activa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```
**Relaciones:** 1:N con `grados`, `usuarios`  
**Índices:** `idx_sedes_activa`, `idx_sedes_codigo`  

##### Tabla: `grados`
Niveles académicos dentro de cada sede.
```sql
CREATE TABLE grados (
    id SERIAL PRIMARY KEY,
    sede_id INTEGER NOT NULL REFERENCES sedes(id) ON DELETE CASCADE,
    nombre VARCHAR(50) NOT NULL,               -- "6°", "7°", "8°"
    codigo VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(sede_id, nombre)                    -- Un grado único por sede
);
```
**Relaciones:** N:1 con `sedes`, 1:N con `grupos`  
**Índices:** `idx_grados_sede`  
**Constraint:** Un grado no puede repetirse en la misma sede  

##### Tabla: `grupos`
Secciones dentro de cada grado (puede haber 1 o múltiples por grado).
```sql
CREATE TABLE grupos (
    id SERIAL PRIMARY KEY,
    grado_id INTEGER NOT NULL REFERENCES grados(id) ON DELETE CASCADE,
    nombre VARCHAR(50) NOT NULL,               -- "6°1", "6°2", "7°1"
    codigo VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(grado_id, nombre)                   -- Un grupo único por grado
);
```
**Relaciones:** N:1 con `grados`, 1:N con `estudiantes`, N:M con `usuarios` (docentes directores)  
**Índices:** `idx_grupos_grado`  

##### Tabla: `asignaturas`
Materias que se dictan en la institución.
```sql
CREATE TABLE asignaturas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,              -- "Álgebra", "Geometría"
    area_id INTEGER NOT NULL REFERENCES areas(id) ON DELETE CASCADE,
    codigo VARCHAR(20) UNIQUE,
    descripcion TEXT,
    grados VARCHAR(100),                       -- "6,7,8,9" - grados donde se dicta
    activa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(nombre, area_id)
);
```
**Relaciones:** N:1 con `areas`, N:M con `usuarios` (docentes)  
**Índices:** `idx_asignaturas_area`, `idx_asignaturas_activa`  

---

#### 👥 **DOMINIO: USUARIOS Y ASIGNACIONES**

##### Tabla: `usuarios`
Docentes, coordinadores y rector del sistema.
```sql
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    nombre_completo VARCHAR(255) NOT NULL,
    cedula VARCHAR(20) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,       -- Bcrypt hash
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('docente', 'coordinador', 'rector')),
    sede_id INTEGER REFERENCES sedes(id) ON DELETE SET NULL,
    activo BOOLEAN DEFAULT TRUE,
    fecha_ingreso DATE,
    telefono VARCHAR(20),
    foto_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    ultimo_acceso TIMESTAMP
);
```
**Roles:**
- `docente`: 50 usuarios, pueden subir contenido, ver sus grupos
- `coordinador`: 3-5 usuarios, supervisan todo, crean estructura
- `rector`: 1 usuario, dashboard ejecutivo, reportes

**Relaciones:** N:1 con `sedes`, N:M con `asignaturas`, N:M con `grupos`  
**Índices:** `idx_usuarios_email`, `idx_usuarios_sede`, `idx_usuarios_rol`, `idx_usuarios_activo`, `idx_usuarios_cedula`  
**Seguridad:** Password nunca se almacena en texto plano, solo hash bcrypt  

##### Tabla: `docente_asignaturas`
Relación muchos a muchos: un docente puede dictar múltiples asignaturas.
```sql
CREATE TABLE docente_asignaturas (
    id SERIAL PRIMARY KEY,
    docente_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    asignatura_id INTEGER NOT NULL REFERENCES asignaturas(id) ON DELETE CASCADE,
    fecha_asignacion DATE DEFAULT CURRENT_DATE,
    activa BOOLEAN DEFAULT TRUE,
    UNIQUE(docente_id, asignatura_id)
);
```
**Ejemplo:** Profesor Juan puede dictar "Álgebra" y "Geometría"  
**Índices:** `idx_docente_asignaturas_docente`, `idx_docente_asignaturas_asignatura`  

##### Tabla: `docente_grupos`
Relación muchos a muchos: un docente puede ser director de uno o varios grupos.
```sql
CREATE TABLE docente_grupos (
    id SERIAL PRIMARY KEY,
    docente_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    grupo_id INTEGER NOT NULL REFERENCES grupos(id) ON DELETE CASCADE,
    fecha_asignacion DATE DEFAULT CURRENT_DATE,
    activa BOOLEAN DEFAULT TRUE,
    UNIQUE(docente_id, grupo_id)
);
```
**Nota:** Lo normal es 1 grupo por docente, pero puede tener múltiples  
**Índices:** `idx_docente_grupos_docente`, `idx_docente_grupos_grupo`  

##### Tabla: `historial_sedes`
Auditoría de reasignaciones de docentes entre sedes.
```sql
CREATE TABLE historial_sedes (
    id SERIAL PRIMARY KEY,
    docente_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    sede_anterior_id INTEGER REFERENCES sedes(id) ON DELETE SET NULL,
    sede_nueva_id INTEGER REFERENCES sedes(id) ON DELETE SET NULL,
    fecha_cambio TIMESTAMP DEFAULT NOW(),
    motivo TEXT,
    realizado_por INTEGER REFERENCES usuarios(id) ON DELETE SET NULL
);
```
**Propósito:** Mantener trazabilidad completa de cambios administrativos  
**Índices:** `idx_historial_docente`, `idx_historial_fecha`  

---

#### 📝 **MÓDULO 1: PLANEACIONES DE CLASE**

##### Tabla: `planeaciones`
Documentos de planificación de clases subidos por docentes.
```sql
CREATE TABLE planeaciones (
    id SERIAL PRIMARY KEY,
    docente_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    asignatura_id INTEGER NOT NULL REFERENCES asignaturas(id) ON DELETE CASCADE,
    sede_id INTEGER NOT NULL REFERENCES sedes(id) ON DELETE CASCADE,
    titulo VARCHAR(255),
    nombre_archivo_original VARCHAR(255) NOT NULL,
    
    -- Google Drive
    drive_file_id VARCHAR(255) NOT NULL UNIQUE,
    drive_view_link TEXT,
    drive_embed_link TEXT,
    drive_download_link TEXT,
    
    tamano_bytes INTEGER,
    tipo_archivo VARCHAR(10) CHECK (tipo_archivo IN ('pdf', 'docx')),
    fecha_subida TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```
**Flujo:**
1. Docente sube archivo PDF/DOCX
2. Backend lo guarda en Google Drive
3. Se almacena metadata + links en PostgreSQL
4. Coordinador puede visualizar y comentar

**Relaciones:** N:1 con `usuarios`, `asignaturas`, `sedes`  
**Índices:** `idx_planeaciones_docente`, `idx_planeaciones_asignatura`, `idx_planeaciones_sede`, `idx_planeaciones_fecha`, `idx_planeaciones_drive_id`  

##### Tabla: `comentarios`
Retroalimentación de coordinadores sobre planeaciones.
```sql
CREATE TABLE comentarios (
    id SERIAL PRIMARY KEY,
    planeacion_id INTEGER NOT NULL REFERENCES planeaciones(id) ON DELETE CASCADE,
    coordinador_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    contenido TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CHECK (LENGTH(contenido) >= 10)
);
```
**Funcionalidad:**
- Coordinador revisa planeación y escribe comentarios
- Docente recibe notificación por email

**Índices:** `idx_comentarios_planeacion`, `idx_comentarios_coordinador`, `idx_comentarios_fecha`  

##### Tabla: `planeaciones_destacadas`
Planeaciones marcadas como referentes institucionales.
```sql
CREATE TABLE planeaciones_destacadas (
    id SERIAL PRIMARY KEY,
    planeacion_id INTEGER NOT NULL REFERENCES planeaciones(id) ON DELETE CASCADE,
    coordinador_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    razon TEXT NOT NULL,                         -- Por qué es destacada (min 20 chars)
    activa BOOLEAN DEFAULT TRUE,
    visualizaciones INTEGER DEFAULT 0,           -- Gamificación
    fecha_destacado TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(planeacion_id),
    CHECK (LENGTH(razon) >= 20)
);
```
**Propósito:**
- Crear banco de mejores prácticas institucionales
- Reconocimiento público a docentes
- Visible para TODOS los docentes (independiente de área)

**Índices:** `idx_destacadas_planeacion`, `idx_destacadas_activa`, `idx_destacadas_fecha`, `idx_destacadas_visualizaciones`  

---

#### 🎯 **MÓDULO 2: PROYECTOS PEDAGÓGICOS**

##### Tabla: `proyectos`
Proyectos pedagógicos creados por docentes.
```sql
CREATE TABLE proyectos (
    id SERIAL PRIMARY KEY,
    docente_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT NOT NULL,
    objetivos TEXT,
    fecha_inicio DATE NOT NULL,
    fecha_fin_estimada DATE,
    
    -- Documento base (opcional)
    drive_file_id VARCHAR(255) UNIQUE,
    drive_view_link TEXT,
    drive_embed_link TEXT,
    drive_download_link TEXT,
    nombre_archivo_original VARCHAR(255),
    
    estado VARCHAR(50) DEFAULT 'activo' CHECK (estado IN ('activo', 'pausado', 'completado', 'cancelado')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CHECK (LENGTH(titulo) >= 5),
    CHECK (LENGTH(descripcion) >= 20)
);
```
**Estados:**
- `activo`: En desarrollo
- `pausado`: Temporalmente detenido
- `completado`: Finalizado
- `cancelado`: Descartado

**Índices:** `idx_proyectos_docente`, `idx_proyectos_estado`, `idx_proyectos_fecha_inicio`, `idx_proyectos_fecha_fin`  

##### Tabla: `evidencias_proyecto`
Documentación del progreso/avance del proyecto.
```sql
CREATE TABLE evidencias_proyecto (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    fecha_evidencia DATE NOT NULL,              -- Fecha del avance
    
    drive_file_id VARCHAR(255) NOT NULL UNIQUE,
    drive_view_link TEXT,
    drive_embed_link TEXT,
    drive_download_link TEXT,
    nombre_archivo_original VARCHAR(255),
    tipo_archivo VARCHAR(20),                   -- pdf, docx, imagen, video
    tamano_bytes INTEGER,
    subido_por INTEGER REFERENCES usuarios(id),
    created_at TIMESTAMP DEFAULT NOW(),
    CHECK (LENGTH(titulo) >= 5)
);
```
**Tipos de archivo soportados:** PDF, DOCX, JPG, PNG, MP4, Excel  
**Visualización:** Timeline cronológico en frontend  

**Índices:** `idx_evidencias_proyecto_proyecto`, `idx_evidencias_proyecto_fecha`, `idx_evidencias_proyecto_tipo`, `idx_evidencias_proyecto_created`  

##### Cálculo de Progreso de Proyecto
**Función PostgreSQL:**
```sql
CREATE OR REPLACE FUNCTION calcular_progreso_proyecto(proyecto_id_param INTEGER)
RETURNS DECIMAL AS $$
DECLARE
    fecha_inicio DATE;
    fecha_fin DATE;
    total_evidencias INTEGER;
    meses_transcurridos DECIMAL;
    meses_totales DECIMAL;
    progreso DECIMAL;
BEGIN
    SELECT p.fecha_inicio, p.fecha_fin_estimada, COUNT(ep.id)
    INTO fecha_inicio, fecha_fin, total_evidencias
    FROM proyectos p
    LEFT JOIN evidencias_proyecto ep ON p.id = ep.proyecto_id
    WHERE p.id = proyecto_id_param
    GROUP BY p.id, p.fecha_inicio, p.fecha_fin_estimada;
    
    meses_transcurridos := EXTRACT(YEAR FROM AGE(CURRENT_DATE, fecha_inicio)) * 12 +
                          EXTRACT(MONTH FROM AGE(CURRENT_DATE, fecha_inicio));
    
    meses_totales := EXTRACT(YEAR FROM AGE(fecha_fin, fecha_inicio)) * 12 +
                    EXTRACT(MONTH FROM AGE(fecha_fin, fecha_inicio));
    
    IF meses_transcurridos > 0 THEN
        progreso := LEAST((total_evidencias::DECIMAL / meses_transcurridos) * 100, 100);
    ELSE
        progreso := 0;
    END IF;
    
    RETURN ROUND(progreso, 2);
END;
$$ LANGUAGE plpgsql;
```

##### Tabla: `comentarios_proyecto`
Retroalimentación sobre proyectos o evidencias específicas.
```sql
CREATE TABLE comentarios_proyecto (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER REFERENCES proyectos(id) ON DELETE CASCADE,
    evidencia_id INTEGER REFERENCES evidencias_proyecto(id) ON DELETE CASCADE,
    coordinador_id INTEGER NOT NULL REFERENCIAS usuarios(id) ON DELETE CASCADE,
    contenido TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CHECK (
        (proyecto_id IS NOT NULL AND evidencia_id IS NULL) OR
        (proyecto_id IS NULL AND evidencia_id IS NOT NULL)
    ),
    CHECK (LENGTH(contenido) >= 10)
);
```
**Lógica:** Un comentario es SOBRE el proyecto general O sobre una evidencia específica, nunca ambos  

**Índices:** `idx_comentarios_proyecto_proyecto`, `idx_comentarios_proyecto_evidencia`, `idx_comentarios_proyecto_coordinador`, `idx_comentarios_proyecto_fecha`  

---

#### 📅 **MÓDULO 3: CRONOGRAMAS INDIVIDUALES**

##### Tabla: `cronogramas`
Cronograma anual de actividades de cada docente.
```sql
CREATE TABLE cronogramas (
    id SERIAL PRIMARY KEY,
    docente_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    anio_escolar INTEGER NOT NULL,              -- 2025, 2026, etc.
    periodo VARCHAR(50),                        -- "Anual", "Semestral"
    
    drive_file_id VARCHAR(255) NOT NULL UNIQUE,
    drive_view_link TEXT,
    drive_embed_link TEXT,
    drive_download_link TEXT,
    nombre_archivo_original VARCHAR(255),
    
    total_actividades_estimadas INTEGER,       -- Para cálculo de cumplimiento
    estado VARCHAR(50) DEFAULT 'activo' CHECK (estado IN ('activo', 'completado', 'archivado')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CHECK (LENGTH(titulo) >= 5),
    CHECK (anio_escolar >= 2020 AND anio_escolar <= 2100)
);

CREATE UNIQUE INDEX idx_cronogramas_docente_anio_activo 
ON cronogramas(docente_id, anio_escolar) WHERE estado = 'activo';
```
**Constraint único:** Un docente solo puede tener un cronograma activo por año escolar  

**Índices:** `idx_cronogramas_docente`, `idx_cronogramas_anio`, `idx_cronogramas_estado`, `idx_cronogramas_created`  

##### Tabla: `evidencias_cronograma`
Documentación de cumplimiento de actividades del cronograma.
```sql
CREATE TABLE evidencias_cronograma (
    id SERIAL PRIMARY KEY,
    cronograma_id INTEGER NOT NULL REFERENCES cronogramas(id) ON DELETE CASCADE,
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    actividad_relacionada TEXT NOT NULL,        -- Qué actividad del cronograma evidencia
    fecha_evidencia DATE NOT NULL,
    
    drive_file_id VARCHAR(255) NOT NULL UNIQUE,
    drive_view_link TEXT,
    drive_embed_link TEXT,
    drive_download_link TEXT,
    nombre_archivo_original VARCHAR(255),
    tipo_archivo VARCHAR(20),
    tamano_bytes INTEGER,
    subido_por INTEGER REFERENCES usuarios(id),
    created_at TIMESTAMP DEFAULT NOW(),
    CHECK (LENGTH(titulo) >= 5),
    CHECK (LENGTH(actividad_relacionada) >= 5)
);
```

**Índices:** `idx_evidencias_cronograma_cronograma`, `idx_evidencias_cronograma_fecha`, `idx_evidencias_cronograma_tipo`, `idx_evidencias_cronograma_created`  

##### Cálculo de Cumplimiento de Cronograma
**Función PostgreSQL:**
```sql
CREATE OR REPLACE FUNCTION calcular_cumplimiento_cronograma(cronograma_id_param INTEGER)
RETURNS DECIMAL AS $$
DECLARE
    total_actividades INTEGER;
    total_evidencias INTEGER;
    cumplimiento DECIMAL;
BEGIN
    SELECT c.total_actividades_estimadas, COUNT(ec.id)
    INTO total_actividades, total_evidencias
    FROM cronogramas c
    LEFT JOIN evidencias_cronograma ec ON c.id = ec.cronograma_id
    WHERE c.id = cronograma_id_param
    GROUP BY c.id, c.total_actividades_estimadas;
    
    IF total_actividades IS NULL OR total_actividades = 0 THEN
        total_actividades := 40;
    END IF;
    
    cumplimiento := (total_evidencias::DECIMAL / total_actividades) * 100;
    cumplimiento := LEAST(cumplimiento, 100);
    
    RETURN ROUND(cumplimiento, 2);
END;
$$ LANGUAGE plpgsql;
```

##### Tabla: `comentarios_cronograma`
Retroalimentación sobre cronogramas o evidencias.
```sql
CREATE TABLE comentarios_cronograma (
    id SERIAL PRIMARY KEY,
    cronograma_id INTEGER REFERENCES cronogramas(id) ON DELETE CASCADE,
    evidencia_id INTEGER REFERENCES evidencias_cronograma(id) ON DELETE CASCADE,
    coordinador_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    contenido TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CHECK (
        (cronograma_id IS NOT NULL AND evidencia_id IS NULL) OR
        (cronograma_id IS NULL AND evidencia_id IS NOT NULL)
    ),
    CHECK (LENGTH(contenido) >= 10)
);
```

**Índices:** `idx_comentarios_cronograma_cronograma`, `idx_comentarios_cronograma_evidencia`, `idx_comentarios_cronograma_coordinador`, `idx_comentarios_cronograma_fecha`  

---

#### 👨‍🎓 **MÓDULO 4: OBSERVADOR DE ESTUDIANTES**

##### Tabla: `estudiantes`
Estudiantes ingresados por docentes directores de grupo.
```sql
CREATE TABLE estudiantes (
    id SERIAL PRIMARY KEY,
    grupo_id INTEGER NOT NULL REFERENCES grupos(id) ON DELETE CASCADE,
    numero_documento VARCHAR(20) NOT NULL,
    nombres VARCHAR(150) NOT NULL,
    apellidos VARCHAR(150) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(grupo_id, numero_documento)
);
```
**Nota:** Datos mínimos para cumplir GDPR/protección de datos de menores  

**Índices:** `idx_estudiantes_grupo`, `idx_estudiantes_documento`, `idx_estudiantes_nombres`  

##### Tabla: `observadores`
Observaciones académicas/comportamentales por período.
```sql
CREATE TABLE observadores (
    id SERIAL PRIMARY KEY,
    estudiante_id INTEGER NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
    docente_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    periodo INTEGER NOT NULL CHECK (periodo >= 1 AND periodo <= 4),
    observacion TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(estudiante_id, docente_id, periodo)
);
```
**Períodos:** 4 por año escolar (trimestral/cuatrimestral)  
**Editabilidad:** Docente puede modificar constantemente hasta fin de período  

**Índices:** `idx_observadores_estudiante`, `idx_observadores_docente`, `idx_observadores_periodo`, `idx_observadores_updated`  

##### Generación de PDF de Observador
**Backend genera PDF con:**
1. Datos del estudiante (documento, nombres, apellidos, grado, grupo)
2. Tabla 4x1 con observaciones de cada período
3. Si solo hay observaciones en período 1, tabla se descarga completa (vacía en períodos 2, 3, 4)
4. Formato profesional con logo institucional

**Biblioteca:** ReportLab (Python) o alternativa HTML→PDF  

---

#### 📢 **MÓDULO 5: PUBLICACIONES**

##### Tabla: `publicaciones`
Anuncios/comunicados institucionales de coordinadores y rector.
```sql
CREATE TABLE publicaciones (
    id SERIAL PRIMARY KEY,
    autor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    titulo VARCHAR(255) NOT NULL,
    contenido TEXT NOT NULL,
    
    -- Documento adjunto OPCIONAL
    drive_file_id VARCHAR(255) UNIQUE,
    drive_view_link TEXT,
    drive_embed_link TEXT,
    drive_download_link TEXT,
    nombre_archivo_original VARCHAR(255),
    tipo_archivo VARCHAR(20),
    tamano_bytes INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CHECK (LENGTH(titulo) >= 5),
    CHECK (LENGTH(contenido) >= 10)
);
```

**Características:**
- **Quién publica:** Solo coordinadores y rector
- **Quién ve:** Todos (docentes, coordinadores, rector)
- **Documento adjunto:** OPCIONAL (puede ser solo texto)
- **Sin comentarios:** Comunicación unidireccional
- **Sin vencimiento:** Permanecen indefinidamente
- **Notificaciones:** Email a todos los usuarios cuando se publica
- **Orden:** Más reciente primero

**Ejemplos:**
- Con archivo: "Nuevo formato de planeaciones" + PDF adjunto
- Sin archivo: "Reunión general 20 de mayo en Sede Norte"

**Índices:** `idx_publicaciones_autor`, `idx_publicaciones_fecha`, `idx_publicaciones_updated`  

---

#### 🔔 **SISTEMA DE NOTIFICACIONES Y AUDITORÍA**

##### Tabla: `notificaciones`
Sistema de notificaciones en la aplicación.
```sql
CREATE TABLE notificaciones (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo VARCHAR(50) NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    mensaje TEXT NOT NULL,
    leida BOOLEAN DEFAULT FALSE,
    link VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Tipos de notificaciones:**
- `nuevo_comentario_planeacion`
- `nuevo_comentario_proyecto`
- `nuevo_comentario_cronograma`
- `planeacion_destacada`
- `nueva_publicacion`
- `proyecto_sin_evidencias_30_dias`
- `cronograma_bajo_cumplimiento`

**Índices:** `idx_notificaciones_usuario`, `idx_notificaciones_leida`, `idx_notificaciones_tipo`, `idx_notificaciones_fecha`, `idx_notificaciones_usuario_no_leidas`  

##### Tabla: `actividad_sistema`
Log de auditoría completo.
```sql
CREATE TABLE actividad_sistema (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    accion VARCHAR(100) NOT NULL,
    entidad_tipo VARCHAR(50),
    entidad_id INTEGER,
    detalles JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Propósito:** Cumplimiento, auditoría, análisis de uso, seguridad  

**Índices:** `idx_actividad_usuario`, `idx_actividad_accion`, `idx_actividad_fecha`, `idx_actividad_entidad`  

##### Tabla: `configuracion`
Configuraciones globales del sistema.
```sql
CREATE TABLE configuracion (
    id SERIAL PRIMARY KEY,
    clave VARCHAR(100) NOT NULL UNIQUE,
    valor TEXT,
    descripcion TEXT,
    tipo_dato VARCHAR(20) DEFAULT 'string',
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by INTEGER REFERENCES usuarios(id) ON DELETE SET NULL
);
```

**Configuraciones iniciales:**
```sql
INSERT INTO configuracion (clave, valor, descripcion, tipo_dato) VALUES
('nombre_institucion', 'Institución Educativa San Luis', 'Nombre', 'string'),
('anio_escolar_actual', '2025', 'Año escolar', 'integer'),
('max_size_archivo_mb', '10', 'Tamaño máximo archivo', 'integer'),
('periodos_año_escolar', '4', 'Cantidad períodos', 'integer');
```

---

# 🛠️ STACK TECNOLÓGICO

## BACKEND

### FastAPI (Framework Web)
**Versión:** 0.104+  
**Lenguaje:** Python 3.11+

Framework web moderno y de alto rendimiento para construcción de APIs RESTful. Se eligió por:
- **Rendimiento excepcional:** Comparable a Node.js y Go gracias a Starlette y Pydantic
- **Tipado fuerte:** Validación automática de requests/responses con type hints de Python
- **Documentación automática:** Genera OpenAPI (Swagger) y ReDoc sin configuración adicional
- **Async/await nativo:** Soporte completo para operaciones asíncronas
- **Facilidad de desarrollo:** Sintaxis intuitiva, menos código boilerplate
- **Testing integrado:** Herramientas incorporadas para pruebas unitarias y de integración

**Uso en el proyecto:** Base del servidor API que maneja todas las peticiones HTTP del frontend, gestiona autenticación, permisos y lógica de negocio.

---

### PostgreSQL (Base de Datos Relacional)
**Versión:** 15+  
**Modo:** Auto-gestionado en VPS

Sistema de gestión de base de datos relacional de código abierto. Se eligió por:
- **Integridad referencial robusta:** FOREIGN KEYS, UNIQUE constraints, CHECK constraints
- **ACID completo:** Garantiza consistencia de datos críticos
- **Índices avanzados:** B-tree para consultas rápidas
- **JSON/JSONB:** Soporte nativo para datos semi-estructurados (metadata)
- **Funciones y triggers:** Lógica de negocio a nivel de base de datos
- **Extensibilidad:** Funciones personalizadas en PL/pgSQL
- **Gratuito y maduro:** 30+ años de desarrollo activo

**Uso en el proyecto:** Almacena TODA la metadata del sistema (usuarios, estructura académica, observaciones), NO almacena archivos. Total estimado: 70 MB/año.

---

### SQLAlchemy (ORM)
**Versión:** 2.0

Object-Relational Mapper que traduce entre objetos Python y tablas PostgreSQL. Se eligió por:
- **Abstracción de SQL:** Escribir consultas en Python en lugar de SQL puro
- **Relaciones automáticas:** Manejo de FOREIGN KEYS como atributos de objetos
- **Lazy/Eager loading:** Control sobre carga de relaciones
- **Migraciones con Alembic:** Versionado automático de esquema de base de datos
- **Type safety:** Integración perfecta con type hints de Python
- **Query builder potente:** Desde consultas simples hasta JOINs complejos

**Uso en el proyecto:** Define los 24 modelos (tablas) como clases Python, gestiona todas las consultas a PostgreSQL, mantiene sincronización entre código y base de datos.

---

### Alembic (Migraciones de Base de Datos)
**Versión:** 1.12+

Herramienta de migración de esquema de base de datos. Se eligió por:
- **Versionado de esquema:** Cada cambio en la BD queda registrado con timestamp
- **Rollback seguro:** Posibilidad de deshacer cambios si algo falla
- **Autogeneración:** Detecta diferencias entre modelos SQLAlchemy y BD actual
- **Trabajo en equipo:** Evita conflictos cuando múltiples desarrolladores modifican BD
- **Producción segura:** Migraciones probadas en desarrollo antes de aplicar en producción

**Uso en el proyecto:** Crear y aplicar las 24 tablas iniciales, agregar índices, modificar constraints, agregar nuevas columnas en futuras versiones.

---

### Celery (Procesamiento Asíncrono)
**Versión:** 5.3+  
**Broker/Backend:** Redis 7

Sistema de cola de tareas distribuidas para procesamiento en background. Se eligió por:
- **Tareas asíncronas:** Operaciones pesadas sin bloquear requests HTTP
- **Programación de tareas:** Cron jobs para reportes mensuales automáticos
- **Retry automático:** Reintentos configurables en caso de fallos
- **Monitoreo:** Flower para visualizar estado de workers y tasks
- **Escalabilidad:** Múltiples workers pueden procesar tareas en paralelo
- **Priorización:** Colas con diferentes prioridades

**Uso en el proyecto:**
- Envío de emails en background (comentarios, publicaciones)
- Generación de reportes PDF mensuales
- Alertas automáticas (proyectos sin evidencias, cronogramas bajo cumplimiento)

---

### Redis (Cache y Message Broker)
**Versión:** 7 Alpine

Base de datos en memoria de alta velocidad. Se eligió por:
- **Velocidad extrema:** Lectura/escritura en microsegundos
- **Message broker:** Cola de tareas para Celery
- **Cache de sesiones:** Almacenar JWT blacklist o rate limiting
- **Pub/Sub:** Notificaciones en tiempo real (futuro)
- **Ligero:** Imagen Docker Alpine de solo 10MB
- **TTL automático:** Expiración automática de claves

**Uso en el proyecto:** Broker para Celery (comunicación entre FastAPI y workers), cache de consultas frecuentes del dashboard.

---

### Google Drive API (Almacenamiento de Archivos)
**Biblioteca:** google-api-python-client + google-auth

API oficial de Google para interactuar con Google Drive. Se eligió por:
- **Gratuito:** 15 GB por cuenta sin costo
- **Escalable:** Múltiples cuentas (multi-tenant) cuando se llene
- **Visualización integrada:** iframes con preview nativo de documentos
- **Permisos granulares:** Control de acceso por archivo
- **Búsqueda potente:** API de búsqueda de archivos
- **Compartir enlaces:** URLs directas de visualización y descarga
- **No requiere infraestructura:** Google maneja toda la infraestructura

**Uso en el proyecto:** Almacena TODOS los archivos (planeaciones, proyectos, cronogramas, publicaciones). PostgreSQL solo guarda `drive_file_id` y links. Ahorra ~$300 en 5 años vs S3/Spaces.

**Estrategia multi-cuenta:** Cuando se llene una cuenta (15 GB), crear segunda cuenta service y rotar uploads. Total capacidad: 30-45 GB con 2-3 cuentas.

---

### Pydantic (Validación de Datos)
**Versión:** 2.0+

Biblioteca de validación de datos con type hints. Se eligió por:
- **Validación automática:** Valida requests HTTP en tiempo real
- **Serialización:** Convierte objetos Python a JSON automáticamente
- **Error messages claros:** Indica exactamente qué campo falló y por qué
- **Type coercion:** Convierte "123" a 123 automáticamente
- **Documentación automática:** FastAPI usa Pydantic para generar OpenAPI
- **Rendimiento:** Escrito en Rust para validación ultra-rápida

**Uso en el proyecto:** Define todos los schemas de request/response (24+ schemas), valida cada campo de entrada, documenta automáticamente la API.

---

### Passlib + Bcrypt (Seguridad de Passwords)
**Versión:** Passlib 1.7+

Biblioteca de hashing de passwords. Se eligió por:
- **Bcrypt:** Algoritmo de hashing one-way con salt automático
- **Adaptativo:** Se puede aumentar el costo computacional con el tiempo
- **Seguro:** Imposible de revertir (no se puede obtener password original)
- **Estándar de industria:** Usado por bancos y aplicaciones críticas
- **Validación sencilla:** Compara hash almacenado vs password ingresado

**Uso en el proyecto:** Hashea passwords de usuarios antes de almacenar en BD, valida login comparando hash. NUNCA se almacena password en texto plano.

---

### Python-JOSE (JSON Web Tokens)
**Versión:** 3.3+

Implementación de JWT para Python. Se eligió por:
- **Stateless authentication:** No requiere almacenar sesiones en servidor
- **Claims personalizados:** Incluir user_id, rol, permisos en el token
- **Expiración automática:** Tokens válidos por 24 horas
- **Firma digital:** Verificación criptográfica que no fue modificado
- **Estándar industria:** RFC 7519

**Uso en el proyecto:** Genera JWT después de login exitoso, valida JWT en cada request protegido, incluye rol del usuario para autorización RBAC.

---

### ReportLab (Generación de PDFs)
**Versión:** 4.0+

Biblioteca para crear documentos PDF programáticamente. Se eligió por:
- **Generación desde cero:** Crea PDFs sin plantillas
- **Control total:** Posicionamiento exacto de elementos
- **Tablas y gráficos:** Soporte para estructuras complejas
- **Imágenes:** Inserción de logos y gráficos
- **Pure Python:** Sin dependencias externas
- **Producción:** Usado por empresas para facturas, reportes

**Uso en el proyecto:** Genera PDF de observador de estudiante (datos + tabla 4 períodos), genera reportes mensuales institucionales con gráficos y estadísticas.

---

### Pytest (Testing)
**Versión:** 7.4+

Framework de testing para Python. Se eligió por:
- **Sintaxis simple:** Tests legibles con `assert` estándar
- **Fixtures:** Setup/teardown reutilizables
- **Parametrización:** Ejecutar mismo test con diferentes datos
- **Coverage:** Mide porcentaje de código testeado
- **Plugins:** Extensiones para async, DB, mocking
- **Fast:** Ejecución paralela de tests

**Uso en el proyecto:** Tests de integración de APIs, tests de permisos RBAC, tests de servicios de Google Drive.

---

## FRONTEND

### Vue.js 3 (Framework JavaScript)
**Versión:** 3.3+  
**API Style:** Composition API

Framework progresivo para construcción de interfaces de usuario. Se eligió por:
- **Reactividad potente:** Sistema reactivo basado en Proxy de ES6
- **Composition API:** Mejor organización de lógica reutilizable
- **Single File Components:** HTML + CSS + JS en un solo archivo .vue
- **Virtual DOM:** Actualizaciones eficientes del DOM
- **TypeScript opcional:** Soporte completo pero no obligatorio
- **Ecosystem maduro:** Vue Router, Pinia, Vite
- **Curva de aprendizaje moderada:** Más fácil que React/Angular
- **Documentación excelente:** Guías claras y ejemplos prácticos

**Uso en el proyecto:** Base del frontend SPA (Single Page Application), maneja toda la interfaz de usuario, comunicación con backend vía REST API, navegación entre vistas.

---

### Vite (Build Tool)
**Versión:** 5.0+

Herramienta de construcción de frontend de próxima generación. Se eligió por:
- **Hot Module Replacement ultra-rápido:** Cambios visibles en <1 segundo
- **Build optimizado:** Rollup para producción (code splitting, tree shaking)
- **ES modules nativos:** No transpila en desarrollo
- **TypeScript sin configuración:** Soporte out-of-the-box
- **Plugins:** Ecosystem rico de extensiones
- **Modern por defecto:** Genera código ES2020+

**Uso en el proyecto:** Servidor de desarrollo local con recarga instantánea, build de producción optimizado, manejo de assets (imágenes, CSS), transpilación de .vue a JavaScript.

---

### Pinia (State Management)
**Versión:** 2.1+

Sistema de gestión de estado global para Vue. Se eligió por:
- **Successor oficial de Vuex:** Recomendado por el equipo de Vue
- **Composition API nativa:** Stores con `ref()` y `computed()`
- **TypeScript first:** Inferencia automática de tipos
- **DevTools:** Inspección de estado en tiempo real
- **Modular:** Un store por módulo (planeaciones, proyectos, etc.)
- **SSR ready:** Soporte para Server-Side Rendering (futuro)

**Uso en el proyecto:** 11 stores (auth, planeaciones, proyectos, cronogramas, observadores, publicaciones, dashboard, usuarios, sedes, grupos, notificaciones). Centraliza estado compartido entre componentes.

---

### Vue Router (Navegación)
**Versión:** 4.2+

Router oficial para aplicaciones Vue.js. Se eligió por:
- **Navegación declarativa:** Rutas definidas como objetos
- **Rutas anidadas:** Layouts con children routes
- **Navigation guards:** Protección de rutas por autenticación/permisos
- **History mode:** URLs limpias sin `#` (HTML5 History API)
- **Lazy loading:** Carga componentes solo cuando se necesitan
- **Scroll behavior:** Control de posición del scroll en navegación

**Uso en el proyecto:** Define 40+ rutas (docente/*, coordinador/*, rector/*), protege rutas privadas con guards, implementa redirección según rol de usuario.

---

### Tailwind CSS (Framework CSS)
**Versión:** 3.4+

Framework CSS utility-first para diseño rápido. Se eligió por:
- **Utility classes:** Clases pequeñas y componibles (`flex`, `p-4`, `text-blue-600`)
- **No CSS custom:** Todo se hace con clases predefinidas
- **Responsive por defecto:** Prefijos `sm:`, `md:`, `lg:` para breakpoints
- **Dark mode:** Soporte nativo con `dark:` prefix
- **PurgeCSS automático:** Elimina clases no usadas (bundle pequeño)
- **Customizable:** Configuración en `tailwind.config.js`
- **Productividad alta:** Diseño rápido sin salir del HTML

**Uso en el proyecto:** Todo el styling del frontend, diseño responsivo, componentes visuales (cards, tables, modals), sistema de colores institucional.

---

### Axios (HTTP Client)
**Versión:** 1.6+

Cliente HTTP basado en promesas para navegador y Node.js. Se eligió por:
- **Interceptors:** Añadir JWT automáticamente a requests
- **Error handling:** Captura errores HTTP centralizadamente
- **Timeout:** Control de tiempos de espera
- **Cancel requests:** Cancelar peticiones en vuelo
- **Progress tracking:** Monitorear progreso de uploads
- **Transformers:** Modificar requests/responses automáticamente
- **Browser + Node:** Mismo código en cliente y servidor

**Uso en el proyecto:** Todas las comunicaciones con backend API, interceptor para añadir JWT token, interceptor para logout automático en 401, manejo global de errores.

---

### Chart.js (Visualización de Datos)
**Versión:** 4.4+

Biblioteca de gráficos JavaScript simple pero flexible. Se eligió por:
- **8 tipos de gráficos:** Line, bar, pie, doughnut, radar, etc.
- **Responsive:** Se adapta automáticamente al tamaño del contenedor
- **Animaciones fluidas:** Transiciones suaves entre estados
- **Interactivo:** Tooltips, hover effects, legends clicables
- **Canvas-based:** Rendimiento excelente incluso con muchos datos
- **Plugins:** Extensible con complementos custom
- **Vue wrapper:** vue-chartjs para integración perfecta

**Uso en el proyecto:** Dashboard con gráficos de progreso de proyectos, comparativas entre sedes, evolución temporal de métricas.

---

### Lucide Icons (Íconos)
**Versión:** lucide-vue-next

Set de íconos open-source hermosos y consistentes. Se eligió por:
- **800+ íconos:** Cobertura completa de necesidades UI
- **SVG optimizados:** Tamaño pequeño y escalables
- **Vue components:** Uso como componentes nativos `<FileIcon />`
- **Customizable:** Color, tamaño, stroke width
- **Tree-shakeable:** Solo incluye íconos usados
- **Consistente:** Diseño uniforme en todos los íconos

**Uso en el proyecto:** Íconos en toda la UI (navegación, botones, cards, estados), mejora la comprensión visual, consistencia de diseño.

---

### Date-fns (Manipulación de Fechas)
**Versión:** 2.30+

Biblioteca moderna para trabajar con fechas. Se eligió por:
- **Inmutable:** No muta objetos Date
- **Tree-shakeable:** Solo importas funciones que usas
- **i18n:** Localización para español colombiano
- **Pure functions:** Sin side effects
- **TypeScript:** Totalmente tipado
- **Modular:** Importar solo lo necesario

**Uso en el proyecto:** Formateo de fechas en tablas y cards, cálculos de días transcurridos, comparación de fechas para alertas, conversión entre zonas horarias.

---

### VeeValidate (Validación de Formularios)
**Versión:** 4.11+

Biblioteca de validación de formularios para Vue. Se eligió por:
- **Composition API:** Integración nativa con Vue 3
- **Yup integration:** Schemas de validación reutilizables
- **Async validation:** Validación en servidor (check username)
- **Error messages:** Mensajes personalizados por campo
- **Touch/dirty tracking:** Estado del formulario
- **Field-level validation:** Valida al escribir o al submit

**Uso en el proyecto:** Validación de formularios de login, creación de proyectos, ingreso de estudiantes, subida de archivos con validación de tipo/tamaño.

---

## INFRAESTRUCTURA

### Docker (Contenedorización)
**Versión:** 24.0+

Plataforma para desarrollo, envío y ejecución de aplicaciones en contenedores. Se eligió por:
- **Aislamiento:** Cada servicio en su propio contenedor
- **Reproducibilidad:** Mismo ambiente en desarrollo y producción
- **Portabilidad:** Funciona igual en cualquier máquina
- **Versionado:** Imágenes etiquetadas (v1.0, v1.1)
- **Orquestación:** Docker Compose para multi-container
- **Recursos controlados:** Límites de CPU y memoria por contenedor

**Uso en el proyecto:** Contenedor para backend (FastAPI), contenedor para Celery worker, contenedor para PostgreSQL, contenedor para Redis, contenedor para Nginx.

---

### Docker Compose (Orquestación Multi-Container)
**Versión:** 2.20+

Herramienta para definir y ejecutar aplicaciones Docker multi-contenedor. Se eligió por:
- **YAML declarativo:** Define servicios, networks, volumes en un archivo
- **Networking automático:** Comunicación entre contenedores por nombre
- **Volúmenes:** Persistencia de datos de PostgreSQL
- **Env variables:** Configuración por ambiente (dev/prod)
- **One command deploy:** `docker-compose up -d`
- **Logs centralizados:** Ver logs de todos los servicios

**Uso en el proyecto:** Orquesta 5 contenedores (postgres, redis, backend, celery, frontend), gestiona red interna, maneja volúmenes de base de datos, simplifica despliegue.

---

### Nginx (Web Server y Reverse Proxy)
**Versión:** 1.24+

Servidor web de alto rendimiento y reverse proxy. Se eligió por:
- **Alto rendimiento:** Maneja miles de conexiones concurrentes
- **Reverse proxy:** Dirige tráfico a backend según URL
- **Static files:** Sirve frontend (HTML/CSS/JS) directamente
- **SSL termination:** Maneja HTTPS, descarga backend
- **Compression:** Gzip automático de respuestas
- **Load balancing:** Distribución de carga (futuro)
- **Buffer de uploads:** Maneja archivos grandes sin saturar backend

**Uso en el proyecto:** Sirve frontend estático desde `/var/www`, proxy de `/api/*` hacia FastAPI:8000, maneja certificados SSL, limita tamaño de uploads a 15MB.

---

### Let's Encrypt (Certificados SSL)
**Tool:** Certbot

Autoridad certificadora gratuita y automatizada. Se eligió por:
- **Gratuito:** Certificados SSL sin costo
- **Automatizado:** Certbot configura Nginx automáticamente
- **Auto-renovación:** Se renueva cada 60 días sin intervención
- **Trusted:** Reconocido por todos los navegadores
- **ACME protocol:** Validación automática de dominio

**Uso en el proyecto:** HTTPS obligatorio en producción, certificado para `sgpi.institucioneducativasanluis.edu.co`, renovación automática con cron job.

---

### Ubuntu Server (Sistema Operativo)
**Versión:** 22.04 LTS

Sistema operativo Linux para servidores. Se eligió por:
- **LTS:** Soporte extendido por 5 años
- **Estable:** Usado en millones de servidores
- **Documentación abundante:** Solución a cualquier problema online
- **APT:** Gestor de paquetes robusto
- **Seguridad:** Actualizaciones automáticas de seguridad
- **Ligero:** Versión Server sin GUI

**Uso en el proyecto:** Sistema operativo del VPS, ejecuta Docker, Nginx, cron jobs de backup.

---

### VPS Provider (Hosting)
**Opciones:** Contabo o Hetzner  
**Specs:** 2GB RAM, 50GB SSD, 1 vCPU  
**Costo:** $5/mes

Servidor privado virtual. Se eligió por:
- **Económico:** $5/mes vs $50+/mes en AWS/DigitalOcean
- **Root access:** Control total del servidor
- **IP fija:** Para configurar DNS
- **Uptime alto:** 99.9% garantizado
- **Backups:** Snapshots manuales disponibles
- **Tráfico ilimitado:** Sin cargos extra por bandwidth

**Uso en el proyecto:** Hospeda TODA la aplicación (PostgreSQL, Redis, Backend, Frontend, Nginx) en un solo servidor. Suficiente para 50 usuarios concurrentes.

---

## HERRAMIENTAS DE DESARROLLO

### Git (Control de Versiones)
**Versión:** 2.40+

Sistema de control de versiones distribuido. Se usa por:
- **Histórico completo:** Cada cambio queda registrado
- **Branching:** Desarrollo paralelo sin conflictos
- **Rollback:** Volver a versión anterior si algo falla
- **Colaboración:** Múltiples desarrolladores simultáneamente
- **GitHub/GitLab:** Hosting remoto del código

**Uso en el proyecto:** Versionado de código fuente, branches por feature, pull requests para code review, tags para releases (v1.0, v1.1).

---

### VS Code (Editor de Código)
**Recomendado con extensiones:**
- Python
- Vue - Official
- Tailwind CSS IntelliSense
- Prettier
- ESLint
- PostgreSQL

Editor moderno con soporte para todo el stack.

---

### Postman / Insomnia (Testing de API)
Herramientas para probar endpoints REST durante desarrollo.

---

### pgAdmin / DBeaver (Gestión de BD)
Interfaces gráficas para inspeccionar y consultar PostgreSQL.

---