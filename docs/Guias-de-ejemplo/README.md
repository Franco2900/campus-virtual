# Guías de ejemplo para el chatbot

Esta carpeta contiene tres archivos de texto con formato **pregunta-respuesta** sobre el uso del
Campus Virtual, uno por rol:

| Archivo | Rol destinatario | Preguntas |
|---|---|---|
| `guia_administrador_campus_virtual.txt` | Administrador | 68 |
| `guia_profesor_campus_virtual.txt` | Profesor | 101 |
| `guia_estudiante_campus_virtual.txt` | Estudiante | 120 |

No son datos de la aplicación: no crean usuarios, cursos ni tareas. Son **material de prueba** para
cargarlos como *fuentes de conocimiento* del chatbot (CU-12) y comprobar que el asistente responde
con información del campus en lugar de improvisar, y que respeta el alcance de cada rol.

## Requisitos

Antes de cargarlas necesitás:

1. Backend y frontend corriendo (ver el `README.md` de la raíz).
2. Ollama activo **con el modelo de embeddings** descargado:

   ```bash
   ollama pull nomic-embed-text
   ollama pull qwen3:4b        # modelo que responde en el chat
   ```

   Sin `nomic-embed-text` la carga falla con un error 400 y la fuente queda en estado `error`.
3. Una sesión con rol **Administrador** (la pantalla de fuentes es exclusiva de ese rol).

## Cómo cargarlas

1. Iniciá sesión como Administrador y entrá en **Fuentes** (`/knowledge`).
2. Presioná **Cargar fuente**.
3. Completá el formulario:

   | Campo | Valor sugerido |
   |---|---|
   | Nombre | `Guía del Administrador`, `Guía del Profesor`, `Guía del Estudiante` |
   | Propósito | `Procedimientos de la interfaz para el rol <rol>` |
   | Tipo | **Respuesta aprobada** |
   | Roles destino | Solo el rol que corresponde al archivo |
   | Archivo | el `.txt` de esta carpeta |

4. Presioná **Cargar fuente**. La indexación es síncrona: cuando termina, la fila aparece con estado
   **Activa**.

Repetí el procedimiento para los tres archivos. Un archivo por carga.

### Por qué «Respuesta aprobada» y no «Documento»

El tipo cambia cómo se parte el archivo antes de indexarlo:

- **Respuesta aprobada** corta por **bloques separados por una línea en blanco**. Estas guías tienen un
  bloque por pregunta, así que cada `Pregunta:` + `Respuesta:` se indexa como un fragmento
  autocontenido (~68, ~101 y ~120 fragmentos). El recuperador devuelve fragmentos completos y las
  respuestas aprobadas se priorizan sobre el resto del material.
- **Documento** corta por tamaño (bloques de 500 caracteres con solapamiento de 50), así que puede
  partir una respuesta al medio y devolver contexto incompleto.

### Por qué limitar los roles destino

El chatbot solo recupera fragmentos autorizados para el rol de la sesión. Si cargás cada guía con su
rol, podés verificar ese filtro: un Estudiante no debe recibir contenido de la guía del Administrador.
Si dejás todos los roles sin marcar, la fuente aplica a los tres y esa verificación se pierde.

## Cómo comprobarlo

Con las tres fuentes activas, entrá en **Asistente** (`/chat`) y probá:

1. **Contenido**: como Estudiante, preguntá *«¿Cómo entrego una tarea?»*. La respuesta debe seguir los
   pasos de la guía (pantalla `/submissions`, contenido y/o enlaces, y que el asistente solo explica,
   no ejecuta la entrega).
2. **Alcance por rol**: seguí como Estudiante y preguntá *«¿Cómo creo un curso?»*. No debe obtener el
   procedimiento de la guía del Administrador; como mucho, una orientación general a que esa función
   corresponde a otro rol.
3. **Límite**: preguntá algo ajeno a la plataforma. Debe redirigir la consulta al propósito del
   asistente en lugar de inventar.

Podés repetir la prueba con una cuenta de Profesor y una de Administrador. Para tener datos con los que
navegar, usá los scripts de siembra del proyecto (`scripts/seed_admin.py` y `scripts/seed_demo.py`).

## Problemas comunes

| Síntoma | Causa probable | Solución |
|---|---|---|
| Al cargar aparece `No se pudo procesar la fuente. Verificá que el servicio de Ollama esté disponible...` y la fuente queda en `error` | Ollama no está corriendo o falta `nomic-embed-text` | `ollama serve` y `ollama pull nomic-embed-text`, y volver a cargar |
| El chat responde que no se pudo completar la consulta (502) | Falta el modelo `qwen3:4b` | `ollama pull qwen3:4b` |
| La carga responde que el formato no está admitido o supera el tamaño | Solo se aceptan `.md` y `.txt` de hasta 1 MB | convertir el archivo o dividirlo |
| El asistente no menciona la guía | Fuente en `error` o `processing`, rol destino que no coincide, o pregunta con términos muy distintos a los de la guía | revisar estado y roles en `/knowledge`; reformular la pregunta con las palabras de la guía |

La recuperación trae hasta 4 fragmentos por turno, por eso conviene que cada bloque sea una pregunta
concreta y autocontenida, como en estos archivos.

## Dónde queda guardado

- Copia del archivo: `backend/instance/knowledge/` (nombre aleatorio; el original se conserva en la
  columna de nombre del archivo).
- Índice vectorial: `backend/instance/chroma/`.
- Registro de la fuente: tabla `knowledge_source` de la base SQLite.

Todo eso está dentro de `instance/`, que no se versiona. Al eliminar una fuente desde `/knowledge` se
borra el índice, después el archivo y por último la fila.

Para empezar de cero: eliminá las fuentes desde la pantalla o, con el backend detenido, borrá la
carpeta `backend/instance/` y volvé a aplicar las migraciones y la siembra.

## Si querés reemplazar o ampliar las guías

Mantené el mismo formato: un bloque por pregunta, con `Pregunta:` y `Respuesta:` y una línea en blanco
entre bloques. El contenido debe describir la interfaz tal como está en el código; si cambia una
pantalla o una regla de negocio, actualizá la guía antes de volver a cargarla. Cada carga crea una
fuente nueva, así que eliminá la anterior para no duplicar contenido en el índice.
