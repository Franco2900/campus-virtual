# Design

## Context

Ver `proposal.md - Why` y `specs/chatbot-assistant/spec.md` (12 requisitos). Estado actual relevante, verificado leyendo el código:

- Arquitectura de capas `routes → services → models` con un blueprint por dominio registrado en `backend/app.py:33-57` y `backend/blueprints/guards.py` (`login_required` → 401, `require_roles` → 403). Los blueprints leen el body con `request.get_json(silent=True)`, delegan en `services/` y traducen excepciones a JSON (`ValidationError`→400, `ConflictError`→409, `NotFoundError`→404, `ForbiddenError`→403). Patrón exacto en `backend/blueprints/submissions.py:23-38` y `backend/blueprints/users.py:29-41`.
- `backend/blueprints/guards.py:8-16`: `login_required` inyecta `current_user` obtenido de la sesión (`services/auth_service.py::get_current_user` lee `session["user_id"]`). La identidad/rol **siempre** proviene de la sesión, nunca del body.
- Servicios de solo lectura reutilizables por las tools: `course_service.list_courses_for_user`/`get_course_or_404`/`get_manageable_course` (`backend/services/course_service.py:15-74`), `enrollment_service.list_students` (`:10-21`), `task_service.list_tasks` (`:91-116`), `grade_service.get_course_grades` (`backend/services/grade_service.py:191-196`), `grading_service.list_submissions_for_task` (`backend/services/grading_service.py:80-90`). El alcance por rol ya vive dentro de estos servicios (`get_manageable_course` para Profesor, `_require_active_enrollment` para Estudiante).
- Modelos: `backend/models/*.py` con `db.Model`, `__tablename__` en singular, FKs planas `db.ForeignKey("user.id")`, sin `relationship()` ni `ondelete` (los servicios hacen los joins explícitos), timestamps `db.DateTime(timezone=True)` con `default=lambda: datetime.now(UTC)`. Ejemplos: `enrollment.py`, `task.py`, `course_teacher.py`.
- Migraciones Alembic incrementales en `backend/migrations/versions/` (`0001`…`0007`). El head actual es `0007_add_grading` (`revision = '0007_add_grading'`, `down_revision = '0006'`).
- `backend/tests/test_migrations.py:8-15` importa explícitamente cada módulo de modelo y luego `assert compare_metadata(...) == []`. **Cualquier modelo nuevo debe importarse ahí** o el test de paridad modelo↔esquema falla.
- `backend/tests/conftest.py`: fixture `app` con `TESTING=True` (usa `db.create_all()`, ver `backend/app.py:59-61`) sobre SQLite temporal, y fixture `client`. Los tests siembran con helpers (patrón `backend/tests/test_grades.py:39-80`).
- `backend/config/config.py`: `Config` lee variables de entorno (`SECRET_KEY`, `CAMPUS_DB_PATH`); no hay hoy config del LLM.
- Frontend: router en `frontend/src/App.jsx` (`ProtectedRoute` anidado en `AppLayout`), sidebar en `frontend/src/app/Sidebar.jsx` (array `NAV_ITEMS` con `roles` opcional → visible para todos si se omite), cliente HTTP en `frontend/src/api/client.js` (`get`/`post`/`put`/`patch`/`del`, arroja `Error` con `data.error`). Página patrón: `frontend/src/features/grades/GradesPage.jsx` (usa `PageHeader`, `Card`, `Spinner`, `EmptyState`, `FormField`) + `api.js` del mismo feature.
- Design system (`frontend/src/ui/index.js`): `Button`, `Card`, `Badge`, `RoleBadge`, `StatusBadge`, `PageHeader`, `Spinner`, `EmptyState`, `DataTable`, `StatCard`, `FormField`, `Modal`, `ConfirmDialog`, `ToastProvider`/`useToast`.
- Dependencias instalables verdaderas (verificado con `pip index versions` + `pip install --dry-run` en el `.venv` del proyecto, Python **3.14.6**): `langchain-ollama` va por **1.1.0** (major 1.x) y `langchain` por **1.4.6**; `langchain==1.4.6` + `langchain-ollama==1.1.0` resuelven limpio y arrastran `langchain-core 1.6.12`, `langgraph`, `langsmith`, `ollama`, `pydantic 2.x`.

## Objectives / Non-Objectives

**Objectives**
- Backend aditivo: blueprint `chat`, servicio `chat_service`, modelos `Conversation`/`Message` + migración `0008`, sin tocar contratos de CU-01..CU-10.
- Agente LangChain local (`langchain-ollama` + `qwen3:4b`) con herramientas de **solo lectura** cuyo alcance por rol se resuelve reutilizando los `services/` existentes y la identidad de la sesión (regla 16).
- Historial por usuario en SQLite, aislado e inyectado como contexto acotado (A8).
- Página `/chat` sobre el design system, con estados de carga y error (A7).

**Non-Objectives (fuera de alcance, ya fijado en `proposal.md`)**
- Escritura vía chatbot (A4), corrección/calificación (A5), servicios LLM en la nube, adjuntos, notificaciones, **streaming** (respuesta completa por request), conversaciones compartidas, fine-tuning, chat flotante, paginación/exportación del historial.
- No se cambian modelos ni endpoints de CU-01..CU-10.

## Technical Approach

`POST /api/chat/messages` recibe el texto del usuario (sesión obligatoria), el servicio obtiene/crea el hilo del usuario, carga una **ventana acotada** del historial, construye el agente con un system prompt en español + las tools de solo lectura **scopeadas por la sesión**, ejecuta el agente y persiste el par (mensaje de usuario + respuesta) en una sola transacción. `GET /api/chat/messages` devuelve el historial del propio usuario. El alcance por rol no depende del modelo: cada tool reutiliza los servicios que ya aplican `get_manageable_course`/enrollment, pasándoles el `current_user` de la sesión.

## Decisions

### D-A: Cambio aditivo, un hilo por usuario (get-or-create)
`Conversation`/`Message` son tablas nuevas; no se altera ninguna entidad existente. El servicio mantiene **una conversación activa por usuario** (`_get_or_create_conversation`) y appendea todos los mensajes ahí.
**Alternativas consideradas**: (1) varias conversaciones con selector en la UI — fuera de alcance (`proposal.md` excluye paginación/exportación, y no se pide lista de hilos); (2) no persistir conversación y guardar solo mensajes con `user_id` — se descarta porque el enunciado/spec hablan explícitamente de «conversación/mensajes» y una tabla `conversation` deja la puerta abierta a múltiples hilos sin migración futura.
**Consecuencias**: contexto trivial de cargar (un solo `conversation_id`), aislamiento por `user_id`, y el modelo de datos soporta multi-hilo sin cambios de esquema.

### D-B: Esquema `Conversation`/`Message` y migración `0008` (patrón de los modelos existentes)
Nuevos módulos siguiendo las convenciones vigentes (FK plana, sin `relationship()`, sin `ondelete`, timestamps UTC):

`backend/models/conversation.py`
```python
class Conversation(db.Model):
    __tablename__ = "conversation"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
```

`backend/models/message.py`
```python
MESSAGE_ROLES = ("user", "assistant")

class Message(db.Model):
    __tablename__ = "message"
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversation.id"), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)   # "user" | "assistant"
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
```
Migración nueva `backend/migrations/versions/0008_add_chat_history.py` con `revision = '0008_add_chat_history'`, `down_revision = '0007_add_grading'`; `upgrade()` crea `conversation` y `message` (+ índices `ix_conversation_user_id`, `ix_message_conversation_id`), `downgrade()` dropea `message` y luego `conversation` (orden inverso por la FK).
**Alternativas consideradas**: (1) `db.relationship()` + `cascade` — se descarta para no divergir del estilo del repo (ningún modelo usa relationships; los servicios hacen joins explícitos); (2) `role` como `db.Enum` — se descarta: son dos valores internos controlados por el servicio (no input de usuario), un `String(20)` + validación en el servicio es suficiente y evita el ruido del enum en SQLite; (3) `ondelete="CASCADE"` en `message.conversation_id` — se descarta porque **no hay ningún flujo de borrado** de conversaciones ni de usuarios en alcance: no habría nada que cascadee. Si en el futuro se agrega «borrar conversación», se añade una migración con CASCADE (SQLite además requiere `PRAGMA foreign_keys=ON`).
**Consecuencias**: los índices en las FK sostienen las consultas de historial; `backend/tests/test_migrations.py` **debe** importar `conversation` y `message` para que `compare_metadata(...) == []` siga pasando.

### D-C: Contrato de endpoints (`blueprints/chat.py`)
Blueprint `chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")`, registrado en `backend/app.py`. Guards `@login_required` (401) + `@require_roles(UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN)`.

`POST /api/chat/messages`
- Request: `{"content": "<texto>"}`.
- 201:
```json
{
  "conversation_id": 3,
  "user_message":      {"id": 41, "role": "user",      "content": "...", "created_at": "2026-10-17T10:00:00+00:00"},
  "assistant_message": {"id": 42, "role": "assistant", "content": "...", "created_at": "2026-10-17T10:00:05+00:00"}
}
```
- 400 `{"error": "La consulta no puede estar vacía"}` (o > `CHAT_MESSAGE_MAX_LENGTH`).
- 502 `{"error": "No se pudo completar la consulta. Intentá nuevamente en unos minutos."}` (A7).
- 401 sin sesión (guard).

`GET /api/chat/messages`
- 200 `{"conversation_id": 3, "messages": [{"id","role","content","created_at"}]}` ordenado por `id` asc; si el usuario aún no tiene hilo: `{"conversation_id": null, "messages": []}`.
- 401 sin sesión (guard).

La serialización vive en el blueprint (`_serialize_message`), como en `submissions.py`/`users.py`; el servicio devuelve modelos. Los errores del dominio se traducen en el blueprint (`ValidationError`→400) y el error del LLM se encapsula en el servicio y se mapea a 502.
**Alternativas consideradas**: (1) `GET /api/chat/conversations/<id>/messages` — se descarta: sin multi-hilo en alcance (D-A), un recurso «messages» del propio usuario es más simple y expresa el aislamiento por sesión; (2) devolver 200 con el shape de `assistant_message` aunque falle — rechazado por D-D.

### D-D: A7 como error de servicio (HTTP 502) y **sin persistir** el turno fallido
Ante fallo del LLM/Ollama (no disponible, modelo ausente, timeout), el servicio no guarda el par de mensajes y el blueprint responde 502 con el texto amable de A7; la UI lo renderiza como burbuja de error con «Reintentar».
**Alternativas consideradas**: (1) responder 200 con un `assistant_message` que diga que falló y **persistirlo** — rechazado: ensucia el historial con respuestas que no son del asistente y complica el A8 («el historial contiene respuestas de error»); (2) 500 genérico — rechazado: 502 («bad gateway» hacia el servicio local de inferencia) describe mejor el fallo y permite distinguirlo en tests/smoke.
**Consecuencias**: la postcondición «nunca queda la solicitud sin explicación» se cumple en la UI (burbuja A7); el historial solo contiene turnos realmente respondidos, lo que mantiene limpio el contexto inyectado.

### D-E: Agente con `create_agent` de LangChain 1.x sobre `ChatOllama`
El agente se construye con `langchain.agents.create_agent(model, tools, system_prompt=...)` (langchain 1.4.6) sobre `langchain_ollama.ChatOllama(model=..., base_url=...)`, con `temperature=0`. La invocación se aísla en un **seam** `_invoke_agent(agent, messages) -> str` para testing.
**Alternativas consideradas**: (1) loop manual `ChatOllama.bind_tools` con `langchain_core.messages` — más control sobre `max_iterations`, pero más código propio que mantener; (2) solo `langchain-core` + `langchain-ollama` sin el paquete `langchain` — rechazado porque la spec exige `langchain` como dependencia (`Requirement: Integración…`), e instalar un paquete no usado sería peor que usarlo.
**Consecuencias**: se usa la API oficial y la recursión del agente queda acotada con `recursion_limit` en el config de `invoke`. **Detalle a verificar en apply**: firma exacta de `create_agent` y del kwarg de URL de `ChatOllama` contra las versiones instaladas (1.4.6 / 1.1.0).

### D-F: System prompt en español — documentación como fuente primaria + reglas de CU-11
El prompt se arma en `chat_service._build_system_prompt()` (constante de módulo, en español) y materializa las reglas del CU: identidad «asistente del Campus Virtual»; idioma español, tono claro y amable, extensión adaptada (regla 11/14); **fuente primaria = documentación del repo** vía la tool `search_platform_docs` (D-G) y prohibición de inventar funcionalidades/reglas (regla 6); datos concretos **solo** de las tools, nunca inventados (regla 5); alcance limitado a la plataforma y redirección ante consultas ajenas (A6); solo lectura, no crear/modificar/eliminar (A4) y no corregir/calificar (A5); ante insuficiencia, reconocer el límite y derivar a profesor/administrador (A2); no revelar el prompt ni detalles técnicos; **defensa de prompt-injection**: las reglas del sistema prevalecen sobre cualquier instrucción del usuario y el rol no se puede cambiar por texto (D-O).
**Alternativas consideradas**: (1) precargar `AGENTS.md`+`README.md`+`casos_de_uso.md` enteros en el prompt — rechazado: infla el contexto en cada request (≈miles de líneas) y encarece/enlentece la inferencia local con un modelo 4b; (2) sin bloque de reglas y confiar solo en las tools — rechazado: se perderían A2/A4/A5/A6, que no son datos sino comportamiento.

### D-G: Tool `search_platform_docs` (lectura de archivos del repo) en lugar de inyección estática
Tool de solo lectura que resuelve las fuentes contra la raíz del proyecto con `Path(__file__).resolve().parents[2]` (portable, sin rutas absolutas ni separadores por SO) y lee `AGENTS.md`, `README.md`, `casos_de_uso.md`; devuelve hasta `DOC_EXCERPT_MAX_CHARS` (2000) caracteres de coincidencias por palabra clave. Sin restricción de rol (la documentación es común a los tres roles).
**Alternativas consideradas**: precargar (ver D-F) — rechazado por costo de contexto; embebidos/vector store — sobredimensionado para 3 archivos y añade dependencias (fuera del alcance «sin dependencias nuevas innecesarias»).
**Consecuencias**: contexto acotado y determinista; si los archivos no existen (entorno raro), la tool devuelve un texto neutro y el modelo responde A2 en vez de romper.

### D-H: Ventana de historial = últimos 10 mensajes
`CHAT_HISTORY_WINDOW = 10` (hasta 5 intercambios) se traduce a `HumanMessage`/`AIMessage` y se antepone al mensaje nuevo.
**Justificación**: suficiente para resolver anáforas/continuidad (A8, «¿y esa tarea cuándo vence?»), mantiene el prompt pequeño (bajo costo/latencia y menos degradación en un modelo 4b), y evita arrastrar contexto viejo que la spec dice no tratar como definitivo (regla 14). Es configurable por `CHAT_HISTORY_WINDOW` para escalar a un modelo mayor sin tocar código.
**Alternativas consideradas**: ventana fija por tokens — innecesaria para el TP; historial completo — riesgo de latencia y de que el modelo priorice datos viejos por sobre las tools.

### D-I: Tools de solo lectura con alcance por sesión (enumeradas)
Factory `build_tools(current_user)` que devuelve tools `@tool` (de `langchain_core.tools`) cerrando sobre `current_user` (identidad de sesión, jamás parámetro del modelo — regla 16). Ninguna llama a una función mutadora:

| Tool | Devuelve | Delegación (servicio existente) | Alcance |
|------|----------|---------------------------------|---------|
| `list_my_courses()` | Cursos del usuario (`id`, `name`, `code`, `active`) | `course_service.list_courses_for_user(current_user)` | Pro: asignados; Est: inscritos activos; Admin: todos |
| `list_course_students(course_id)` | Estudiantes del curso + estado de inscripción | `enrollment_service.list_students(course_id, current_user)` | Admin/Profesor (Est → `ForbiddenError` → texto de permiso) |
| `list_course_tasks(course_id)` | Tareas del curso (Est: disponibles + su entrega; Pro: todas) | `task_service.list_tasks(course_id, current_user)` | Según rol |
| `get_course_grades(course_id)` | Notas/promedio (Est: propias; Pro: matriz del curso) | `grade_service.get_course_grades(course_id, current_user)` | Según rol (aplica enrollment/`get_manageable_course`) |
| `list_task_submissions(course_id, task_id)` | Entregas de la tarea con estudiante y corrección | `grading_service.list_submissions_for_task(course_id, task_id, current_user)` | Profesor (Admin vía `get_manageable_course`) |
| `search_platform_docs(query)` | Extractos de la documentación del repo | lectura directa de `AGENTS.md`/`README.md`/`casos_de_uso.md` | Todos los roles |

Cada tool **captura** `ForbiddenError`/`NotFoundError`/`ValidationError` y devuelve un texto en español (p. ej. «No tenés permisos para ver esa información»), de modo que A3/A2 produzcan una respuesta que el modelo pueda relatar sin exponer detalles técnicos. Las tools devuelven texto JSON compacto (`json.dumps(..., ensure_ascii=False)`).
**Justificación**: el filtrado por permisos ya está implementado y probado en los `services/`; el chatbot **no** reimplementa autorización, solo le pasa la sesión. Esto satisface `Requirement: Datos reales… con alcance por rol y validación en backend` y `Requirement: Rechazo de mutaciones…` (garantía de solo lectura por construcción: el módulo no importa ninguna función de escritura).
**Alternativas consideradas**: (1) pasar el `user_id`/rol como argumento de la tool — rechazado (viola regla 16: permitiría al modelo elegir identidad); (2) exponer un único «query SQL» — rechazado (SQL crudo fuera de la arquitectura y sin control de permisos).

### D-J: Configuración por entorno con defaults de desarrollo
Se agregan a `backend/config/config.py::Config` (mismo patrón `os.environ.get` ya usado):
```python
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:4b")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "120"))   # segundos (helper _int_env)
CHAT_HISTORY_WINDOW = int(os.environ.get("CHAT_HISTORY_WINDOW", "10"))
CHAT_MESSAGE_MAX_LENGTH = int(os.environ.get("CHAT_MESSAGE_MAX_LENGTH", "4000"))
```
`chat_service` los lee de `current_app.config`. La URL/modelo son datos, no secretos (Ollama es local, sin API keys).
**Alternativas consideradas**: constantes en el servicio — rechazado: D-039 exige que cambiar de modelo sea una sola variable de configuración.

### D-K: Dependencias fijadas (verificadas en Python 3.14.6)
`backend/requirements.txt` suma:
```
langchain==1.4.6
langchain-core==1.6.12
langchain-ollama==1.1.0
```
`langchain-ollama` va por su **major 1.x** (la serie actual compatible con `langchain-core` 1.x); se fija explícitamente `langchain-core` porque `chat_service` importa de él directamente (`langchain_core.messages`, `langchain_core.tools`). **Evidencia**: `pip index versions` mostró `langchain-ollama 1.1.0` / `langchain 1.4.6` / `langchain-core 1.6.12` como últimas, y un `pip install --dry-run "langchain==1.4.6" "langchain-ollama==1.1.0"` resolvió sin conflictos sobre el `.venv` (CPython 3.14), arrastrando `langgraph`, `langsmith`, `ollama`, `pydantic 2.14`.
**Riesgo**: `langchain` meta arrastra `langgraph` (footprint mayor al mínimo). **Alternativa considerada**: usar solo `langchain-core`+`langchain-ollama` — rechazado porque la spec exige `langchain`.
**Consecuencias**: `pip install -r backend/requirements.txt` es reproducible; `README.md` documenta `ollama serve` + `ollama pull qwen3:4b`.

### D-L: Frontend — feature `chatbot` sobre el design system
Estructura:
```
frontend/src/features/chatbot/
├── api.js               # getHistory(), sendMessage(content)
├── ChatPage.jsx         # página /chat (orquesta estados)
├── MessageList.jsx      # lista con auto-scroll + burbuja "pensando…"
├── MessageBubble.jsx    # mensaje (alineación por rol vía tokens)
└── ChatComposer.jsx     # FormField textarea + Button enviar
```
Archivos a tocar: `frontend/src/App.jsx` (ruta `/chat` con `<ProtectedRoute roles={["student","teacher","admin"]}>`) y `frontend/src/app/Sidebar.jsx` (ítem `{ to: "/chat", label: "Asistente", icon: "bi-chat-dots-fill" }`, sin `roles` → visible a los tres). Todo por `src/api/client.js` (`get`/`post`), sin dependencias nuevas en `package.json`.
Componentes del design system: `PageHeader`, `Card`, `Button`, `FormField`, `Spinner`, `EmptyState`, `useToast` (ToastProvider ya montado en `App.jsx`). Sin colores hardcodeados: superficies/alíneación con tokens/utilitarias existentes (`bg-brand-soft`, `text-brand`), nunca hex.
UX/states: carga inicial con `Spinner`; `EmptyState` sin mensajes; al enviar, `composer` deshabilitado + burbuja «pensando…» (A7/loading); éxito → burbuja del asistente; error → alerta `role="alert"` (A7) con `Button` «Reintentar» que reenvía el último texto. **Sin streaming** (respuesta completa por request, según `proposal.md`).
`data-testid` estables para la evidencia: `chat-page`, `chat-empty`, `chat-message-list`, `chat-message-user`, `chat-message-assistant`, `chat-input`, `chat-send`, `chat-thinking`, `chat-error`.
**Alternativas consideradas**: widget flotante / panel lateral — ya descartados por D-039 (página dedicada).

### D-M: Estrategia de tests (mocking del LLM por seam)
`backend/tests/test_chat.py` no depende de un Ollama vivo: se parchea el seam `chat_service._invoke_agent` (y/o `_build_agent`) con `monkeypatch`/`unittest.mock.patch`, devolviendo texto fijo o lanzando excepción. Las tools se prueban **directamente** (`build_tools(current_user)` + `tool.invoke({...})` dentro de `app.app_context()` con datos sembrados), sin agente. Cobertura por requisito de spec:
- 401 sin sesión en `POST` y `GET`.
- Happy path: 201 + shapes + persistencia; `GET` devuelve ambos mensajes ordenados.
- Validación: body no-objeto / sin `content` / vacío / no-string / excede longitud → 400.
- Contexto (A8): una segunda consulta recibe el historial previo (fake que captura `messages`).
- Aislamiento: el usuario B no ve mensajes de A (ni en `GET` ni en el contexto inyectado).
- A7: fake que lanza → 502 + texto amable + **nada persistido**.
- Solo lectura: conteo de filas de `course`/`task`/`submission`/`user` sin cambios tras una consulta; aserción de que `build_tools` no expone nombres de funciones mutadoras.
- Alcance por rol de cada tool (Estudiante vs Profesor vs Admin; Estudiante sobre curso ajeno → texto de permiso).
- `search_platform_docs` devuelve texto no vacío para una consulta conocida.
Además, `backend/tests/test_migrations.py` se actualiza para importar `conversation` y `message`.

### D-N: Smoke `scripts/smoke_cu11.py` con guardia de Ollama
Patrón `smoke_cu10.py` (urllib + cookie jar, checks PASS/FAIL, exit 0/1), conectado a `scripts/verify.py --cu cu11`. Checks deterministas: 401 anónimo (`POST`/`GET`), 400 con `content` vacío, login Estudiante, `GET` inicial vacío, `POST` → se acepta **201 (Ollama arriba)** o **502 (A7, Ollama abajo)**; si 201, se valida `assistant_message.role == "assistant"` y contenido no vacío, y luego `GET` incluye el mensaje de usuario; aislamiento con un segundo usuario. Si el backend devuelve 502, el smoke imprime `[SKIP] Ollama no disponible: se validó A7` y **mantiene el PASS** de los checks deterministas.
**Justificación**: las máquinas de CI/agente pueden no tener Ollama; el smoke debe quedar verde sin él, pero seguir ejercitando autorización/validación/aislamiento/contrato. La verificación con respuesta real se hace en el gate de evidencia (D-O).
**Alternativas consideradas**: (1) smoke con Ollama obligatorio — rechazado (frágil en CI); (2) backdoor «modelo fake» en el backend — rechazado (meter código de test en producción).

### D-O: Evidencia Playwright y seguridad/prompt-injection
Evidencia en `evidencias/cu-11/NN-accion-{light,dark}.png`, con servicios vía `scripts/verify.py --serve` y **Ollama corriendo** para la respuesta real: (01) estado vacío, (02) consulta enviada + «pensando…», (03) respuesta del asistente, (04) estado de error A7 (Ollama caído), (05) acceso sin sesión (401/redirección). Re-captura quirúrgica ante fallos (skill `design-system`/`new-use-case`).
Seguridad: sin secretos en el repo (modelo/URL/timeout por entorno, Ollama local sin claves); **prompt-injection**: la autorización se aplica en el backend dentro de cada tool (identidad/rol desde la sesión) — aunque el usuario convenza al modelo de «actuar como admin» o de «ignorar las reglas», la tool sigue devolviendo solo lo permitido por el rol real (regla 16). Las tools no tienen capacidad de escritura (D-I), por lo que una inyección no puede mutar datos ni calificar.

### D-P: Registro de decisiones y docs de cierre
Las decisiones de este diseño se registran en `decisiones.md` (numeración vigente, además de D-039), y se actualizan la tabla de API de `AGENTS.md`, `README.md` (requisito Ollama), `progreso.md` y `reviews/cu-11.md` durante el cierre del CU.

## Data Flow

```
UI /chat ──POST /api/chat/messages {content}──▶ blueprints/chat.py
   │                                              │ login_required + require_roles
   │                                              ▼
   │                                     services/chat_service.py
   │                                       _get_or_create_conversation(user)
   │                                       _load_history(conv, window=10)
   │                                       _build_system_prompt()
   │                                       build_tools(user)  ── solo lectura ──┐
   │                                       _build_agent(...) / _invoke_agent    │
   │                                              │                             │
   │                                              │  (tool calls del modelo)    │
   │                                              ▼                             ▼
   │                                     ChatOllama (Ollama local)      course/enrollment/
   │                                              │                     task/grade/grading
   │                                              │                     services (rol = sesión)
   │                                              ▼
   │                                   persistir user_message + assistant_message (commit)
   │                                              │
   ◀────────── 201 {user_message, assistant_message} ─┘
   │
   └── GET /api/chat/messages ──▶ historial del usuario (aislado)
```

## File Changes

| Archivo | Acción | Descripción |
|---------|--------|-------------|
| `backend/models/conversation.py` | Crear | Modelo `Conversation` (D-B) |
| `backend/models/message.py` | Crear | Modelo `Message` + `MESSAGE_ROLES` (D-B) |
| `backend/migrations/versions/0008_add_chat_history.py` | Crear | Migración incremental post-`0007_add_grading` (D-B) |
| `backend/services/chat_service.py` | Crear | Orquestación del agente, tools, prompts, historial (D-E..D-I) |
| `backend/blueprints/chat.py` | Crear | Endpoints `POST`/`GET /api/chat/messages` (D-C) |
| `backend/app.py` | Modificar | Importar modelos nuevos y registrar `chat_bp` |
| `backend/config/config.py` | Modificar | Config Ollama/chat por entorno (D-J) |
| `backend/requirements.txt` | Modificar | `langchain`, `langchain-core`, `langchain-ollama` fijadas (D-K) |
| `backend/tests/test_chat.py` | Crear | Tests del CU-11 con seam mockeado (D-M) |
| `backend/tests/test_migrations.py` | Modificar | Importar `conversation`, `message` (paridad modelos↔esquema) |
| `scripts/smoke_cu11.py` | Crear | Smoke HTTP con guardia de Ollama (D-N) |
| `frontend/src/features/chatbot/api.js` | Crear | `getHistory()`, `sendMessage(content)` |
| `frontend/src/features/chatbot/ChatPage.jsx` | Crear | Página `/chat` (estados) |
| `frontend/src/features/chatbot/MessageList.jsx` | Crear | Lista de mensajes + auto-scroll + «pensando…» |
| `frontend/src/features/chatbot/MessageBubble.jsx` | Crear | Burbuja por rol (tokens) |
| `frontend/src/features/chatbot/ChatComposer.jsx` | Crear | Entrada + envío |
| `frontend/src/App.jsx` | Modificar | Ruta `/chat` protegida (3 roles) |
| `frontend/src/app/Sidebar.jsx` | Modificar | Ítem «Asistente» visible a los 3 roles |
| `README.md` | Modificar | Requisito Ollama + `ollama pull qwen3:4b` |
| `AGENTS.md` | Modificar | Tabla de API (endpoints chat) + nota del chatbot |
| `docs/er-diagrama.md` | Modificar | Entidades `conversation`/`message` (si el diagrama las documenta) |
| `decisiones.md`, `progreso.md` | Modificar | Cierre del CU-11 |

## Interfaces / Contracts

Blueprint (patrón de `submissions.py`/`users.py`):
```python
# backend/blueprints/chat.py
chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")

@chat_bp.post("/messages")
@login_required
@require_roles(UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN)
def send_message_endpoint(current_user):
    data = request.get_json(silent=True)
    try:
        user_msg, assistant_msg = chat_service.respond(current_user, data)
    except ValidationError as error:
        return jsonify({"error": str(error)}), 400
    except ChatServiceError as error:      # error del LLM / A7
        return jsonify({"error": str(error)}), 502
    return jsonify(_serialize_turn(user_msg, assistant_msg)), 201

@chat_bp.get("/messages")
@login_required
@require_roles(UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN)
def list_messages_endpoint(current_user):
    conversation, messages = chat_service.get_history(current_user)
    return jsonify({...}), 200
```

Servicio (superficie pública + seams de test):
```python
# backend/services/chat_service.py
MESSAGE_MAX_LENGTH_ENV = "CHAT_MESSAGE_MAX_LENGTH"
class ChatServiceError(Exception): ...          # → 502 (A7)

def respond(current_user, data): ...            # valida, orquesta, persiste; pública
def get_history(current_user): ...              # (conversation|None, [Message, ...])

def build_tools(current_user): ...              # tools de solo lectura (D-I)
def _build_agent(tools): ...                    # create_agent(...)  [seam]
def _invoke_agent(agent, messages) -> str: ...  # [seam de mock en tests]
def _build_system_prompt() -> str: ...          # D-F
```

Tools (firma y retorno, texto JSON):
```python
def build_tools(current_user) -> list:
    @tool
    def list_my_courses() -> str: ...                     # course_service.list_courses_for_user
    @tool
    def list_course_students(course_id: int) -> str: ...  # enrollment_service.list_students
    @tool
    def list_course_tasks(course_id: int) -> str: ...     # task_service.list_tasks
    @tool
    def get_course_grades(course_id: int) -> str: ...     # grade_service.get_course_grades
    @tool
    def list_task_submissions(course_id: int, task_id: int) -> str: ...  # grading_service.list_submissions_for_task
    @tool
    def search_platform_docs(query: str) -> str: ...      # lectura de AGENTS.md/README.md/casos_de_uso.md
    return [list_my_courses, ...]
```

Migración:
```python
# backend/migrations/versions/0008_add_chat_history.py
revision = '0008_add_chat_history'
down_revision = '0007_add_grading'
def upgrade():  # create_table conversation (+ix_conversation_user_id); create_table message (+ix_message_conversation_id)
def downgrade():  # drop_table message; drop_table conversation
```

## Testing Strategy

| Capa | Qué se prueba | Cómo |
|------|---------------|------|
| Unit (tools) | Alcance por rol y solo lectura de cada tool | `build_tools(current_user)` + `tool.invoke({...})` en `app_context` con datos sembrados; asserts de contenido/permiso y de conteo de filas sin cambios |
| Unit (servicio) | Ventana de historial, armado de prompt, validación de mensaje, mapeo de error a `ChatServiceError` | Llamadas directas a `chat_service` con `_invoke_agent` parcheado (fake que captura `messages`/lanza) |
| Integration (API) | 401/400/201/502, shapes, persistencia, aislamiento, contexto A8 | `client` de `conftest.py`, sesión vía `POST /api/auth/login`, `_invoke_agent` mockeado |
| Paridad esquema | `compare_metadata(...) == []` tras `flask db upgrade` de la `0008` | `backend/tests/test_migrations.py` con los modelos nuevos importados |
| Smoke HTTP | Auth/validación/aislamiento + contrato de respuesta (200 o 502) | `scripts/smoke_cu11.py` vía `scripts/verify.py --cu cu11` |
| E2E (UI) | Estados de `/chat` (vacío, pensando, respuesta, error A7, sin sesión) | Playwright MCP, capturas claro/oscuro en `evidencias/cu-11/` |

## Threat Matrix

N/A — el cambio no altera routing, comandos de shell, subprocesos, automatización de VCS/PR, clasificación de ejecutables ni integración de procesos. (El boundary relevante es LLM/prompt-injection y lectura de archivos locales, tratado en D-O: la autorización se resuelve en las tools del backend, no en el modelo.)

## Migration / Rollout

1. **Esquema**: crear los modelos y la migración `0008_add_chat_history`; aplicar con `flask db upgrade` y verificar la paridad con `test_migrations.py`. Rollback: `downgrade` dropea `message` y `conversation` (sin datos de otras entidades).
2. **Backend**: `requirements.txt`; `config.py`; `chat_service.py` (tools + prompt + agente); `blueprints/chat.py`; registrar en `app.py`. Iterar con `pytest backend/tests/test_chat.py -q`.
3. **Tests**: `test_chat.py` + actualización de `test_migrations.py`; luego suite completa.
4. **Frontend**: feature `chatbot`, ruta y sidebar; `npm run build` + `lint:format`.
5. **Verificación**: `scripts/smoke_cu11.py` vía `scripts/verify.py --cu cu11`; evidencia Playwright (claro/oscuro) con Ollama arriba; `reviews/cu-11.md`.
6. **Cierre**: `progreso.md`, `decisiones.md`, tabla de API en `AGENTS.md`, `README.md`, archive del cambio; commits por unidad de trabajo (skill `work-unit-commits`).

## Open Questions

- [ ] **Firma exacta de librería**: `create_agent` y el kwarg de URL de `ChatOllama` (¿`base_url`?) y de timeout deben confirmarse contra `langchain 1.4.6` / `langchain-ollama 1.1.0` al aplicar; si difieren, ajustar en `chat_service` sin cambiar el contrato (deferred to tasks).
- [ ] **Persistencia del `user_message` en el turno fallido**: se asume **no persistir** el turno cuando el LLM falla (D-D). Si se prefiere conservar la pregunta del usuario para reintentos con contexto, es un ajuste de servicio sin cambio de contrato.
- [ ] **Longitud de la respuesta**: no se fija un tope de tokens de salida; si el modelo responde demasiado, evaluar `max_tokens`/`num_predict` en `ChatOllama` (deferred to tasks).

## Deferred to tasks

- Fijar naming final de la tool de documentación y su algoritmo de extractos (keyword vs. primeras N líneas) — D-G.
- Verificar/ajustar la API real de `create_agent`/`ChatOllama` (`base_url`, timeout, `recursion_limit`, `num_predict`) — Open Questions.
- Definir el texto final del system prompt (bloque de reglas A2/A4/A5/A6) y su tono — D-F.
- Actualizar `docs/er-diagrama.md` con `conversation`/`message` si el diagrama se mantiene.
- Estrategia de re-captura quirúrgica de pantallas y guion exacto de pasos Playwright — D-O.
- Comandos concretos de verificación y su registro en `errores.md` ante fallos — skill `run-verification`.
