# Design: Gestión de fuentes de conocimiento del chatbot (CU-12)

## Context

Hoy el chatbot (CU-11, capacidad `chatbot-assistant`) responde con el conocimiento general del modelo más una búsqueda substring sobre `AGENTS.md`, `README.md` y `casos_de_uso.md` mediante la tool `search_platform_docs` (`backend/services/chat_service.py:247-250`, helper `_search_platform_docs` en `backend/services/chat_service.py:55-86`). No existe mecanismo para que el Administrador cargue guías, FAQs ni respuestas aprobadas, ni para priorizar información autorizada por rol.

CU-12 (cambio `add-chatbot-knowledge-sources`) introduce:

- Una capacidad nueva, `chatbot-knowledge-sources`: gestión administrativa de fuentes (carga, listado, eliminación) con procesamiento/indexado sincrónico y estados `processing` / `active` / `error`.
- Un delta de la capacidad existente `chatbot-assistant`: la referencia principal del chatbot pasa a ser las fuentes administradas; se añade la tool de recuperación RAG scopeada por rol en `build_tools(current_user)` y la priorización de respuestas aprobadas.

Restricciones del proyecto que el diseño respeta: regla de dependencias `routes → services → models`, permisos SIEMPRE en backend desde la sesión Flask, garantía de solo lectura del agente, portabilidad Windows/Linux/macOS, design system de frontend (tokens + `src/ui/`), migraciones Alembic incrementales.

## Technical Approach

Una entidad nueva `KnowledgeSource` en SQLite guarda la metadata administrativa (nombre, propósito, roles destino, tipo, estado). El archivo original se persiste en disco y su contenido se trocea, vectoriza (embeddings Ollama `nomic-embed-text`) e indexa en una colección local de ChromaDB, de forma síncrona dentro del request de carga. El chatbot recupera fragmentos mediante una nueva tool de solo lectura `search_knowledge_sources` agregada en `build_tools(current_user)` (`backend/services/chat_service.py:160-259`), que filtra por rol (tomado del usuario de sesión, nunca del modelo) y por fuentes en estado `active`, y prioriza los fragmentos de `approved_answer`. La tool `search_platform_docs` se reemplaza (ver Architecture Decisions). Toda la lógica vive en `backend/services/knowledge_service.py`; el blueprint `backend/blueprints/knowledge.py` solo orquesta HTTP siguiendo el patrón de `backend/blueprints/users.py:29-41`.

## Architecture Decisions

### Decision: Límite de tamaño de archivo = 1 MB (1.048.576 bytes)

**Choice**: `KNOWLEDGE_MAX_FILE_BYTES`, default `1048576` (1 MB), validado en `knowledge_service` con rechazo HTTP 400.

**Alternatives considered**: sin límite (depend MAX_CONTENT_LENGTH de Flask, que aborta con error genérico de Werkzeug); 5 MB; 10 MB.

**Rationale**: el corpus es texto plano (`.md`/`.txt`); 1 MB equivale a cientos de páginas, muy por encima de cualquier guía o FAQ del campus. Con `chunk_size=500` produce como máximo ~2.000 fragmentos, un volumen manejable en una colección local y compatible con el procesamiento síncrono dentro del request (el timeout de Ollama ya configurado es `OLLAMA_TIMEOUT=120`, `backend/config/config.py:23`). Un límite más alto aumenta el riesgo de timeout del request sin beneficio práctico; sin límite, un upload enorme saturaría la memoria y el índice. El límite es explícito y configurable por entorno, no implícito del servidor.

### Decision: Fuente sin roles destino = aplicable a todos los roles autenticados

**Choice**: `target_roles` vacío u omitido en `POST` significa "aplicable a todos los roles autenticados". El frontend por defecto envía los tres roles tildados; el caso vacío queda soportado en el servicio y en el filtrado.

**Alternatives considered**: rechazar con 400 si no se envía al menos un rol.

**Rationale**: el spec de la capacidad ya lo fija como requisito: "Cuando una fuente no define roles destino, su contenido aplica a todos los usuarios autenticados" (`specs/chatbot-knowledge-sources/spec.md`, Requirement "Recuperación de conocimiento scopeada por rol"). Rechazar sería contradictar un requisito ya aprobado. La seguridad no se debilita: el contenido igualmente solo llega a usuarios autenticados y su difusión amplia es una decisión explícita del Administrador. En ChromaDB se representa con los tres flags de rol en `true` (ver esquema de metadata).

### Decision: Fallo de procesamiento persiste la fila en `error` (con `error_message`)

**Choice**: dos tramos distintos:
- **Rechazo de validación** (extensión, tamaño, campos faltantes/inválidos): HTTP 400 **antes** de persistir nada; no se crea fila ni se guarda archivo (regla 4/A4).
- **Fallo de procesamiento** (lectura, chunking, embeddings, indexado): la fila persiste en estado `error` con el motivo en una columna `error_message`, se compensa el índice (se eliminan los fragmentos ya agregados de esa fuente), el archivo almacenado se conserva y el endpoint responde HTTP 400 con mensaje amable (reglas 5/13, escenario A5). La fuente `error` es visible y eliminable por el Administrador desde el listado.

**Alternatives considered**: descartar la fila y el archivo en todo fallo (diagnóstico imposible para el Administrador); responder 201 con `status=error` (contradice "informa que no pudo completar la operación").

**Rationale**: el spec exige que A5 informe el fallo y que la fuente quede `error`; un fallo silencioso deja al Administrador sin diagnóstico (causa típica: Ollama sin el modelo `nomic-embed-text`). El estado `error` además queda excluido de la recuperación por diseño (el filtrado solo acepta `active`). El fallo de validación en cambio no debe dejar rastro: nunca llegó a ser una fuente.

### Decision: Variables de entorno nuevas

**Choice**: se agregan a `Config` (`backend/config/config.py`), siguiendo el patrón de `OLLAMA_*` existente (líneas 21-25), con helper análogo a `_database_uri()` para resolver rutas relativas contra `BACKEND_DIR`:

| Variable | Default | Descripción |
|---|---|---|
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Modelo de embeddings de Ollama |
| `CHROMA_PERSIST_DIR` | `instance/chroma` (resuelto contra `BACKEND_DIR`) | Directorio de persistencia de ChromaDB |
| `CHROMA_COLLECTION` | `campus_knowledge` | Nombre de la colección vectorial |
| `KNOWLEDGE_MAX_FILE_BYTES` | `1048576` | Límite de tamaño del archivo cargado |
| `KNOWLEDGE_UPLOAD_DIR` | `instance/knowledge` (resuelto contra `BACKEND_DIR`) | Directorio de archivos originales cargados |

Se reutilizan sin cambios `OLLAMA_BASE_URL` y `OLLAMA_TIMEOUT`. Las extensiones admitidas (`.md`, `.txt`) quedan como constante del servicio (`KNOWLEDGE_ALLOWED_EXTENSIONS`), no como env: son una regla de negocio, no una opción de despliegue.

**Alternatives considered**: una colección de Chroma por rol (aislamiento físico); HuggingFace embeddings (descartado por la propuesta: sin sentence-transformers/PyTorch).

**Rationale**: consistencia con el patrón de config por env del proyecto; defaults que funcionan out-of-the-box en los tres SO; paths relativos resueltos igual que la DB (portabilidad). Una sola colección con metadata por rol evita duplicar embeddings y simplifica el borrado (un `where={"source_id": id}` en lugar de N colecciones).

### Decision: Borrado no atómico — orden ChromaDB → archivo → fila, con defensa en la recuperación

**Choice**: `delete_source(source_id)` ejecuta en este orden:

1. Cargar la fila (`SELECT`); si no existe → `NotFoundError` → HTTP 404.
2. **Índice vectorial primero**: `collection.delete(where={"source_id": <id>})`. Operación idempotente. Si falla → se aborta con `KnowledgeServiceError` (HTTP 500 con mensaje amable) y la fila **no** se elimina.
3. **Archivo**: `Path.unlink()` best-effort; un `OSError` se loguea (`current_app.logger`) y no interrumpe (el archivo huérfano es inerte y no alcanza a los usuarios).
4. **Fila**: `db.session.delete(row); db.session.commit()`. Si el commit falla → HTTP 500; como el paso 2 ya corrió y es idempotente, reintentar el DELETE converge.

Además, la recuperación del chatbot **nunca confía solo en el índice**: `retrieve_for_user` consulta primero los `id` de fuentes `active` en SQLite y agrega `source_id: {"$in": [...]}` al `where` de ChromaDB. Así, aunque un borrado quede a medias o una fila quede en `error`, ningún fragmento huérfano puede filtrarse al chat (refuerzo de las reglas 5, 11 y 13).

**Alternatives considered**: fila primero y luego índice (riesgo de que fragmentos huérfanos sigan siendo recuperables — la recuperación iría directo a Chroma); transacción Saga completa con compensaciones activas (complejidad innecesaria: el índice es derivado y reconstruible; el archivo es inerte).

**Rationale**: el vector index es el único camino por el cual el contenido llega a los usuarios, así que se retira primero (la regla 11 exige retirar la fuente del mecanismo de recuperación activo). Los otros dos artefactos (archivo, fila) son inertes si quedan huérfanos un instante. La defensa en la recuperación (filtro por `active` ids) hace el estado degradado inocuo. El orden inverso (fila → índice) es el peor: un fallo dejaría contenido recuperable sin registro administrable.

### Decision: `search_platform_docs` se reemplaza por `search_knowledge_sources`

**Choice**: la tool `search_platform_docs` (`backend/services/chat_service.py:247-250`) y su helper `_search_platform_docs` (`:55-86`) se eliminan; `build_tools` incorpora `search_knowledge_sources(query)`. El system prompt (`:138-153`) se reescribe para declarar que las fuentes administradas son la referencia primaria (reglas 8 y 9 de CU-12) y que el conocimiento general del modelo es solo complemento no contradictorio.

**Alternatives considered**: mantener ambas tools (el modelo podría consultar los docs del repo y contradecir las fuentes administradas, diluyendo la prioridad de regla 8/9); dejar solo la LLM sin tool (imposible anclar respuestas).

**Rationale**: el delta de `chatbot-assistant` renombra el requisito a "Respuesta anclada a fuentes de conocimiento administradas": la documentación del repositorio deja de ser la referencia. Mantener las dos tools crea una fuente de contradicción que el spec prohíbe explícitamente ("los conocimientos generales del modelo MAY utilizarse como complemento únicamente cuando no contradigan las fuentes administradas"). Sin fuentes activas pertinentes, el comportamiento cae en "Consulta sin información suficiente" (ya implementado en el prompt). El contrato HTTP del chat (`POST/GET/DELETE /api/chat/messages`) no cambia: el set de tools es interno.

### Decision: Filtrado por rol en ChromaDB con flags booleanos por rol

**Choice**: metadata por fragmento con flags `role_student`, `role_teacher`, `role_admin` (booleanos). La query de un usuario con rol R usa `where: {"$and": [{"source_id": {"$in": [<active ids>]}}, {"role_<R>": True}]}`.

**Alternatives considered**: metadata `target_roles` como lista y filtro `$in`/`$contains` (el soporte de listas en `where` de ChromaDB es dependiente de versión); post-filtrado exclusivamente en Python (trae al modelo fragmentos que jamás deberían salir de Chroma — aunque no se le presenten, aumenta la superficie de error y complica el `k` efectivo).

**Rationale**: los flags por rol convierten el filtro "pertenece a mi rol" en **una sola cláusula `$eq`** con semántica estable en cualquier versión de chromadb/langchain-chroma, sin depender de operadores `$in` sobre listas. El costo es metadata trivial (3 booleanos por fragmento). El post-filtrado en Python queda descartado como mecanismo primario (una fuga en la fuente de datos es peor defecto que un `k` reducido); el ordenamiento por prioridad sí es un post-proceso en Python sobre el resultado ya filtrado (ver Retrieval).

## Data Model

### Entidad `KnowledgeSource` (`backend/models/knowledge_source.py`)

Patrón idéntico a `models/conversation.py` y `models/submission.py` (timestamps timezone-aware con `datetime.now(UTC)`, columnas explícitas):

```python
class KnowledgeSourceType(enum.Enum):
    DOCUMENT = "document"
    APPROVED_ANSWER = "approved_answer"


class KnowledgeSourceStatus(enum.Enum):
    PROCESSING = "processing"
    ACTIVE = "active"
    ERROR = "error"


class KnowledgeSource(db.Model):
    __tablename__ = "knowledge_source"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    source_type = db.Column(
        db.Enum(KnowledgeSourceType, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    status = db.Column(
        db.Enum(KnowledgeSourceStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=KnowledgeSourceStatus.PROCESSING,
    )
    # Lista de valores "student"|"teacher"|"admin"; vacía => aplica a todos.
    target_roles = db.Column(db.JSON, nullable=False, default=list)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)  # nombre uuid en disco
    file_size_bytes = db.Column(db.Integer, nullable=False, default=0)
    chunk_count = db.Column(db.Integer, nullable=False, default=0)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(UTC),
                           onupdate=lambda: datetime.now(UTC))
```

Notas:

- `target_roles` como `db.JSON` (mismo precedente que `Submission.links`, `models/submission.py:16`): son 0..3 valores acotados de un enum de negocio; una tabla join (`knowledge_source_role`) sería complejidad sin beneficio — SQLite no busca eficientemente por JSON igual que un RDBMS, pero la tabla tendrá decenas de filas y el filtro real por rol ocurre en ChromaDB, no en SQLite.
- Enums con `values_callable` igual que `UserRole` (`models/user.py:21-25`) para persistir los valores string.
- Índices: solo la clave primaria. La tabla es chica (corpus administrativo); el `WHERE status = 'active'` de la recuperación escanea pocas filas. Se agrega `ix_knowledge_source_status` únicamente si en medición real aparece como cuello de botella (no anticipar).

### Migración `0009_add_knowledge_source.py`

Patrón de `migrations/versions/0008_add_chat_history.py`: `revision = "0009_add_knowledge_source"`, `down_revision = "0008_add_chat_history"`.

- **upgrade**: `op.create_table("knowledge_source", ...)` con las columnas anteriores (`sa.Enum(..., name="knowledgesourcetype")`, `sa.JSON()`, `server_default=sa.text("CURRENT_TIMESTAMP")` en timestamps, como en 0008); sin índices adicionales.
- **downgrade**: `op.drop_table("knowledge_source")`. No altera entidades previas: rollback trivial.

Registro del modelo: agregar `knowledge_source` al import de `models` en `backend/app.py:42-51`.

## ChromaDB Metadata Schema

Cada fragmento (chunk) indexado lleva `ids=f"{source_id}:{chunk_index}"` y `metadatas`:

| Campo | Tipo | Uso |
|---|---|---|
| `source_id` | int | Borrado por fuente (`where={"source_id": id}`) y filtro `{"$in": [active ids]}` en la recuperación |
| `source_type` | str (`document` \| `approved_answer`) | Detección de prioridad (regla 8) |
| `role_student` | bool | Filtro por rol del usuario |
| `role_teacher` | bool | Filtro por rol del usuario |
| `role_admin` | bool | Filtro por rol del usuario |

Los tres flags se escriben en `true` cuando `target_roles` está vacío (decisión "sin roles destino"). No se indexa `status`: la recuperación filtra por la lista de `active` ids leída de SQLite en cada turno, lo que garantiza que `processing`/`error`/eliminadas nunca participen aunque suyieran a quedar fragmentos. Tampoco se indexa `priority`: la prioridad se deriva de `source_type` en el post-ordenamiento.

## Ingestion Pipeline (síncrono)

`knowledge_service.create_source(file_storage, form_data, ...)`:

```
POST /api/knowledge/sources (multipart)
        │
        ▼
[1] Validación              ext ∈ {.md,.txt}; size ≤ KNOWLEDGE_MAX_FILE_BYTES;
    (fallo → 400,           name/description/source_type/target_roles válidos.
     sin fila)              ── fallo ──→ HTTP 400, nada persistido (A4)
        │ ok
        ▼
[2] Persistir fila          status=processing; stored_filename = uuid4().hex + ext;
    + archivo en disco      guardar en KNOWLEDGE_UPLOAD_DIR/<stored_filename>
        │
        ▼
[3] Leer texto              UTF-8 (decoding estricto-ish: utf-8, errors="replace");
                            contenido vacío tras strip → error
        │
        ▼
[4] Chunking                document: RecursiveCharacterTextSplitter(
                              chunk_size=500, chunk_overlap=50,
                              separators=["\n## ", "\n### ", "\n", ". ", " "])
                            (patrón aprobado de rag-chat/ingest.py:55-59)
                            approved_answer: split por bloques en blanco
                              (cada párrafo no vacío = 1 fragmento, sin overlap)
        │
        ▼
[5] Embeddings + indexado   OllamaEmbeddings(model=OLLAMA_EMBED_MODEL,
                            base_url=OLLAMA_BASE_URL)
                            collection.add(documents, embeddings, ids, metadatas)
        │
        ▼
[6] Activación              status=active, error_message=None, chunk_count=N;
                            commit → HTTP 201 con la fuente serializada (A1 paso 8)
```

**Manejo de errores (A4/A5)**:

- Fallo en [1]: HTTP 400 con el motivo; no hay fila ni archivo.
- Fallo en [2]-[5] (`except Exception` alrededor del bloque): compensación — `collection.delete(where={"source_id": id})` best-effort (por si el fallo fue a mitad de `collection.add`), `status=error`, `error_message` con el motivo resumido, commit; respuesta HTTP 400: `"No se pudo procesar la fuente. Verificá que el servicio de Ollama esté disponible y que el modelo de embeddings ('<OLLAMA_EMBED_MODEL>') esté instalado."` (mensaje amable, sin exponer stack; causa típica documentada en el proposal).
- El estado `processing` solo es visible si el proceso muere a mitad de request (fila quedó sin transición); queda excluido de la recuperación igual que `error`, cumpliendo reglas 5 y 13.

**Costo acotado**: con el techo de 1 MB y `OLLAMA_TIMEOUT=120`, el peor caso de ingesta es aceptable en entorno local; el corpus real del TP es mucho menor. No se implementa cola asíncrona (out of scope, justificado en la propuesta).

## Retrieval & Priority

### Tool RAG en `build_tools(current_user)` (`backend/services/chat_service.py:160`)

```python
@tool
def search_knowledge_sources(query: str) -> str:
    """Busca información en las fuentes de conocimiento autorizadas del campus
    para el rol del usuario autenticado. Incluye respuestas aprobadas."""
    try:
        results = knowledge_service.retrieve_for_user(query, current_user.role)
    except ValidationError as error:
        return str(error)
    if not results:
        return ("No se encontró información en las fuentes de conocimiento "
                "disponibles para tu rol.")
    return json.dumps(results, ensure_ascii=False)
```

- `current_user` viene del cierre de `build_tools(current_user)` igual que las otras tools existentes (patrón de CU-11): la identidad y el rol **nunca** son parámetros del modelo (regla 16 de CU-11, scenario "Rol tomado de la sesión, no del modelo").
- Solo lectura: la tool consulta servicios; no muta nada (garantía de CU-11 preservada).

### `knowledge_service.retrieve_for_user(query, user_role, k=4)`

1. `active_ids = [row.id for row in db.session.execute(select(KnowledgeSource.id).where(status == ACTIVE))]`. Sin fuentes activas → `[]` (el chatbot cae en "sin información suficiente").
2. Embedding de la query con `OllamaEmbeddings` (1 llamada a Ollama por turno de recuperación).
3. `similarity_search(query, k=k, filter={"$and": [{"source_id": {"$in": active_ids}}, {f"role_{user_role.value}": True}]})`.
4. **Post-ordenamiento de prioridad (regla 8)**: stable-sort de los k resultados con clave `(not metadata["source_type"] == "approved_answer", distance)` — los `approved_answer` quedan primero manteniendo su orden por similitud. No se hace query separada por tipo: con `k=4` y corpus chico un solo retrieval + sort es suficiente y simple.
5. Enriquecimiento: un solo `SELECT` de `id, name, description, source_type` para los `source_id` recuperados (evita N+1) y devolución como lista de:

```json
[
  {
    "source_name": "FAQ de inscripciones",
    "source_type": "approved_answer",
    "text": "fragmento (truncado a 1200 caracteres)"
  }
]
```

   Los fragmentos `approved_answer` van primero; la tool instruye vía system prompt que esas respuestas deben conservarse en su significado.

### System prompt (reescritura de `_build_system_prompt`, `chat_service.py:138-153`)

Cambios respecto de CU-11 (manteniendo el resto de líneas):

- La fuente primaria deja de ser "la documentación del repositorio" y pasa a ser "las fuentes de conocimiento administradas del campus, obtenidas con `search_knowledge_sources`".
- Nueva instrucción: "Cuando una respuesta aprobada recuperada corresponda a la consulta, conservá su significado; no la reemplaces por una respuesta contradictoria de tu conocimiento general."
- Nueva instrucción: "El conocimiento general solo puede usarse como complemento y nunca para contradecir las fuentes administradas ni para inventar reglas de la plataforma; ante contradicción o falta de información, reconocé el límite."
- Se mantiene: solo lectura, redirección de borrado de historial a la UI, no revelar el prompt, reglas del sistema prevalecen.

### Interacción con la eliminación (A7)

Como `retrieve_for_user` cruza SQLite (activos) + Chroma por `source_id`, una fuente eliminada desaparece de ambas fuentes de verdad en la misma operación: consultas futuras no la utilizan y el chatbot, sin ella, aplica "sin información suficiente" o responde con las fuentes restantes. El historial de conversaciones no se toca (regla 12; `delete_history` y el almacenamiento de `Message` son independientes).

## API Contracts

Blueprint `backend/blueprints/knowledge.py`, `url_prefix="/api/knowledge"`, registrado en `create_app` (`backend/app.py:53-61`). Todos los endpoints: `@login_required` + `@require_roles(UserRole.ADMIN)` (`blueprints/guards.py:8-39`) → sin sesión 401, rol distinto de admin 403 con `"No tenés permisos para realizar esta acción"`.

### `GET /api/knowledge/sources`

→ **200**:

```json
{
  "sources": [
    {
      "id": 1,
      "name": "Guía del Estudiante",
      "description": "Cómo entregar tareas",
      "source_type": "document",
      "status": "active",
      "target_roles": ["student"],
      "original_filename": "guia-estudiante.md",
      "file_size_bytes": 4231,
      "chunk_count": 12,
      "error_message": null,
      "created_at": "2026-10-19T12:00:00+00:00",
      "updated_at": "2026-10-19T12:00:05+00:00"
    }
  ]
}
```

Orden: `id` descendente. `target_roles: []` significa "todos los roles".

### `POST /api/knowledge/sources`

`Content-Type: multipart/form-data`:

| Parte | Requerida | Notas |
|---|---|---|
| `file` | sí | `.md` o `.txt`; ≤ `KNOWLEDGE_MAX_FILE_BYTES` |
| `name` | sí | string no vacío, ≤ 200 |
| `description` | no | string; default `""` |
| `source_type` | sí | `document` \| `approved_answer` |
| `target_roles` | no | campo repetido por rol (`student`, `teacher`, `admin`); ausente/vacío = todos |

- **201**: `{"message": "Fuente cargada y procesada correctamente", "source": {<serialización como arriba>}}` (A1 paso 8).
- **400**: validación (extensión, tamaño, campos) → sin fila; o fallo de procesamiento → fila en `error` persistida (ver Decisiones). Body: `{"error": "<motivo amable>"}`.
- **401/403**: guards.

El cliente HTTP agrega `postForm(path, formData)` en `frontend/src/api/client.js` (sin header `Content-Type` manual, igual que `request` pero con `FormData`); el resto del cliente no cambia.

### `DELETE /api/knowledge/sources/<int:source_id>`

- **200**: `{"message": "Fuente eliminada"}`.
- **404**: `{"error": "Fuente no encontrada"}` (lanzada vía `NotFoundError`, patrón `users.py:64-67`).
- **500**: `{"error": "No se pudo eliminar la fuente. Intentá nuevamente."}` (`KnowledgeServiceError` desde el fallo del paso Chroma del borrado; patrón del manejo de `ChatServiceError` en `chat.py:40-41`, pero con 500 en vez de 502 porque no hay servicio externo de por medio en el fallo de la capa de datos).

No hay `PUT/PATCH` (edición fuera de alcance, decidido en la propuesta).

## Frontend

Feature `frontend/src/features/knowledge/` (patrón de `features/users/` y `features/chatbot/`):

| Archivo | Contenido |
|---|---|
| `api.js` | `getSources()`, `createSource(formData)` (vía `postForm`), `deleteSource(id)` |
| `KnowledgePage.jsx` | página de gestión (A1, A2, A6) |
| `KnowledgeUploadForm.jsx` | formulario de carga dentro de un `Modal` |
| `SourceDeleteDialog.jsx` (o inline) | confirmación con `ConfirmDialog` |

**KnowledgePage**:

- `PageHeader` con título "Fuentes de conocimiento" y botón "Cargar fuente" (`Button`).
- Listado con `DataTable` (patrón de `UsersPage`) o `Card` por fila: Nombre, Propósito, Tipo (`Badge`: "Documento" / "Respuesta aprobada"), Roles (badges por rol; vacío → "Todos"), Estado (`StatusBadge` con variantes `active`/`processing`/`error`; en `error` se muestra `error_message` en texto secundario), acción Eliminar.
- Estados de carga: `Spinner` al listar; `EmptyState` sin fuentes; `Toast` en éxito/error de altas y bajas (patrón `ToastProvider` de `App.jsx:155`).
- **Eliminar (A2/A6)**: `ConfirmDialog` (intención danger, aviso de que la fuente dejará de estar disponible para el chatbot) → `deleteSource` → refetch + Toast; cancelar cierra sin efectos (A6 es solo UI: nada se envía al backend).
- **Cargar (A1)**: `Modal` + `KnowledgeUploadForm` con `FormField` (nombre, descripción, tipo, checkboxes de roles con los tres tildados por defecto, input `file` accept `.md,.txt`); envío como `FormData`; en 400 se muestra el `error` del backend (la validación del servidor es la fuente de verdad, convención del proyecto).
- `data-testid` en elementos clave (`knowledge-page`, `knowledge-upload-form`, `knowledge-source-row`, `knowledge-delete-confirm`) para la evidencia Playwright.

**Integración en el shell**:

- `frontend/src/app/Sidebar.jsx:3-28`: nuevo item en `NAV_ITEMS`: `{ to: "/knowledge", label: "Fuentes", icon: "bi-bookmark-data-fill", roles: ["admin"] }` (el filtrado por rol ya existe en `:31`).
- `frontend/src/App.jsx`: nueva ruta bajo `ProtectedRoute` con `role="admin"`, patrón de `/users` (líneas 54-61).

Reutiliza design system existente (`src/ui/`: `Button`, `Card`, `Badge`, `StatusBadge`, `PageHeader`, `Spinner`, `EmptyState`, `DataTable`, `FormField`, `Modal`, `ConfirmDialog`, `Toast`), tokens de `src/theme/tokens.css`, sin colores hardcodeados; funciona en claro/oscuro.

## File Changes

| Archivo | Acción | Descripción |
|------|--------|-------------|
| `backend/models/knowledge_source.py` | Crear | Modelo `KnowledgeSource` + enums |
| `backend/migrations/versions/0009_add_knowledge_source.py` | Crear | Migración incremental (upgrade/downgrade) |
| `backend/services/knowledge_service.py` | Crear | Validación, ingesta síncrona, borrado compensado, `retrieve_for_user` |
| `backend/blueprints/knowledge.py` | Crear | `GET/POST/DELETE /api/knowledge/sources`, solo Admin |
| `backend/app.py` | Modificar | Registro de `knowledge_bp` y del modelo en el import de `models` |
| `backend/config/config.py` | Modificar | 5 variables nuevas (tabla de Decisiones) + helper de resolución de dirs |
| `backend/services/chat_service.py` | Modificar | Tool `search_knowledge_sources`; eliminación de `search_platform_docs`/`_search_platform_docs`; system prompt actualizado |
| `backend/requirements.txt` | Modificar | `chromadb` y `langchain-chroma` con versiones fijadas |
| `backend/tests/test_knowledge_service.py` | Crear | Tests de servicio (validación, estados, borrado, retrieval) |
| `backend/tests/test_knowledge_blueprint.py` | Crear | Tests HTTP del blueprint (401/403/200/201/400/404/500) |
| `backend/tests/` (chat existente) | Modificar | Ajustes por reemplazo de la tool y prompt |
| `frontend/src/features/knowledge/` | Crear | `api.js`, `KnowledgePage.jsx`, `KnowledgeUploadForm.jsx` |
| `frontend/src/api/client.js` | Modificar | `postForm(path, formData)` |
| `frontend/src/app/Sidebar.jsx` | Modificar | Item "Fuentes" (admin) |
| `frontend/src/App.jsx` | Modificar | Ruta `/knowledge` (admin) |
| `scripts/smoke_cu12.py` | Crear | Smoke HTTP del CU (patrón `smoke_cu02.py`) |
| `scripts/verify.py` | Modificar | Registrar el smoke de cu12 si el patrón lo requiere |
| `AGENTS.md`, `decisiones.md`, `progreso.md`, `README.md` | Modificar | Docs de cierre (endpoint en tabla API, env vars, roadmap) |

## Testing Strategy

Separación de seams para no depender de Ollama/Chroma en tests: `knowledge_service` resuelve embeddings y colección mediante funciones internas `_get_embeddings()` y `_get_collection()` (lazy, con lock); los tests las monkeypatchean con fakes (lista en memoria que respeta `add`/`delete`/`similarity_search` con filtros). Los tests NUNCA llaman a servicios externos (patrón del suite actual, que tampoco depende de Ollama).

| Capa | Qué se testea | Approach |
|-------|-------------|----------|
| Unit (servicio) | Validación: extensión inválida, tamaño excedido, campos faltantes/inválidos, roles inválidos → `ValidationError`, sin fila creada | `test_knowledge_service.py` con app context de testing |
| Unit (servicio) | Transición de estados: éxito → `active` con `chunk_count`; fallo de embeddings (fake que explota) → fila `error` con `error_message` y compensación de índice (A5) | Fake de colección que registra `delete` |
| Unit (servicio) | Chunking `document` (splitter) y `approved_answer` (1 fragmento por bloque, todos con `source_type=approved_answer`) | Asertación sobre lo agregado al fake |
| Unit (servicio) | Borrado: orden (fake registra llamadas), idempotencia del paso índice, 404, file-unlink tolerante a `OSError` | Monkeypatch de `Path.unlink` |
| Unit (servicio) | Retrieval: sin fuentes activas → `[]`; rol student no recupera fuente solo-teacher (regla 7); fragmentos `approved_answer` quedan primero (regla 8); solo `active_ids` entran al `where` (reglas 5/13) | Fake que aplica el `filter` real |
| Integration (blueprint) | 401 sin sesión, 403 no-admin (A3), 201 carga, 400 extensión/tamaño (A4), 200 listado con metadata, 200/404 delete | Cliente de test de Flask (patrón de `tests/` de users/chat) |
| Integration (chat) | `build_tools` incluye `search_knowledge_sources` y ya no `search_platform_docs`; la tool usa el rol del `current_user` del cierre, no del input; prompt contiene las instrucciones de prioridad | Inspección de tools y del system prompt |
| Smoke HTTP | `scripts/smoke_cu12.py`: login admin → upload .md → poll de listado hasta `active` → consulta al chat que usa la fuente → delete → 404; no-admin → 403 | `scripts/verify.py --cu cu12` con base temporal sembrada (aisla `KNOWLEDGE_UPLOAD_DIR` y `CHROMA_PERSIST_DIR` bajo la base temporal) |
| E2E / evidencia | Playwright claro/oscuro: listado, alta, error de validación, borrado con confirmación (A1/A2/A4/A6), ruta oculta para no-admin | `verify.py --serve --seed-demo` + capturas en `evidencias/cu-12/` |

Comandos reales de verificación (gate de cierre):

- Backend (iteración): dentro de `backend/`, `..\.venv\Scripts\python.exe -m pytest tests/test_knowledge_service.py tests/test_knowledge_blueprint.py -q` (Linux/macOS: `../.venv/bin/python -m pytest ... -q`).
- Backend (gate): `..\.venv\Scripts\python.exe -m pytest -q` y `.\.venv\Scripts\python.exe -m ruff check backend` + `ruff format --check backend` desde la raíz.
- Frontend: dentro de `frontend/`, `cmd /c npm run build` y `cmd /c npm run lint:format`.
- Smoke: `.\.venv\Scripts\python.exe scripts\verify.py --cu cu12`.
- Re-regresión CU-11: re-ejecutar el smoke del chat (`--cu cu11`) para confirmar que el reemplazo de la tool no rompió el contrato HTTP.

## Threat Matrix

`N/A — no routing, shell commands, subprocesses, VCS/PR automation, executable-file classification, or process-integration boundary.` El cambio introduce subida de archivos de solo texto (`.md`/`.txt`) interpretados únicamente como contenido a trocear y vectorizar; no se ejecutan, no se interpretan como código, no hay paths del sistema del lado del usuario (el nombre en disco lo genera el backend con `uuid4`) y no se exponen al modelo como instrucciones ejecutables. El boundary de "documentación-like paths" aplica a clasificar ejecutables del repo, no a uploads de contenido; aun así, la validación de extensión por allowlist y el nombre aleatorio en disco son la respuesta de diseño.

## Migration / Rollout

- **Migración**: `0009_add_knowledge_source`, incremental y no invasiva (solo crea una tabla). `flask db upgrade` desde `backend/` (Windows: `..\.venv\Scripts\python.exe -m flask --app app db upgrade`); `scripts/seed_admin.py`, `seed_demo.py` y `verify.py` ya aplican migraciones pendientes.
- **Dependencias**: `chromadb` y `langchain-chroma` fijadas en `requirements.txt`; verificar instalación en Python 3.14.6 en los tres SO durante apply (riesgo del proposal). Requisito operativo: `ollama pull nomic-embed-text` — documentar en README/AGENTS; la carga falla con mensaje amable si falta.
- **Rollout**: sin feature flags; la funcionalidad queda inerte hasta que el Administrador carga la primera fuente. El chat mantiene su comportamiento funcional sin fuentes (sin embargo se re-verifica el smoke de CU-11).
- **Rollback**: `flask db downgrade` (solo dropea la tabla nueva); quitar el registro del blueprint y la tool de `build_tools` restaura el chat de CU-11; retirar las dependencias de `requirements.txt` no afecta a otros CUs; borrar `CHROMA_PERSIST_DIR` y `KNOWLEDGE_UPLOAD_DIR` no toca datos funcionales.

## Open Questions

- Ninguno bloqueante. Riesgo residual a verificar en apply (no en diseño): compatibilidad de `chromadb` con Python 3.14.6 en Windows; si la instalación falla, se replantea el almacén vectorial manteniendo el resto del diseño (el servicio encapsula Chroma tras `_get_collection`/`_get_embeddings`, lo que aísla el reemplazo).
