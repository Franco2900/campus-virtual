# Proposal: Gestión de fuentes de conocimiento del chatbot (CU-12)

## Intent

El chatbot del Campus Virtual (CU-11) responde hoy con conocimiento general del modelo y una búsqueda substring sobre `AGENTS.md`/`README.md`/`casos_de_uso.md` (`search_platform_docs`). Ese mecanismo no permite al Administrador cargar guías, FAQs ni respuestas aprobadas, ni priorizar información autorizada por rol. CU-12 cierra esa brecha: el Administrador gestiona fuentes de conocimiento autorizadas (carga y eliminación) y el chatbot las utiliza como referencia principal mediante recuperación RAG, priorizando respuestas aprobadas y respetando el alcance por rol (reglas 3, 7 y 8 de CU-12). Es el último CU pendiente del alcance original de la consigna.

Vinculación: `casos_de_uso.md` sección **CU-12 — Gestionar fuentes de conocimiento del chatbot** (flujo principal + A1..A7 + 15 reglas) y reglas de negocio de `AGENTS.md` (roles excluyentes, validación en backend, portabilidad).

## Scope

### In Scope

Alcance aprobado por el CU y por las decisiones del usuario (input firme, no re-litigables):

- Modelo `KnowledgeSource` + migración Alembic `0009` (esquema de fuentes de conocimiento).
- `backend/services/knowledge_service.py`: alta, listado, obtención y baja de fuentes; validación de formato/tamaño; chunking e indexado sincrónicos; borrado del índice vectorial, el archivo y la fila en una transacción (reglas 4, 5, 11, 13, 15).
- Blueprint admin `backend/blueprints/knowledge.py` (endpoints `GET/POST/DELETE` bajo `/api/knowledge/sources`, solo Administrador; permisos en backend, reglas 1 y 2).
- Integración RAG en el chat: tool de recuperación en `build_tools(current_user)` de `chat_service.py`, con ChromaDB + embeddings locales Ollama `nomic-embed-text`, filtrado por rol del usuario en la recuperación (reglas 7 y 8).
- Respuestas aprobadas modeladas como `source_type='approved_answer'` dentro de la misma entidad fuente, parseadas a fragmentos con prioridad alta en la recuperación (regla 8).
- Formatos admitidos por defecto: `.md` y `.txt`; estados `processing` / `active` / `error` con procesamiento síncrono al cargar (reglas 4, 5, 13).
- Frontend admin en `frontend/src/features/knowledge/`: pantalla de gestión (listar, cargar con metadatos y roles destino, eliminar con confirmación, A1/A2/A6), sobre el design system existente.
- Eliminación sin afectar el historial de conversaciones (regla 12).
- Tests backend (patrón de CUs previos), smoke HTTP y evidencia UI Playwright.

### Out of Scope

- No se usa sentence-transformers / PyTorch; embeddings solo vía Ollama.
- No se introduce un supervisor multi-agente (LangGraph); se conserva `create_agent` (CU-11) + una tool RAG.
- No se crea una entidad separada para respuestas aprobadas.
- No se implementa procesamiento asíncrono ni cola de trabajos (el corpus chico lo justifica; se revisará solo si crece).
- No se modifican contratos de CU-01..CU-11 (los endpoints y pantallas existentes se conservan; `search_platform_docs` puede quedar complementada o reemplazada por la tool RAG, sin cambiar el contrato del chat).
- No se cargan ni procesan archivos de la carpeta desechable `rag-chat/` (solo se reutilizan patrones de código).
- No se permite al chatbot mutar datos funcionales (regla 14; se conserva la garantía de solo lectura del agente).
- No se habilita edición de fuentes existentes (solo carga y eliminación, según el CU).

## Capabilities

> Contrato con la fase de specs: `sdd-spec` debe crear un spec completo para la capacidad nueva y un delta para la modificada.

### New Capabilities

- `chatbot-knowledge-sources`: gestión administrativa de fuentes de conocimiento (carga, validación, procesamiento/indexado, listado, eliminación) y recuperación RAG scopeada por rol para el chatbot, incluyendo respuestas aprobadas con prioridad.

### Modified Capabilities

- `chatbot-assistant`: el requisito "Respuesta anclada a la documentación de la plataforma" cambia a nivel de spec — la referencia principal pasan a ser las fuentes administradas por el Administrador (regla 6 de CU-12) en lugar de la documentación del repositorio; se añade la priorización de respuestas aprobadas (regla 8 de CU-12) y el filtrado por rol en la recuperación (regla 7 de CU-12). El requisito de arquitectura del chatbot se extiende con la nueva tool y el servicio RAG, sin alterar la garantía de solo lectura.

## Approach

Enfoque técnico de alto nivel (detalle en la fase de diseño):

1. **Modelo y migración**: entidad `KnowledgeSource` (nombre, descripción/purpose, roles destino, `source_type` `document` | `approved_answer`, `status` `processing` | `active` | `error`, ruta/nombre del archivo original, metadatos de procesamiento) persistida en SQLite; migración incremental `0009` con Flask-Migrate/Alembic, posterior a `0008`, sin alterar entidades existentes.
2. **knowledge_service**: en `services/` (regla de dependencias `routes → services → models`). Validación de extensión/tamaño (`.md`/`.txt`), almacenamiento del archivo original, chunking con `RecursiveCharacterTextSplitter` (`chunk_size=500`, `chunk_overlap=50`, separadores de headers Markdown — patrón aprobado del ejemplo `rag-chat/`), embeddings con `OllamaEmbeddings` (`nomic-embed-text`) e indexado en ChromaDB vía `langchain-chroma` (retriever `k=4`). Para `approved_answer`, el contenido se parsea a fragmentos individuales marcados con prioridad alta. Todo síncrono dentro del request, con la fila en `processing` y transición a `active` o `error`.
3. **Blueprint admin**: `backend/blueprints/knowledge.py`, registrado en `app.py`, con los endpoints de gestión solo para Administrador; validaciones y lógica delegadas en el servicio (patrón de blueprints existentes).
4. **Integración RAG en el chat**: en `chat_service.py`, `build_tools(current_user)` incorpora una tool de búsqueda en las fuentes de conocimiento que recupera fragmentos relevantes filtrando por el rol del usuario (identidad y rol SIEMPRE desde la sesión Flask, nunca del modelo — regla 16 y práctica de CU-11). Las respuestas aprobadas recuperadas se presentan con prioridad; el system prompt se ajusta para que las fuentes autorizadas prevalezcan sobre el conocimiento general (reglas 8 y 9 de CU-12). La colección ChromaDB se inicializa/apunta con configuración por env (patrón `OLLAMA_*` existente).
5. **Frontend admin**: feature `frontend/src/features/knowledge/` con página de gestión (listado con estado y roles, formulario de carga con roles destino, eliminación con `ConfirmDialog`), consumiendo el backend vía `src/api/client.js`, sobre `src/ui/` y tokens (design system).
6. **Verificación**: tests backend por servicio/blueprint (patrón de `backend/tests/`), smoke HTTP con `scripts/verify.py`, evidencia UI Playwright claro/oscuro.

## Affected Areas

| Área | Impacto | Descripción |
|------|---------|-------------|
| `backend/models/knowledge_source.py` | Nuevo | Modelo `KnowledgeSource` |
| `backend/migrations/versions/0009_*` | Nuevo | Migración incremental del esquema de fuentes |
| `backend/services/knowledge_service.py` | Nuevo | Validación, chunking, indexado, borrado transaccional |
| `backend/blueprints/knowledge.py` | Nuevo | Endpoints admin de gestión de fuentes |
| `backend/app.py` | Modificado | Registro del nuevo blueprint |
| `backend/services/chat_service.py` | Modificado | Tool RAG en `build_tools`, ajuste del system prompt |
| `backend/config/` | Modificado | Config por env de ChromaDB/embeddings (con defaults) |
| `backend/requirements.txt` | Modificado | `chromadb`, `langchain-chroma` (versiones fijadas) |
| `backend/tests/` | Nuevo/Modificado | Tests de knowledge_service, blueprint y tool RAG |
| `frontend/src/features/knowledge/` | Nuevo | Pantalla de gestión admin |
| `frontend/src/app/` (sidebar/rutas) | Modificado | Acceso a la pantalla para Administrador |
| `AGENTS.md`, `decisiones.md`, `progreso.md`, `scripts/verify.py`/`smoke_cu12.py` | Modificado/Nuevo | Documentación y verificación |
| `openspec/specs/chatbot-assistant/spec.md` | Modificado (al archivar) | Delta de la capacidad modificada |

## Risks

| Riesgo | Probabilidad | Mitigación |
|--------|--------------|------------|
| Dependencias nuevas `chromadb` y `langchain-chroma` (peso, compatibilidad con Python 3.14, instalación en Windows/Linux/macOS) | Media | Fijar versiones en `requirements.txt`; verificar instalación y suite completo en el gate de cierre; fallback: si chromadb no es viable en el entorno, replantear en diseño (no se relitiga aquí la elección) |
| Requisito operativo: `ollama pull nomic-embed-text` además de `qwen3:4b` | Alta (fácil de olvidar) | Documentar en README/AGENTS y en el error amable si el modelo de embeddings no está disponible; la carga de fuentes debe fallar con mensaje claro (A5) |
| Procesamiento síncrono dentro del request de carga: latencia percebida o timeout con archivos grandes | Media | Limitar tamaño máximo del archivo (a definir en diseño, regla 15); corpus chico del TP lo justifica; estados `processing`/`error` evitan presentar fuentes incompletas (reglas 5 y 13) |
| Borrado de la colección vectorial no transaccional con SQLite: inconsistencia índice ↔ fila ↔ archivo | Media | Orden de operaciones y compensación definidos en diseño; el índice vectorial es derivado y reconstruible; los 3 artefactos (índice, archivo, fila) se borran en la operación de baja (regla 11) |
| Latencia de embeddings por consulta en el chat (llamada a Ollama por turno de recuperación) | Media | Retrieval acotado (`k=4`); aceptable en entorno local; medir en smoke |
| Cambio de comportamiento del chatbot puede afectar percepción del CU-11 ya aprobado | Baja | El delta de `chatbot-assistant` es deliberado y acotado; los endpoints y la garantía de solo lectura no cambian; se re-verifica el smoke de CU-11 |
| El corpus de fuentes es contenido del Administrador, no del repo: `scripts/verify.py` debe aislar la base de datos de prueba | Baja | Patrón existente de bases temporales sembradas del verify |

## Rollback Plan

- Revertir el commit(s) del cambio: la migración `0009` es incremental y no altera entidades previas; revertirla con `flask db downgrade` (o recrear la base) restaura el esquema anterior.
- Quitar el registro del blueprint en `app.py` y la tool RAG de `build_tools` restaura el comportamiento del chat de CU-11.
- `chromadb`/`langchain-chroma` solo se usan en el flujo de conocimiento; retirarlas de `requirements.txt` no afecta a otros CUs.
- La colección vectorial local puede eliminarse por completo sin impacto en datos funcionales (cursos, usuarios, tareas, historial).

## Dependencies

- Ollama local ejecutándose con `qwen3:4b` (ya requerido por CU-11) y `nomic-embed-text` descargado (`ollama pull nomic-embed-text`).
- Paquetes nuevos en `backend/requirements.txt`: `chromadb`, `langchain-chroma` (versiones fijadas; compatibilidad con Python 3.14.6 a verificar en apply).
- Ejemplo descartable `rag-chat/` como referencia de patrones (no es parte del sistema; no se versiona su contenido).
- Flask-Migrate/Alembic (ya en el proyecto) para la migración `0009`.

## Success Criteria

- [ ] Un Administrador puede cargar un `.md`/`.txt`, con roles destino, y la fuente queda `active` y recuperable por el chatbot para los roles autorizados (A1, reglas 1-7).
- [ ] Una consulta que coincide con una respuesta aprobada produce una respuesta del chatbot que prioriza y conserva el sentido de esa respuesta (regla 8).
- [ ] La recuperación filtra por rol: un Estudiante no recupera fragmentos de una fuente dirigida solo a Profesores/Administradores (regla 7).
- [ ] Un no-Administrador recibe 403/401 en los endpoints de gestión y no ve la pantalla (A3, reglas 1 y 2).
- [ ] Archivo inválido o fallo de procesamiento queda `error` o se rechaza con el motivo, y la fuente no se usa por el chatbot (A4, A5, reglas 4, 5, 13).
- [ ] Eliminar una fuente la retira del índice vectorial, del almacenamiento y de la base; consultas futuras ya no la utilizan; el historial de conversaciones no se ve afectado (A2, A6, A7, reglas 11 y 12).
- [ ] Tests backend en verde, smoke HTTP del CU en verde, build/lint frontend OK, evidencia UI Playwright capturada (gate de cierre del proyecto).

## Review Workload Forecast

Estimación preliminar de líneas cambiadas (autenticado como texto escrito, sin contar goldens generados):

| Bloque | Estimación |
|--------|------------|
| Modelo + migración `0009` | ~120-180 |
| `knowledge_service` + config | ~350-450 |
| Blueprint admin + registro en `app.py` | ~120-180 |
| Integración RAG en `chat_service` + requirements | ~120-180 |
| Tests backend | ~400-600 |
| Frontend (feature + rutas/sidebar) | ~350-500 |
| Docs (`AGENTS.md`, `decisiones.md`, `progreso.md`, smoke) | ~150-250 |
| **Total estimado** | **~1600-2300** |

Decision needed before apply: No
Chained PRs recommended: No
400-line budget risk: High

El presupuesto de revisión de 400 líneas por PR se supera ampliamente con un PR único. Sin embargo, la estrategia de delivery confirmada por el orquestador es `single-pr`. La recomendación técnica es encadenar 2-3 PRs con unidades autónomas (p. ej. PR #1: backend (modelo, migración, servicio, blueprint, tests); PR #2: integración RAG en el chat + tests; PR #3: frontend + docs + evidencia), cada uno con verificación y rollback propio. La decisión final de slicing corresponde a `sdd-tasks`/al orquestador alineándose con `delivery_strategy`.
