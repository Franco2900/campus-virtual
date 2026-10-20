# Tasks: Gestión de fuentes de conocimiento del chatbot (CU-12)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~1600-2300 (Slice 1 ~750-1000, Slice 2 ~250-400, Slice 3 ~600-900) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (backend de gestión) → PR 2 (integración RAG en el chat) → PR 3 (frontend + docs + evidencia) |
| Delivery strategy | chained-pr |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

> El forecast del proposal (~1600-2300 líneas) supera ampliamente el presupuesto de 400 líneas por PR con un PR único. Se recomienda encadenar 3 slices autónomos mergeables en orden a `main`; cada slice tiene alcance, verificación y rollback propios y no rompe CU-01..CU-11. Con `delivery_strategy: ask-on-risk`, el orquestador debe confirmar la estrategia de encadenado (stacked-to-main o feature-branch-chain) antes de `sdd-apply`.

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Backend de gestión de fuentes (modelo, migración `0009`, servicio, blueprint admin, config, requirements) | PR 1 | `..\.venv\Scripts\python.exe -m pytest tests/test_knowledge_service.py tests/test_knowledge_blueprint.py -q` (desde `backend/`) | `.\.venv\Scripts\python.exe scripts\verify.py --cu cu12` (requiere el smoke del Slice 3; hasta entonces, ciclo manual de alta/listado/borrado con la base temporal) | Revertir el PR: `flask db downgrade` dropea `knowledge_source`; quitar el registro de `knowledge_bp` y del modelo en `app.py` deja CU-01..CU-11 intactos |
| 2 | Integración RAG en el chat (tool `search_knowledge_sources`, reemplazo de `search_platform_docs`, system prompt) | PR 2 | `..\.venv\Scripts\python.exe -m pytest tests/test_chat.py tests/test_knowledge_service.py -q` (desde `backend/`) | Re-ejecutar smoke de regresión CU-11 (`.\.venv\Scripts\python.exe scripts\verify.py --cu cu11`) para confirmar contrato HTTP del chat | Revertir el PR: restaurar `build_tools`/system prompt de CU-11 devuelve el comportamiento previo del chat; el backend de gestión del Slice 1 queda inerte |
| 3 | Frontend admin + smoke HTTP + docs + evidencia UI | PR 3 | `cmd /c npm run build` y `cmd /c npm run lint:format` (desde `frontend/`) + `.\.venv\Scripts\python.exe scripts\verify.py --cu cu12` | `.\.venv\Scripts\python.exe scripts\verify.py --serve --seed-demo` + capturas Playwright claro/oscuro en `evidencias/cu-12/` | Revertir el PR: quitar la ruta `/knowledge`, el item del sidebar y `src/features/knowledge/`; el backend y el RAG siguen funcionando sin pantalla |

## Phase 1: Slice 1 — Backend de gestión de fuentes (PR 1)

### 1.1 Modelo `KnowledgeSource`

- [x] 1.1 Crear `backend/models/knowledge_source.py` con los enums `KnowledgeSourceType` (`document`, `approved_answer`) y `KnowledgeSourceStatus` (`processing`, `active`, `error`) y la clase `KnowledgeSource` (`__tablename__ = "knowledge_source"`) con las columnas del diseño: `id`, `name` (String(200)), `description` (Text, default `""`), `source_type`/`status` (`db.Enum(..., values_callable=...)`, default `PROCESSING`), `target_roles` (`db.JSON`, default `list`), `original_filename`, `stored_filename`, `file_size_bytes`, `chunk_count`, `error_message` (nullable), `created_at`/`updated_at` (DateTime timezone-aware con `datetime.now(UTC)`), siguiendo el patrón de `backend/models/conversation.py` y `backend/models/submission.py`. Registrar el modelo en el import de `models` de `backend/app.py:42-51`. Verificar: `backend/` `..\.venv\Scripts\python.exe -c "from app import create_app; from models.knowledge_source import KnowledgeSource"`.

### 1.2 Migración `0009`

- [x] 1.2 Crear `backend/migrations/versions/0009_add_knowledge_source.py` (`revision = "0009_add_knowledge_source"`, `down_revision = "0008_add_chat_history"`) con `upgrade` = `op.create_table("knowledge_source", ...)` (`sa.Enum(..., name="knowledgesourcetype")`/`knowledgesourcestatus`, `sa.JSON()`, `server_default=sa.text("CURRENT_TIMESTAMP")` en los timestamps, sin índices extra) y `downgrade` = `op.drop_table("knowledge_source")`, siguiendo el patrón de `backend/migrations/versions/0008_add_chat_history.py`. Verificar: desde `backend/`, `..\.venv\Scripts\python.exe -m flask --app app db upgrade` y luego `..\.venv\Scripts\python.exe -m flask --app app db downgrade` sin error; `..\.venv\Scripts\python.exe -m pytest tests/test_migrations.py -q`.

### 1.3 Config por entorno

- [x] 1.3 Agregar a `backend/config/config.py` las variables con defaults del diseño: `OLLAMA_EMBED_MODEL` (`nomic-embed-text`), `CHROMA_PERSIST_DIR` (`instance/chroma`), `CHROMA_COLLECTION` (`campus_knowledge`), `KNOWLEDGE_MAX_FILE_BYTES` (`1048576`), `KNOWLEDGE_UPLOAD_DIR` (`instance/knowledge`), reutilizando `OLLAMA_BASE_URL`/`OLLAMA_TIMEOUT` y con helper de resolución de rutas relativas contra `BACKEND_DIR` análogo a `_database_uri()`. Verificar: `backend/` `..\.venv\Scripts\python.exe -c "from config.config import Config; print(Config.CHROMA_PERSIST_DIR, Config.KNOWLEDGE_MAX_FILE_BYTES)"`.

### 1.4 Dependencias

- [x] 1.4 Agregar `chromadb` y `langchain-chroma` con versiones fijadas a `backend/requirements.txt`; instalar en el venv y confirmar compatibilidad con Python 3.14.6 (riesgo residual del diseño). Verificar: `.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt` sin errores y `backend/` `..\.venv\Scripts\python.exe -c "import chromadb, langchain_chroma"`.

### 1.5 `knowledge_service` — validación y ALTA

- [x] 1.5 Crear `backend/services/knowledge_service.py` con `ValidationError` y la validación de la carga (`KNOWLEDGE_ALLOWED_EXTENSIONS = {".md", ".txt"}`, tamaño ≤ `KNOWLEDGE_MAX_FILE_BYTES`, `name` no vacío ≤ 200, `source_type` válido, `target_roles` ⊆ `{student, teacher, admin}`), los seams `_get_embeddings()`/`_get_collection()` (lazy, con lock), el pipeline de ingesta síncrono del diseño (persistir fila `processing` + archivo uuid en `KNOWLEDGE_UPLOAD_DIR` → leer texto UTF-8 `errors="replace"` → chunking → embeddings + `collection.add` con metadata `source_id`/`source_type`/`role_student`/`role_teacher`/`role_admin` → `status=active`, `chunk_count`), el chunking de `document` (`RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50, separators=["\n## ","\n### ","\n",". "," "])`) y de `approved_answer` (1 fragmento por bloque no vacío), y la compensación de A5 (fallo → `collection.delete(where={"source_id": id})` best-effort, fila `error` con `error_message`, HTTP 400 con mensaje amable). Verificar: `backend/` `..\.venv\Scripts\python.exe -m pytest tests/test_knowledge_service.py -q`.

### 1.6 `knowledge_service` — listado, obtención y borrado

- [x] 1.6 En `backend/services/knowledge_service.py`, implementar `list_sources()` (orden `id` descendente), `get_source(id)` (`NotFoundError` → 404) y `delete_source(id)` con el orden del diseño: (1) fila o `NotFoundError`, (2) `collection.delete(where={"source_id": id})` idempotente (fallo → `KnowledgeServiceError` y fila intacta), (3) `Path.unlink()` best-effort tolerante a `OSError` (log), (4) `db.session.delete(row)` + commit, más la serialización por fuente con los campos del contrato (`target_roles: []` = todos). Verificar: `backend/` `..\.venv\Scripts\python.exe -m pytest tests/test_knowledge_service.py -q`.

### 1.7 Blueprint admin

- [x] 1.7 Crear `backend/blueprints/knowledge.py` (`url_prefix="/api/knowledge"`) con `GET /sources`, `POST /sources` (multipart: `file`, `name`, `description`, `source_type`, `target_roles` repetido), `DELETE /sources/<int:source_id>`, todos con `@login_required` + `@require_roles(UserRole.ADMIN)` de `backend/blueprints/guards.py` (401 sin sesión / 403 no-admin) y delegando la lógica en `knowledge_service` (patrón de `backend/blueprints/users.py`); registrar `knowledge_bp` en `create_app` (`backend/app.py:53-61`). Verificar: `backend/` `..\.venv\Scripts\python.exe -m pytest tests/test_knowledge_blueprint.py -q`.

### 1.8 Tests del Slice 1

- [x] 1.8 Crear `backend/tests/test_knowledge_service.py`: validación (extensión inválida A4, tamaño excedido A4, campos faltantes/roles inválidos → `ValidationError` sin fila), transición de estados (éxito → `active` con `chunk_count`; fake de embeddings que falla → fila `error` con `error_message` y `delete` registrado en el índice A5), chunking (`document` con splitter; `approved_answer` = 1 fragmento por bloque con `source_type=approved_answer`), borrado (orden de llamadas, idempotencia del paso índice, 404, `Path.unlink` tolerante a `OSError` vía monkeypatch), retrieval (sin activas → `[]`; rol student no recupera fuente solo-teacher — regla 7; `approved_answer` primero — regla 8; solo `active_ids` en el `where` — reglas 5/13); y `backend/tests/test_knowledge_blueprint.py`: 401 sin sesión, 403 no-admin (A3), 201 alta, 400 extensión/tamaño (A4), 200 listado con metadata, 200/404 delete, 500 con `KnowledgeServiceError` simulado. Los tests no llaman a Ollama/Chroma (monkeypatch de `_get_embeddings`/`_get_collection`). Verificar: `backend/` `..\.venv\Scripts\python.exe -m pytest tests/test_knowledge_service.py tests/test_knowledge_blueprint.py -q`.

### 1.9 Verificación de cierre del Slice 1

- [x] 1.9 Ejecutar la verificación de cierre del Slice 1: `backend/` `..\.venv\Scripts\python.exe -m pytest -q` (suite completo, garantiza no romper CU-01..CU-11) y, desde la raíz, `.\.venv\Scripts\python.exe -m ruff check backend` + `.\.venv\Scripts\python.exe -m ruff format --check backend`. Verificar: ambos en verde, sin regresiones en los tests existentes.

## Phase 2: Slice 2 — Integración RAG en el chat (PR 2)

### 2.1 Tool de recuperación scopeada por rol

- [x] 2.1 En `backend/services/chat_service.py`, agregar `knowledge_service.retrieve_for_user(query, user_role, k=4)` (según el diseño: `active_ids` desde SQLite, embedding de la query, `similarity_search` con `filter={"$and": [{"source_id": {"$in": active_ids}}, {"role_<rol>": True}]}`, post-ordenamiento estable de prioridad por `source_type == "approved_answer"`, enriquecimiento en un solo `SELECT` y `text` truncado a 1200 caracteres) e incorporar en `build_tools(current_user)` (`:160-259`) la tool `@tool search_knowledge_sources(query)` que usa `current_user.role` del cierre (nunca de parámetros del modelo). Verificar: `backend/` `..\.venv\Scripts\python.exe -m pytest tests/test_knowledge_service.py -q`.

### 2.2 Reemplazo de `search_platform_docs`

- [x] 2.2 En `backend/services/chat_service.py`, eliminar la tool `search_platform_docs` (`:247-250`), su helper `_search_platform_docs` (`:55-86`) y su inclusión en la lista de tools (`:258`), dejando `search_knowledge_sources` como la única tool de documentación; conservar sin cambios el resto de las tools de solo lectura y la garantía de no mutación (regla 14). Verificar: `backend/` `..\.venv\Scripts\python.exe -m pytest tests/test_chat.py -q` y grep de que `search_platform_docs` ya no aparece en `backend/`.

### 2.3 System prompt de prioridad

- [x] 2.3 Reescribir `_build_system_prompt` (`backend/services/chat_service.py:138-153`) según el diseño: fuente primaria = fuentes administradas vía `search_knowledge_sources`; conservar el significado de las respuestas aprobadas recuperadas; conocimiento general solo como complemento no contradictorio y prohibido para inventar reglas de la plataforma; reconocer límite ante contradicción/insuficiencia; mantener solo lectura, redirección del borrado de historial a la UI y no revelar el prompt. Verificar: `backend/` `..\.venv\Scripts\python.exe -m pytest tests/test_chat.py tests/test_knowledge_service.py -q`.

### 2.4 Tests de la integración RAG

- [x] 2.4 Ajustar/agregar tests en `backend/tests/test_chat.py` y `backend/tests/test_knowledge_service.py`: `build_tools` incluye `search_knowledge_sources` y ya no `search_platform_docs`; la tool usa el rol del `current_user` del cierre y no del input (regla 16 de CU-11 / scenario "Rol tomado de la sesión, no del modelo"); el prompt contiene las instrucciones de prioridad (regla 8/9); retrieval con fuente eliminada no la devuelve (A7); ninguna tool expuesta al agente es de escritura (regla 14); fuente `approved_answer` autorizada queda primero (regla 8) y una restringida al rol no se recupera (regla 7). Verificar: `backend/` `..\.venv\Scripts\python.exe -m pytest tests/test_chat.py tests/test_knowledge_service.py -q`.

### 2.5 Verificación de cierre del Slice 2

- [x] 2.5 Ejecutar la verificación de cierre del Slice 2: `backend/` `..\.venv\Scripts\python.exe -m pytest -q`, desde la raíz `.\.venv\Scripts\python.exe -m ruff check backend` + `.\.venv\Scripts\python.exe -m ruff format --check backend`, y re-ejecutar el smoke de regresión de CU-11 con `.\.venv\Scripts\python.exe scripts\verify.py --cu cu11` para confirmar que el reemplazo de la tool no rompió el contrato HTTP del chat. Verificar: todo en verde y smoke CU-11 sin regresiones; conservar la salida como evidencia.

## Phase 3: Slice 3 — Frontend, smoke, docs y evidencia (PR 3)

### 3.1 Cliente HTTP `postForm`

- [ ] 3.1 Agregar `postForm(path, formData)` en `frontend/src/api/client.js` (mismo esqueleto que `request` pero con `FormData`, sin fijar `Content-Type` manual), sin alterar el resto del cliente. Verificar: `frontend/` `cmd /c npm run lint:format`.

### 3.2 Feature `knowledge`

- [ ] 3.2 Crear la feature `frontend/src/features/knowledge/` con `api.js` (`getSources()`, `createSource(formData)` vía `postForm`, `deleteSource(id)`), `KnowledgePage.jsx` (listado con Nombre, Propósito, Tipo/Badge, Roles con "Todos" si vacío, `StatusBadge` con `active`/`processing`/`error` y `error_message` en secundario; `PageHeader` + botón "Cargar fuente"; `Spinner`/`EmptyState`/`Toast`; `data-testid` `knowledge-page`/`knowledge-source-row`), `KnowledgeUploadForm.jsx` (dentro de `Modal`, `FormField` con nombre/descripción/tipo, checkboxes de los tres roles tildados por defecto, input `file` `accept=".md,.txt"`, envío `FormData`, muestra el `error` del backend en 400, `data-testid` `knowledge-upload-form`) y la confirmación de borrado con `ConfirmDialog` danger (aviso de que dejará de estar disponible para el chatbot, cancelación sin efectos A6, `data-testid` `knowledge-delete-confirm`), reutilizando `src/ui/` y tokens sin colores hardcodeados. Verificar: `frontend/` `cmd /c npm run lint:format`.

### 3.3 Rutas y sidebar

- [ ] 3.3 Agregar el item `{ to: "/knowledge", label: "Fuentes", icon: "bi-bookmark-data-fill", roles: ["admin"] }` en `NAV_ITEMS` de `frontend/src/app/Sidebar.jsx:3-28` y la ruta `/knowledge` bajo `ProtectedRoute role="admin"` en `frontend/src/App.jsx` (patrón de `/users`, líneas 54-61, visible solo para Administrador). Verificar: `frontend/` `cmd /c npm run build` y `cmd /c npm run lint:format`.

### 3.4 Smoke HTTP CU-12

- [ ] 3.4 Crear `scripts/smoke_cu12.py` (patrón `scripts/smoke_cu02.py`, flag `--base`) que: login admin → `POST /api/knowledge/sources` con un `.md` de prueba → poll de `GET /api/knowledge/sources` hasta `active` → consulta al chat que usa la fuente → `DELETE` de la fuente → `GET` de la fuente eliminada devuelve ausencia (A7); y caso no-admin → 403 en los endpoints de gestión (A3). Verificar: `.\.venv\Scripts\python.exe scripts\verify.py --cu cu12` (base temporal aislada; `verify.py` resuelve `smoke_cu12.py` por nombre, no requiere edición adicional) con salida en verde.

### 3.5 Evidencia UI Playwright

- [ ] 3.5 Levantar servicios desligados con `.\.venv\Scripts\python.exe scripts\verify.py --serve --seed-demo` y capturar en `evidencias/cu-12/` (nombres `NN-accion.png`): listado con estados, alta exitosa, error de validación A4, borrado con diálogo de confirmación A2/A6, y ausencia del item "Fuentes"/ruta para un usuario no-admin (A3); en tema claro y oscuro; consola sin errores inesperados. Cerrar con `.\.venv\Scripts\python.exe scripts\verify.py --cleanup`. Verificar: capturas presentes y legibles, estado esperado confirmado.

### 3.6 Documentación de cierre

- [ ] 3.6 Actualizar `AGENTS.md` (endpoints `GET/POST/DELETE /api/knowledge/sources` en la tabla API, estructura de `models/`/`services/`/`blueprints/`, variables de entorno nuevas, requisito operativo `ollama pull nomic-embed-text`), `decisiones.md` (nuevas decisiones: límite 1 MB, fuente sin roles = todos, fila `error`, orden de borrado no atómico, reemplazo de `search_platform_docs`), `progreso.md` (estado de CU-12 por slice), `README.md` (requisitos de entorno) y `openspec/specs/chatbot-assistant/spec.md` (merge del delta al archivar). Verificar: revisión manual de que la tabla de API y las env coinciden con el código.

### 3.7 Verificación de cierre del Slice 3 y del CU

- [ ] 3.7 Ejecutar el gate de cierre del CU: `backend/` `..\.venv\Scripts\python.exe -m pytest -q`, raíz `.\.venv\Scripts\python.exe -m ruff check backend` + `.\.venv\Scripts\python.exe -m ruff format --check backend`, `frontend/` `cmd /c npm run build` + `cmd /c npm run lint:format`, y `.\.venv\Scripts\python.exe scripts\verify.py --cu cu12`. Luego ejecutar la revisión obligatoria del CU con la skill `review-use-case` (subagente `reviewer` o inline) y persistir `reviews/cu-12.md` (hallazgos con `archivo:línea`, severidad, veredicto, mapa de evidencia). Verificar: todo en verde, revisión APROBADA.
- [ ] 3.8 Archivar el cambio: sincronizar el delta de `chatbot-assistant` a `openspec/specs/` y mover `openspec/changes/add-chatbot-knowledge-sources/` a `openspec/changes/archive/YYYY-MM-DD-add-chatbot-knowledge-sources/` (fase `sdd-archive`), con `cmd /c openspec validate add-chatbot-knowledge-sources --strict` y `cmd /c openspec status --change add-chatbot-knowledge-sources` en 4/4. Verificar: cambio archivado y estado completo.

## Implementation Order

Slice 1 (backend de gestión) → Slice 2 (integración RAG) → Slice 3 (frontend + smoke + docs + evidencia). Slice 2 depende de que `knowledge_service.retrieve_for_user` exista (Slice 1) y Slice 3 depende del contrato HTTP del backend (Slices 1-2). Cada slice es mergeable a `main` en orden sin romper CU-01..CU-11 y tiene su propio rollback.
