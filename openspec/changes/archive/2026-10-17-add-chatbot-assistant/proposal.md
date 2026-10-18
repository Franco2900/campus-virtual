# Proposal

## Why

CU-11 «Utilizar chatbot de asistencia» (`casos_de_uso.md`) es el último ítem pendiente del roadmap: la consigna del TP exige un chatbot LangChain + Ollama integrado en la app y el sistema todavía no ofrece ninguna forma interactiva de ayuda. Los usuarios autenticados (Estudiante, Profesor, Administrador) deben poder consultar cómo funciona la plataforma y obtener información real del sistema (cursos, inscripciones, tareas, entregas, calificaciones) respetando los permisos de su rol, sin tener que leer la documentación a mano ni esperar a un humano. D-039 ya cerró las decisiones de producto (página `/chat` en `src/features/chatbot/`, modelo `qwen3:4b` vía Ollama local con el nombre como única variable de configuración); este cambio las implementa siguiendo el alcance funcional del CU-11 (flujo principal, alternativos A1–A8, postcondiciones y sus 16 reglas).

## What Changes

Alcance aprobado (decisiones ya tomadas, no se re-litigan):

- **Nuevo blueprint `chat` + `chat_service`:** backend en las capas `routes → services → models` (`backend/blueprints/chat.py`, `backend/services/chat_service.py`). El endpoint de conversación recibe el mensaje del usuario autenticado (sesión; sin sesión → A1) y devuelve la respuesta del chatbot; la identidad y el rol se toman **siempre** de la sesión, nunca de parámetros del modelo (regla 16).
- **Agente LangChain sobre Ollama local:** `langchain-ollama` con modelo `qwen3:4b` (D-039), nombre del modelo y URL de Ollama como variables de configuración para poder escalar sin tocar código. Todo corre localmente, sin servicios en la nube (regla 2). El chatbot responde en español, con tono claro y amable y extensión adaptada a la consulta (regla 11).
- **Herramientas de solo lectura con alcance por rol:** el agente expone tools que reutilizan los `services/` existentes (cursos, inscripciones, tareas/entregas, calificaciones) para consultar datos reales del sistema (paso 7 del flujo). El filtrado por permisos del rol se resuelve en el backend dentro de cada tool (reglas 3, 4, 5, 16): un Estudiante jamás recibe datos de otros usuarios ni de cursos ajenos, un Profesor solo ve sus cursos, etc. El chatbot **no** puede crear, modificar ni eliminar datos (regla 7, A4) ni corregir/calificar entregas (regla 8, A5).
- **Contexto desde la documentación del proyecto:** las consultas de «cómo funciona la plataforma» se responden con las fuentes del repo (`AGENTS.md`, `README.md`, `casos_de_uso.md`); los conocimientos generales del modelo son solo complemento y no pueden inventar funcionalidades ni reglas de la app (regla 6).
- **Historial de conversaciones en SQLite:** tablas nuevas (conversación/mensajes asociadas al `user_id`) creadas por migración incremental con Flask-Migrate/Alembic (D-023, patrón de `backend/migrations/`, después de `0007`). El historial es por usuario, se usa como contexto en conversaciones futivas (paso 8, A8, reglas 12–14) priorizando siempre los datos actuales verificados del sistema (regla 14), y **no** es accesible por otros usuarios.
- **Frontend `/chat`:** feature nueva `frontend/src/features/chatbot/` con página dedicada `/chat` enlazada desde el sidebar para los tres roles (D-039), construida sobre el design system (`src/ui/` + tokens, sin colores hardcodeados; D-019), con estados de carga y error (A7: informa que no pudo completar la consulta y sugiere reintentar).
- **Dependencias:** `langchain` y `langchain-ollama` (versiones fijadas) en `backend/requirements.txt`; el README documenta el requisito `ollama pull qwen3:4b`.

Alcance aprobado vs. detalles a fijar en diseño: las decisiones de producto de arriba están cerradas. La forma exacta de los endpoints (p. ej. `POST/GET /api/chat/messages`), los nombres de tablas/columnas, el tamaño de la ventana de historial que se inyecta como contexto y la estrategia de prompts son detalles de implementación que se fijan en `design.md`, no decisiones nuevas de producto.

## Capabilities

### New Capabilities

- `chatbot-assistant`: chatbot de asistencia para los tres roles autenticados, basado en LangChain + Ollama local (`qwen3:4b`, configurable), con respuestas en español ancladas en la documentación del proyecto y en datos reales del sistema obtenidos mediante herramientas de solo lectura con alcance por rol; historial de conversaciones persistido por usuario en SQLite y reutilizado como contexto; rechazo explícito de mutaciones, calificaciones y consultas fuera de alcance; validaciones de identidad y permisos siempre en el backend.

### Modified Capabilities

<!-- Ninguna capacidad existente cambia a nivel de spec: los endpoints y reglas de `user-auth`, `course-management`, `enrollment-management`, `task-management`, `submission-management`, `grading-management` y `grade-consultation-management` siguen intactos — el chatbot los consume en modo lectura vía los services/ existentes, sin alterar contratos. El link en el sidebar es parte de `chatbot-assistant`, no un requisito nuevo de `frontend-design-system`. Se deja vacío a propósito. -->

## Impact

- **Backend:** blueprint nuevo `backend/blueprints/chat.py` (registrado en `app.py`), servicio nuevo `backend/services/chat_service.py` (orquestación del agente, tools de solo lectura que delegan en los services existentes — sin SQL crudo, sin lógica de negocio duplicada), modelos nuevos de historial en `backend/models/` y migración incremental en `backend/migrations/` (skill `create-migration`). No cambian modelos ni endpoints existentes.
- **Tests backend:** archivo dedicado (p. ej. `backend/tests/test_chat.py`): autorización (401/403), happy path con Ollama mockeado (la suite no depende de un Ollama vivo), garantía de solo lectura, aislamiento del historial entre usuarios y traducción de errores del servicio a una respuesta amable (A7). Smoke `scripts/smoke_cu11.py` (patrón `smoke_cu10.py`) conectado a `scripts/verify.py`.
- **Frontend:** feature nueva `frontend/src/features/chatbot/` (página `/chat`, cliente de API) sobre `src/ui/`/tokens, link en `frontend/src/app/Sidebar` y ruta en el router; `frontend/package.json` sin dependencias nuevas (el chat habla con el backend por `src/api/client.js`).
- **Configuración:** variables de entorno para modelo y URL de Ollama (con defaults de desarrollo); `backend/requirements.txt` incorpora `langchain` y `langchain-ollama` fijados.
- **Documentación:** tabla de API en `AGENTS.md` (endpoints nuevos), README (requisito Ollama + `ollama pull qwen3:4b`), `progreso.md` (CU-11 Completo), `decisiones.md` (entrada propia del cambio además de D-039), evidencia en `evidencias/cu-11/` y revisión en `reviews/cu-11.md`.
- **Fuera de alcance:** crear/modificar/eliminar datos vía chatbot (A4) y corrección/calificación de tareas por chatbot (A5) — la UI y las tools son inherentemente de solo lectura; servicios LLM en la nube o externos (regla 2: solo Ollama local); subida de archivos o adjuntos en el chat; notificaciones (el TP no envía correos); streaming de respuestas (respuesta completa en el request); conversaciones compartidas entre usuarios; fine-tuning o entrenamiento del modelo; chat flotante global o panel lateral (D-039 eligió página `/chat`); paginación/exportación del historial.

## Risks

| Riesgo | Likelihood | Mitigación |
|------|------------|------------|
| Ollama no está corriendo o el modelo `qwen3:4b` no está bajado | Med | Detección del error en `chat_service` y respuesta A7 amable en español («no pudo completarse, intente más tarde»); README documenta `ollama serve` / `ollama pull`; smoke y tests mockean el LLM para no depender de Ollama en CI |
| Latencia de inferencia local (qwen3:4b en hardware justo) | Med | Indicador de «pensando…» en la UI, timeout configurado y mensaje A7; el nombre del modelo es una sola variable de configuración para escalar a un modelo mayor sin tocar código (D-039) |
| Alucinación del modelo presentando datos inventados como confirmados (regla 5) | Med | Los datos concretos salen **solo** de las tools que consultan los services reales; el prompt del sistema exige reconocer limitaciones y remitir a profesor/administrador (A2); sin dato verificable, el chatbot declara no saber |
| Intentos de extracción de datos ajenos vía prompting (regla 16) | Med | Los checks de identidad/permisos viven en el backend dentro de cada tool (rol tomado de la sesión, no del modelo): aunque el modelo «obedezca» al usuario, la tool no devuelve datos fuera de rol |
| Crecimiento del historial y costo de contexto | Baja | Ventana acotada de mensajes inyectados como contexto (detalle de diseño); tablas nuevas no afectan a las existentes |
| Cambios de versiones de langchain-ollama / compatibilidad con el Python del proyecto | Baja | Versiones fijadas en `requirements.txt`; verificación con el suite completo antes de cerrar el CU |

## Rollback Plan

El cambio es aditivo y no altera el comportamiento de ningún CU existente. Para revertir: eliminar el registro del blueprint en `app.py`, borrar `backend/blueprints/chat.py`, `backend/services/chat_service.py`, los modelos de historial, la migración nueva (o revertirla con una migración down que dropee las tablas — no hay datos de otras entidades que afectar), la feature `frontend/src/features/chatbot/`, su ruta y el link del sidebar, y las entradas en `requirements.txt`. Con eso el sistema vuelve al estado pre-CU-11 exacto.

## Success Criteria

- [ ] Un usuario autenticado de cualquiera de los tres roles abre `/chat`, envía una consulta y recibe una respuesta en español (flujo principal, pasos 1–11).
- [ ] Sin sesión, `/chat` y el endpoint responden como A1 (impide el acceso y pide iniciar sesión).
- [ ] Las consultas sobre el funcionamiento de la plataforma se responden con la documentación del repo (regla 6); las que requieren datos del sistema se responden con datos reales obtenidos por tools de solo lectura (regla 5).
- [ ] Un Estudiante no puede obtener datos de otros usuarios ni de cursos ajenos vía el chatbot (A3 + reglas 3/4/16), verificado con tests de backend.
- [ ] Las solicitudes de crear/modificar/eliminar datos (A4) y de corregir/calificar (A5) se rechazan con la orientación correspondiente, y ninguna tool del agente tiene capacidad de escritura.
- [ ] El historial queda persistido por usuario en SQLite vía migración, se reutiliza como contexto (A8) y un usuario no puede leer el historial de otro.
- [ ] Los alternativos A2 (sin información suficiente), A6 (consulta ajena) y A7 (error de servicio) tienen respuesta clara en la UI.
- [ ] La verificación del proyecto pasa: suite backend completo (`pytest`), `npm run build`/lint de frontend, `scripts/verify.py --cu cu11` con smoke, evidencia `evidencias/cu-11/` en tema claro y oscuro, y revisión `reviews/cu-11.md` con veredicto.
- [ ] La migración aplica limpiamente con `flask db upgrade` en Windows, Linux y macOS (portabilidad).
